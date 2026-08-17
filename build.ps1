[CmdletBinding()]
param(
    [string]$JoEngineRoot,
    [string]$PythonPath,
    [switch]$Clean,
    [switch]$Release,
    [switch]$VisualTest,
    [switch]$EncounterTest,
    [switch]$SkipHostTests
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (-not $JoEngineRoot) {
    $JoEngineRoot = Join-Path $projectRoot '.deps\joengine'
}
if (-not (Test-Path -LiteralPath $JoEngineRoot)) {
    throw "Jo Engine dependency is missing. Run .\setup_engine.ps1 first."
}
$resolvedEngine = (Resolve-Path -LiteralPath $JoEngineRoot).Path
$compiler = Join-Path $resolvedEngine 'Compiler\WINDOWS\bin\sh-elf-gcc.exe'
$objcopy = Join-Path $resolvedEngine 'Compiler\WINDOWS\bin\sh-elf-objcopy.exe'
$utilities = Join-Path $resolvedEngine 'Compiler\WINDOWS\Other Utilities'
$make = Join-Path $utilities 'make.exe'
$mkisofs = Join-Path $utilities 'mkisofs.exe'
$cueMaker = Join-Path $utilities 'JoEngineCueMaker.exe'

foreach ($requiredTool in @($compiler, $objcopy, $make, $mkisofs, $cueMaker)) {
    if (-not (Test-Path -LiteralPath $requiredTool)) {
        throw "Required Saturn build tool not found: $requiredTool"
    }
}

if (-not $PythonPath) {
    $pythonCommand = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $PythonPath = $pythonCommand.Source
    }
    else {
        $pythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
        if ($pythonCommand -and $pythonCommand.Source -notlike '*WindowsApps*') {
            $PythonPath = $pythonCommand.Source
        }
        else {
            $bundledPython = Join-Path $env:LOCALAPPDATA 'codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonPath = $bundledPython
            }
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 with Pillow is required. Pass its executable with -PythonPath.'
}

$projectUri = [Uri]($projectRoot.TrimEnd('\') + '\')
$engineUri = [Uri]($resolvedEngine.TrimEnd('\') + '\')
$relativeEngine = [Uri]::UnescapeDataString($projectUri.MakeRelativeUri($engineUri).ToString()).TrimEnd('/')
if ($relativeEngine -match '\s') {
    throw "The relative Jo Engine path '$relativeEngine' contains spaces, which its makefiles do not support."
}

$previousPath = $env:PATH
try {
    $env:PATH = "$utilities;$(Join-Path $resolvedEngine 'Compiler\WINDOWS\bin');$previousPath"
    Push-Location $projectRoot
    try {
        if (-not $SkipHostTests) {
            & '.\test.ps1' -PythonPath $PythonPath
            if ($LASTEXITCODE -ne 0) {
                throw "Host tests failed with exit code $LASTEXITCODE."
            }
        }

        & '.\prepare_avsp_port.ps1' -PythonPath $PythonPath
        if ($LASTEXITCODE -ne 0) {
            throw "AvP Stage 1 asset preparation failed with exit code $LASTEXITCODE."
        }

        & '.\prepare_qsound_audio.ps1' -PythonPath $PythonPath
        if ($LASTEXITCODE -ne 0) {
            throw "QSound event preparation failed with exit code $LASTEXITCODE."
        }

        $contentRoot = Join-Path $projectRoot 'build\avsp_cd'
        foreach ($metadataName in @('ABS.TXT', 'BIB.TXT', 'CPY.TXT')) {
            Copy-Item -LiteralPath (Join-Path $projectRoot "cd\$metadataName") `
                -Destination (Join-Path $contentRoot $metadataName) -Force
        }

        $buildProfile = if ($EncounterTest) { 'encounter-test' }
            elseif ($VisualTest) { 'visual-test' }
            else { 'normal-release' }
        $optimizationProfile = if ($Release) { 'release' } else { 'debug' }
        $compileProfile = "$optimizationProfile-$buildProfile"
        $profileStamp = Join-Path $projectRoot 'build\last_compile_profile.txt'
        $previousProfile = if (Test-Path -LiteralPath $profileStamp) {
            (Get-Content -LiteralPath $profileStamp -Raw).Trim()
        }
        else { '' }
        if ($previousProfile -ne $compileProfile) {
            foreach ($objectName in @('main.o', 'capability_model.o')) {
                $objectPath = Join-Path $projectRoot $objectName
                if (Test-Path -LiteralPath $objectPath) {
                    Remove-Item -LiteralPath $objectPath -Force
                }
            }
            Get-ChildItem -LiteralPath (Join-Path $resolvedEngine 'jo_engine') `
                -Filter '*.o' -File | Remove-Item -Force
        }

        if ($Clean) {
            # Jo Engine's bundled Cygwin rm.exe can fail to reserve its heap on
            # current 64-bit Windows. Remove only this project's known outputs.
            foreach ($generatedName in @(
                'main.o', 'capability_model.o', 'game.elf', 'game.raw',
                'game.iso', 'game.cue', 'game.map', 'stage1_audio.wav',
                'cd\0.bin', 'build\avsp_cd\0.bin'
            )) {
                $generatedPath = Join-Path $projectRoot $generatedName
                if (Test-Path -LiteralPath $generatedPath) {
                    Remove-Item -LiteralPath $generatedPath -Force
                }
            }
            Get-ChildItem -LiteralPath (Join-Path $resolvedEngine 'jo_engine') -Filter '*.o' -File |
                Remove-Item -Force
            }

        $makeArguments = @('-f', 'makefile', "JO_ENGINE_ROOT=$relativeEngine")
        if ($Release) {
            $makeArguments += 'JO_DEBUG=0'
        }
        if ($VisualTest) {
            $makeArguments += 'AVSP_VISUAL_TEST=1'
        }
        if ($EncounterTest) {
            $makeArguments += 'AVSP_ENCOUNTER_TEST=1'
        }
        $makeArguments += 'game.raw'
        & $make @makeArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn compilation failed with exit code $LASTEXITCODE."
        }
        [IO.File]::WriteAllText($profileStamp, $compileProfile)

        & $objcopy '-O' 'binary' 'game.elf' (Join-Path $contentRoot '0.bin')
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the Saturn boot binary (exit code $LASTEXITCODE)."
        }

        $mkisofsArguments = @(
            '-quiet',
            '-sysid', 'SEGA SATURN',
            '-volid', 'AVP_CAP_TEST',
            '-volset', 'AVP_CAP_TEST',
            '-sectype', '2352',
            '-publisher', 'PRIVATE CAPABILITY TEST',
            '-preparer', 'PRIVATE CAPABILITY TEST',
            '-appid', 'AVP_SATURN_CAPABILITY',
            '-abstract', '.\cd\ABS.TXT',
            '-copyright', '.\cd\CPY.TXT',
            '-biblio', '.\cd\BIB.TXT',
            '-generic-boot', (Join-Path $resolvedEngine 'Compiler\COMMON\IP.BIN'),
            '-full-iso9660-filenames',
            '-o', 'game.iso', $contentRoot
        )
        & $mkisofs @mkisofsArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create game.iso (exit code $LASTEXITCODE)."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/GUN.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\GUN.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn PCM ISO verification failed with exit code $LASTEXITCODE."
        }

        # Add the locally rendered QSound reference as a real Saturn CDDA track.
        # It remains an ignored private artifact and is never linked as CPS2 code.
        $audioSource = Join-Path $projectRoot '.deps\mame\captures\stage1_route_reference.wav'
        $audioTrack = Join-Path $projectRoot 'stage1_audio.wav'
        Copy-Item -LiteralPath $audioSource -Destination $audioTrack -Force
        & $cueMaker
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create game.cue (exit code $LASTEXITCODE)."
        }

        $isoFile = Get-Item -LiteralPath (Join-Path $projectRoot 'game.iso')
        $cueFile = Get-Item -LiteralPath (Join-Path $projectRoot 'game.cue')
        $audioFile = Get-Item -LiteralPath $audioTrack
        $eventAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\GUN.PCM')
        $manifestPath = Join-Path $projectRoot 'build\hardware_release_manifest.txt'
        [IO.File]::WriteAllLines($manifestPath, @(
            'target=sega-saturn-ntsc'
            'video=352x224'
            'boot=iso9660-mode1-2048'
            'expansion_ram=32-mbit-required'
            "profile=$buildProfile"
            "iso_bytes=$($isoFile.Length)"
            "iso_sha256=$((Get-FileHash -LiteralPath $isoFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            "cue_bytes=$($cueFile.Length)"
            "cue_sha256=$((Get-FileHash -LiteralPath $cueFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'audio=track-2-cdda-qsound-reference-mix'
            "audio_bytes=$($audioFile.Length)"
            "audio_sha256=$((Get-FileHash -LiteralPath $audioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio=scsp-pcm-capture-exact-predator-weapon'
            'event_audio_iso_path=/AUDIO/GUN.PCM'
            'event_audio_format=signed-16-bit-big-endian-stereo'
            'event_audio_sample_rate=44100'
            'event_audio_source_frames=2525-input,2530-audible,2582-stop'
            "event_audio_bytes=$($eventAudioFile.Length)"
            "event_audio_sha256=$((Get-FileHash -LiteralPath $eventAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
        ))
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:PATH = $previousPath
}

Write-Host "Built $projectRoot\game.cue, game.iso, and stage1_audio.wav"
Write-Host "Hardware manifest: $projectRoot\build\hardware_release_manifest.txt"
