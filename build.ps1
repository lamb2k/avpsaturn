[CmdletBinding()]
param(
    [string]$JoEngineRoot,
    [string]$PythonPath,
    [switch]$Clean,
    [switch]$Release,
    [switch]$VisualTest,
    [switch]$EncounterTest,
    [switch]$BossHitTest,
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
        & '.\prepare_enemy_contact_audio.ps1' -PythonPath $PythonPath
        if ($LASTEXITCODE -ne 0) {
            throw "Enemy-contact audio preparation failed with exit code $LASTEXITCODE."
        }
        & '.\prepare_stage1_sequence_audio.ps1' -PythonPath $PythonPath
        if ($LASTEXITCODE -ne 0) {
            throw "Stage 1 sequence audio preparation failed with exit code $LASTEXITCODE."
        }
        & '.\prepare_stage1_opening_audio.ps1' -PythonPath $PythonPath
        if ($LASTEXITCODE -ne 0) {
            throw "Stage 1 opening audio preparation failed with exit code $LASTEXITCODE."
        }

        $contentRoot = Join-Path $projectRoot 'build\avsp_cd'
        foreach ($metadataName in @('ABS.TXT', 'BIB.TXT', 'CPY.TXT')) {
            Copy-Item -LiteralPath (Join-Path $projectRoot "cd\$metadataName") `
                -Destination (Join-Path $contentRoot $metadataName) -Force
        }

        $buildProfile = if ($BossHitTest) { 'boss-hit-test' }
            elseif ($EncounterTest) { 'encounter-test' }
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
        if ($BossHitTest) {
            $makeArguments += 'AVSP_BOSS_HIT_TEST=1'
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
            'game.iso' '/SPR4/BACT.RLE' '--equals' `
            (Join-Path $contentRoot 'SPR4\BACT.RLE')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn Chrysalis archive ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/SPR4/BHIT.RLE' '--equals' `
            (Join-Path $contentRoot 'SPR4\BHIT.RLE')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn Chrysalis hit archive ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/SPR4/SACT.RLE' '--equals' `
            (Join-Path $contentRoot 'SPR4\SACT.RLE')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn Stalker archive ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/GUN.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\GUN.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/MELEE.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\MELEE.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn melee PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/HIT.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\HIT.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn hit PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/IMPACT.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\IMPACT.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn impact PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/KOIMP.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\KOIMP.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn KO-impact PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/CONTACT.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\CONTACT.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn contact-composite PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/KOCONT.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\KOCONT.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn KO-contact-composite PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/BOSSIN.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\BOSSIN.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn boss-intro PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/BOSSCLR.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\BOSSCLR.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn boss-clear PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/DOOR.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\DOOR.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn door-dialogue PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/AUDIO/TRANS.PCM' '--equals' `
            (Join-Path $contentRoot 'AUDIO\TRANS.PCM')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn interior-transition PCM ISO verification failed with exit code $LASTEXITCODE."
        }
        foreach ($openingPcm in @('RND1A.PCM', 'RND1B.PCM', 'WITHDRW.PCM', 'BREACH.PCM')) {
            & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
                'game.iso' "/AUDIO/$openingPcm" '--equals' `
                (Join-Path $contentRoot "AUDIO\$openingPcm")
            if ($LASTEXITCODE -ne 0) {
                throw "Saturn opening PCM ISO verification failed for $openingPcm with exit code $LASTEXITCODE."
            }
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
        $meleeAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\MELEE.PCM')
        $hitAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\HIT.PCM')
        $impactAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\IMPACT.PCM')
        $koImpactAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\KOIMP.PCM')
        $contactAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\CONTACT.PCM')
        $koContactAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\KOCONT.PCM')
        $bossIntroAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\BOSSIN.PCM')
        $bossClearAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\BOSSCLR.PCM')
        $doorDialogueAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\DOOR.PCM')
        $interiorTransitionAudioFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'AUDIO\TRANS.PCM')
        $roundTitleAFile = Get-Item -LiteralPath (Join-Path $contentRoot 'AUDIO\RND1A.PCM')
        $roundTitleBFile = Get-Item -LiteralPath (Join-Path $contentRoot 'AUDIO\RND1B.PCM')
        $withdrawAudioFile = Get-Item -LiteralPath (Join-Path $contentRoot 'AUDIO\WITHDRW.PCM')
        $breachAudioFile = Get-Item -LiteralPath (Join-Path $contentRoot 'AUDIO\BREACH.PCM')
        $stalkerArchiveFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'SPR4\SACT.RLE')
        $bossArchiveFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'SPR4\BACT.RLE')
        $bossHitArchiveFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'SPR4\BHIT.RLE')
        $manifestPath = Join-Path $projectRoot 'build\hardware_release_manifest.txt'
        [IO.File]::WriteAllLines($manifestPath, @(
            'target=sega-saturn-ntsc'
            'video=352x224'
            'boot=iso9660-mode1-2048'
            'expansion_ram=32-mbit-required'
            'expansion_ram_mapping=dram0-0x22400000-0x225fffff,dram1-0x22600000-0x227fffff'
            'boss_archive_iso_path=/SPR4/BACT.RLE'
            'boss_archive_load_phase=cold-boot'
            "boss_archive_bytes=$($bossArchiveFile.Length)"
            "boss_archive_sha256=$((Get-FileHash -LiteralPath $bossArchiveFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'boss_hit_archive_iso_path=/SPR4/BHIT.RLE'
            'boss_hit_archive_load_phase=retired-character-select-before-cdda'
            "boss_hit_archive_bytes=$($bossHitArchiveFile.Length)"
            "boss_hit_archive_sha256=$((Get-FileHash -LiteralPath $bossHitArchiveFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'stalker_archive_iso_path=/SPR4/SACT.RLE'
            'stalker_archive_phase_overlay=retired-title-surface-before-cdda'
            "stalker_archive_bytes=$($stalkerArchiveFile.Length)"
            "stalker_archive_sha256=$((Get-FileHash -LiteralPath $stalkerArchiveFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
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
            'event_audio_2=scsp-pcm-capture-exact-predator-melee'
            'event_audio_2_iso_path=/AUDIO/MELEE.PCM'
            'event_audio_2_format=signed-16-bit-big-endian-stereo'
            'event_audio_2_sample_rate=44100'
            'event_audio_2_source_frames=2525-input,2528-audible,2578-stop'
            "event_audio_2_bytes=$($meleeAudioFile.Length)"
            "event_audio_2_sha256=$((Get-FileHash -LiteralPath $meleeAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_3=scsp-pcm-capture-exact-predator-damage'
            'event_audio_3_iso_path=/AUDIO/HIT.PCM'
            'event_audio_3_format=signed-16-bit-big-endian-stereo'
            'event_audio_3_sample_rate=44100'
            'event_audio_3_source_frames=4243-health-loss,4246-audible,4274-stop'
            "event_audio_3_bytes=$($hitAudioFile.Length)"
            "event_audio_3_sha256=$((Get-FileHash -LiteralPath $hitAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_4=scsp-pcm-capture-exact-alien-contact-impact'
            'event_audio_4_iso_path=/AUDIO/IMPACT.PCM'
            'event_audio_4_format=signed-16-bit-big-endian-stereo'
            'event_audio_4_sample_rate=44100'
            'event_audio_4_source_frames=4243-health-loss,4245-audible,4268-stop'
            "event_audio_4_bytes=$($impactAudioFile.Length)"
            "event_audio_4_sha256=$((Get-FileHash -LiteralPath $impactAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_5=scsp-pcm-capture-exact-alien-contact-ko-impact'
            'event_audio_5_iso_path=/AUDIO/KOIMP.PCM'
            'event_audio_5_format=signed-16-bit-big-endian-stereo'
            'event_audio_5_sample_rate=44100'
            'event_audio_5_source_frames=4433-health-loss,4435-audible,4461-stop'
            "event_audio_5_bytes=$($koImpactAudioFile.Length)"
            "event_audio_5_sha256=$((Get-FileHash -LiteralPath $koImpactAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_6=scsp-pcm-runtime-alien-contact-composite'
            'event_audio_6_iso_path=/AUDIO/CONTACT.PCM'
            'event_audio_6_format=signed-16-bit-big-endian-stereo'
            'event_audio_6_sample_rate=44100'
            'event_audio_6_source_frames=4243-health-loss,4245-impact,4246-vocal,4274-stop'
            "event_audio_6_bytes=$($contactAudioFile.Length)"
            "event_audio_6_sha256=$((Get-FileHash -LiteralPath $contactAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_7=scsp-pcm-runtime-alien-ko-contact-composite'
            'event_audio_7_iso_path=/AUDIO/KOCONT.PCM'
            'event_audio_7_format=signed-16-bit-big-endian-stereo'
            'event_audio_7_sample_rate=44100'
            'event_audio_7_source_frames=4433-health-loss,4435-impact,4436-vocal,4464-stop'
            "event_audio_7_bytes=$($koContactAudioFile.Length)"
            "event_audio_7_sha256=$((Get-FileHash -LiteralPath $koContactAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_8=scsp-pcm-capture-exact-chrysalis-boss-intro'
            'event_audio_8_iso_path=/AUDIO/BOSSIN.PCM'
            'event_audio_8_format=signed-16-bit-big-endian-stereo'
            'event_audio_8_sample_rate=44100'
            'event_audio_8_source_frames=5460-boss-room-entry,5468-voice-start,5509-stop'
            "event_audio_8_bytes=$($bossIntroAudioFile.Length)"
            "event_audio_8_sha256=$((Get-FileHash -LiteralPath $bossIntroAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_9=scsp-pcm-capture-exact-chrysalis-defeat-stage-clear'
            'event_audio_9_iso_path=/AUDIO/BOSSCLR.PCM'
            'event_audio_9_format=signed-16-bit-big-endian-stereo'
            'event_audio_9_sample_rate=44100'
            'event_audio_9_source_frames=13920-boss-defeated,14070-voice12,14126-voice10,14190-voice12,14269-stop'
            "event_audio_9_bytes=$($bossClearAudioFile.Length)"
            "event_audio_9_sha256=$((Get-FileHash -LiteralPath $bossClearAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_10=scsp-pcm-capture-exact-door-dialogue'
            'event_audio_10_iso_path=/AUDIO/DOOR.PCM'
            'event_audio_10_format=signed-16-bit-big-endian-stereo'
            'event_audio_10_sample_rate=44100'
            'event_audio_10_source_frames=5340-door-dialogue,5384-voice4,5434-replaced'
            "event_audio_10_bytes=$($doorDialogueAudioFile.Length)"
            "event_audio_10_sha256=$((Get-FileHash -LiteralPath $doorDialogueAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_11=scsp-pcm-capture-exact-interior-transition'
            'event_audio_11_iso_path=/AUDIO/TRANS.PCM'
            'event_audio_11_format=signed-16-bit-big-endian-stereo'
            'event_audio_11_sample_rate=44100'
            'event_audio_11_source_frames=5400-interior-transition,5438-voice13,5491-stop'
            "event_audio_11_bytes=$($interiorTransitionAudioFile.Length)"
            "event_audio_11_sha256=$((Get-FileHash -LiteralPath $interiorTransitionAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_12=scsp-pcm-capture-exact-round-title-lead'
            'event_audio_12_iso_path=/AUDIO/RND1A.PCM'
            'event_audio_12_format=signed-16-bit-big-endian-stereo'
            'event_audio_12_sample_rate=44100'
            'event_audio_12_source_frames=1800-confirm,2031-voice13,2035-voice14,2070-stop'
            "event_audio_12_bytes=$($roundTitleAFile.Length)"
            "event_audio_12_sha256=$((Get-FileHash -LiteralPath $roundTitleAFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_13=scsp-pcm-capture-exact-round-title-tail'
            'event_audio_13_iso_path=/AUDIO/RND1B.PCM'
            'event_audio_13_format=signed-16-bit-big-endian-stereo'
            'event_audio_13_sample_rate=44100'
            'event_audio_13_source_frames=2040-title,2076-voice14,2107-stop'
            "event_audio_13_bytes=$($roundTitleBFile.Length)"
            "event_audio_13_sha256=$((Get-FileHash -LiteralPath $roundTitleBFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_14=scsp-pcm-capture-exact-withdraw-sequence'
            'event_audio_14_iso_path=/AUDIO/WITHDRW.PCM'
            'event_audio_14_format=signed-16-bit-big-endian-stereo'
            'event_audio_14_sample_rate=44100'
            'event_audio_14_source_frames=2160-barricade,2255-first-start,2388-stop'
            "event_audio_14_bytes=$($withdrawAudioFile.Length)"
            "event_audio_14_sha256=$((Get-FileHash -LiteralPath $withdrawAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
            'event_audio_15=scsp-pcm-capture-exact-barricade-breach'
            'event_audio_15_iso_path=/AUDIO/BREACH.PCM'
            'event_audio_15_format=signed-16-bit-big-endian-stereo'
            'event_audio_15_sample_rate=44100'
            'event_audio_15_source_frames=2400-breach,2419-first-start,2518-stop'
            "event_audio_15_bytes=$($breachAudioFile.Length)"
            "event_audio_15_sha256=$((Get-FileHash -LiteralPath $breachAudioFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
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
