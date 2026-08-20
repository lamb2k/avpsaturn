[CmdletBinding()]
param(
    [string]$JoEngineRoot,
    [string]$PythonPath,
    [switch]$Clean,
    [switch]$Release,
    [switch]$VisualTest,
    [switch]$FrontendTest,
    [switch]$FrontendShotTest,
    [switch]$EncounterTest,
    [switch]$StreetTest,
    [switch]$BossHitTest,
    [switch]$BossKoTest,
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

# One shared generator harness (clean-checkout correction): runs a
# generator, checks its exit code, confirms every declared output exists
# and is nonzero, and names the exact missing private input when the
# generation cannot run at all.
function Invoke-Generator {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string[]]$Command,
        [string[]]$RequiredInputs = @(),
        [string[]]$DeclaredOutputs = @()
    )
    foreach ($required in $RequiredInputs) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw "$Name cannot run: required private input is missing: $required"
        }
    }
    & $Command[0] @($Command[1..($Command.Count - 1)])
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
    foreach ($output in $DeclaredOutputs) {
        if (-not (Test-Path -LiteralPath $output)) {
            throw "$Name exited 0 but did not produce $output."
        }
        if ((Get-Item -LiteralPath $output).Length -eq 0) {
            throw "$Name produced an empty $output."
        }
    }
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
        & $PythonPath (Join-Path $projectRoot 'tools\gen_avsp_table_set_classes.py')
        if ($LASTEXITCODE -ne 0) {
            throw "Class-to-table-set lookup generation failed with exit code $LASTEXITCODE."
        }
        $animRom = Join-Path $projectRoot '.deps\mame\actorprobe\decrypted_program_2m.bin'
        $animCaptureA = Join-Path $projectRoot '.deps\mame\collision_probe\workram.bin'
        $animCaptureB = Join-Path $projectRoot '.deps\mame\collision_probe_boss\workram.bin'
        $animAnchorRoot = Join-Path $projectRoot '.deps\mame\enemy_actions'
        if ((Test-Path -LiteralPath $animRom) -and
            (Test-Path -LiteralPath $animCaptureA) -and
            (Test-Path -LiteralPath $animCaptureB) -and
            (Test-Path -LiteralPath (Join-Path $animAnchorRoot 'workram_05191.bin')) -and
            (Test-Path -LiteralPath (Join-Path $animAnchorRoot 'workram_05469.bin'))) {
            & $PythonPath (Join-Path $projectRoot 'tools\gen_avsp_anim_records.py') `
                '--rom' $animRom '--capture' $animCaptureA '--capture' $animCaptureB `
                '--capture-dir-range' "$animAnchorRoot`:5191`:5226" `
                '--capture-dir-range' "$animAnchorRoot`:5330`:5469" `
                '--verify-deterministic'
            if ($LASTEXITCODE -ne 0) {
                throw "Animation-record extraction failed with exit code $LASTEXITCODE."
            }
        }
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

        # ROM-derived actor emission windows and boss pose tables: explicit
        # build steps (not preflight side effects), each through the shared
        # generator harness so a missing private input is named exactly.
        Invoke-Generator -Name 'Actor emission-window generation' `
            -Command @($PythonPath, (Join-Path $projectRoot 'tools\gen_avsp_emit_windows.py')) `
            -RequiredInputs @((Join-Path $projectRoot '.deps\mame\actorprobe\decrypted_program_2m.bin')) `
            -DeclaredOutputs @((Join-Path $projectRoot 'generated\avsp_emit_windows.h'))
        Invoke-Generator -Name 'Boss ROM pose-table generation' `
            -Command @($PythonPath, (Join-Path $projectRoot 'tools\gen_boss_rom_data.py')) `
            -RequiredInputs @((Join-Path $projectRoot '.deps\mame\actorprobe'),
                              (Join-Path $projectRoot 'generated\avsp_boss_animation.h')) `
            -DeclaredOutputs @((Join-Path $projectRoot 'generated\avsp_boss_rom.h'))

        # Rebuild the private ROM-derived frontend payload after the general
        # asset extractor. The converter owns build\avsp_cd\FRONT and enforces
        # exact source composition, deterministic hashes and both 78,848-byte
        # lifetime budgets before the ISO is assembled.
        & $PythonPath (Join-Path $projectRoot 'tools\gen_avsp_frontend.py') `
            '--verify-deterministic'
        if ($LASTEXITCODE -ne 0) {
            throw "ROM-derived frontend generation failed with exit code $LASTEXITCODE."
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

        # S2 Body E: the ROM tile archive for the per-object VDP1 renderer.
        # ALWAYS regenerated here, with an EXPLICIT scope - never inferred
        # from whether the file happens to exist. A prior version reused
        # the file if present, which silently broke when a separate sweep
        # (extract_avspu_stage1.py's SPR4 cleanup, now excluding TILES.BIN)
        # deleted it: the "if present" check then always regenerated at
        # whatever the tool's DEFAULT scope happened to be, not the scope
        # the normal build actually needs. The generator itself refuses to
        # write an archive bigger than the runtime's AVSP_TILE_REGION_BYTES
        # carve, so a scope mismatch fails here, not at boot.
        $tileArchive = Join-Path $projectRoot 'build\avsp_cd\SPR4\TILES.BIN'
        $tileManifest = Join-Path $projectRoot 'data\avsp_gfx_tiles.json'
        & $PythonPath (Join-Path $projectRoot 'tools\gen_avsp_gfx_tiles.py') `
            '--scope' 'street'
        if ($LASTEXITCODE -ne 0) {
            throw "ROM tile archive generation failed with exit code $LASTEXITCODE."
        }
        if (-not (Test-Path -LiteralPath $tileArchive)) {
            throw 'build\avsp_cd\SPR4\TILES.BIN is missing after generation.'
        }
        $tileManifestData = Get-Content -LiteralPath $tileManifest -Raw | ConvertFrom-Json
        if ($tileManifestData.scope -ne 'street') {
            throw "Tile archive manifest scope is '$($tileManifestData.scope)', expected 'street'."
        }
        $tileArchiveBytes = (Get-Item -LiteralPath $tileArchive).Length
        if ($tileArchiveBytes -ne $tileManifestData.archive.bytes) {
            throw "Tile archive on disk is $tileArchiveBytes bytes but the manifest records $($tileManifestData.archive.bytes)."
        }
        Write-Host "Tile archive: $tileArchiveBytes bytes, scope=street, budget $($tileManifestData.tile_region_budget_used_pct)% used"

        $contentRoot = Join-Path $projectRoot 'build\avsp_cd'
        # RP4 fixture separation: the captured street strips are a
        # validation fixture and ship only in the StreetTest profile.
        $fixtureSource = Join-Path $projectRoot 'build\rp4_fixture\STRIPS.BIN'
        $fixtureStaged = Join-Path $contentRoot 'ST1\STRIPS.BIN'
        if ($StreetTest) {
            if (-not (Test-Path -LiteralPath $fixtureSource)) {
                throw 'StreetTest requires build\rp4_fixture\STRIPS.BIN (run tools\gen_avsp_street_planes.py).'
            }
            New-Item -ItemType Directory -Force -Path (Join-Path $contentRoot 'ST1') | Out-Null
            Copy-Item -LiteralPath $fixtureSource -Destination $fixtureStaged -Force
        }
        elseif (Test-Path -LiteralPath $fixtureStaged) {
            Remove-Item -LiteralPath $fixtureStaged -Force
        }
        foreach ($metadataName in @('ABS.TXT', 'BIB.TXT', 'CPY.TXT')) {
            Copy-Item -LiteralPath (Join-Path $projectRoot "cd\$metadataName") `
                -Destination (Join-Path $contentRoot $metadataName) -Force
        }

        $buildProfile = if ($BossKoTest) { 'boss-ko-test' }
            elseif ($BossHitTest) { 'boss-hit-test' }
            elseif ($EncounterTest) { 'encounter-test' }
            elseif ($StreetTest) { 'street-test' }
            elseif ($FrontendTest) { 'frontend-test' }
            elseif ($FrontendShotTest) { 'frontend-shot-test' }
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
                'cd\0.bin', 'build\avsp_cd\0.bin',
                'build\avsp_cd\GAME.BIN', 'loader\loader.o',
                'loader\trampoline.o',
                'build\loader\loader.elf', 'build\loader\loader.raw',
                'build\loader\loader.map', 'build\loader\IP.BIN'
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
        if ($StreetTest) {
            $makeArguments += 'AVSP_STREET_TEST=1'
        }
        if ($FrontendTest) {
            $makeArguments += 'AVSP_FRONTEND_TEST=1'
        }
        if ($FrontendShotTest) {
            $makeArguments += 'AVSP_FRONTEND_SHOT_TEST=1'
        }
        if ($BossHitTest) {
            $makeArguments += 'AVSP_BOSS_HIT_TEST=1'
        }
        if ($BossKoTest) {
            $makeArguments += 'AVSP_BOSS_KO_TEST=1'
        }
        # Clean-checkout preflight: every generated header main.c compiles
        # against must exist by now (the prepare stages above produce most);
        # missing ones with runnable deterministic producers are generated
        # here, and anything else fails with the exact missing generator or
        # private input instead of a bare missing-include error mid-make.
        & $PythonPath (Join-Path $projectRoot 'tools\preflight_generated_inputs.py')
        if ($LASTEXITCODE -ne 0) {
            throw "Generated-input preflight failed with exit code $LASTEXITCODE."
        }

        $loaderBuildRoot = Join-Path $projectRoot 'build\loader'
        New-Item -ItemType Directory -Path $loaderBuildRoot -Force | Out-Null
        $makeArguments += 'game.raw'
        & $make @makeArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn compilation failed with exit code $LASTEXITCODE."
        }
        $gameMapText = Get-Content -LiteralPath `
            (Join-Path $projectRoot 'game.map') -Raw
        $loaderMakeArguments = @(
            $makeArguments | Where-Object { $_ -ne 'game.raw' })
        $loaderMakeArguments += 'build/loader/loader.raw'
        & $make @loaderMakeArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn loader compilation failed with exit code $LASTEXITCODE."
        }
        # The pinned Yaba path has a measured 400 KiB monolithic first-read
        # envelope. The staged architecture keeps only this loader in the BIOS
        # first read at Jo Engine's proven 0x06004000 destination. It stages
        # GAME.BIN in 1 MiB low work RAM, then overwrites the loader through a
        # tiny trampoline at 0x060d0000 and transfers control to GAME.BIN's own
        # Jo startup at 0x06004000. Attempts to move Jo's AIP first-read
        # target to 0x060f0000 and 0x060d0000 both left pinned Yaba in its IP
        # wait loop, even though readback proved the file had transferred.
        $loaderBinary = Get-Item -LiteralPath `
            (Join-Path $loaderBuildRoot 'loader.raw')
        $loaderReadEnvelopeBytes = 400KB
        if ($loaderBinary.Length -gt $loaderReadEnvelopeBytes) {
            throw "Saturn first-stage loader is $($loaderBinary.Length) bytes; " +
                "the measured pinned-Yaba first-read envelope is " +
                "$loaderReadEnvelopeBytes bytes."
        }
        $loaderMapText = Get-Content -LiteralPath `
            (Join-Path $loaderBuildRoot 'loader.map') -Raw
        $loaderBssMatch = [regex]::Match(
            $loaderMapText, '0x([0-9a-fA-F]{8})\s+__bend\s*=')
        if (-not $loaderBssMatch.Success) {
            throw 'Could not locate __bend in the first-stage loader map.'
        }
        $loaderBssEnd = [Convert]::ToUInt32($loaderBssMatch.Groups[1].Value, 16)
        if ($loaderBssEnd -gt 0x060CFFF0) {
            throw ('First-stage loader BSS ends at 0x{0:x8}; it overlaps ' +
                'the loader diagnostic/trampoline handoff area.') -f $loaderBssEnd
        }
        $gamePayload = Get-Item -LiteralPath (Join-Path $projectRoot 'game.raw')
        if ($gamePayload.Length -gt 1MB) {
            throw "GAME.BIN exceeds the 1 MiB low-work-RAM staging area."
        }
        $gameBssMatch = [regex]::Match(
            $gameMapText, '0x([0-9a-fA-F]{8})\s+__bend\s*=')
        if (-not $gameBssMatch.Success) {
            throw 'Could not locate __bend in the GAME.BIN map.'
        }
        $gameBssEnd = [Convert]::ToUInt32($gameBssMatch.Groups[1].Value, 16)
        # Hard bound: JO_WORK_RAM_SORT_LIST / JO_WORK_RAM_USER_PROGRAM_AND_DATA_END.
        # Anything at or past 0x060c0000 is outside Jo's user work-RAM area and
        # inside SGL's sort-list region. Jo's own jo_sprite_init() bounds-checks
        # __jo_sprite_def/__jo_sprite_pic against this limit and, when it fails,
        # reports the MISLEADING message 'Please reduce
        # JO_GLOBAL_MEMORY_SIZE_FOR_MALLOC' before jo_core_suspend() waits
        # forever for START - which presents as a nondeterministic boot hang,
        # not as a memory error. This check exists so that failure is caught at
        # build time instead. The older 0x060d0000 trampoline bound was too
        # permissive to catch it.
        if ($gameBssEnd -gt 0x060C0000) {
            throw ('GAME.BIN BSS ends at 0x{0:x8}, past the 0x060c0000 ' +
                'user work-RAM limit (SGL sort list). Jo''s jo_sprite_init() ' +
                'will fail its bounds check and suspend at its error screen. ' +
                'Reclaim BSS (e.g. JO_MAX_SPRITE) rather than shrinking the ' +
                'malloc arena or disabling JO_DEBUG.') -f $gameBssEnd
        }
        $loaderSummary = ("First-stage loader: {0} bytes, " +
            "BSS end 0x{1:x8}, {2} bytes below its file envelope") -f `
            $loaderBinary.Length, $loaderBssEnd, `
            ($loaderReadEnvelopeBytes - $loaderBinary.Length)
        Write-Host $loaderSummary
        $gameSummary = ("Staged GAME.BIN: {0} bytes via low work RAM, " +
            "BSS end 0x{1:x8}, final entry 0x06004000") -f `
            $gamePayload.Length, $gameBssEnd
        Write-Host $gameSummary
        [IO.File]::WriteAllText($profileStamp, $compileProfile)

        Copy-Item -LiteralPath $loaderBinary.FullName `
            -Destination (Join-Path $contentRoot '0.bin') -Force
        Copy-Item -LiteralPath $gamePayload.FullName `
            -Destination (Join-Path $contentRoot 'GAME.BIN') -Force
        $loaderIp = Join-Path $loaderBuildRoot 'IP.BIN'
        & $PythonPath (Join-Path $projectRoot 'tools\build_loader_ip.py') `
            (Join-Path $resolvedEngine 'Compiler\COMMON\IP.BIN') $loaderIp
        if ($LASTEXITCODE -ne 0) {
            throw "Could not build the staged-loader IP.BIN (exit code $LASTEXITCODE)."
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
            '-generic-boot', $loaderIp,
            '-full-iso9660-filenames',
            '-o', 'game.iso', $contentRoot
        )
        & $mkisofs @mkisofsArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create game.iso (exit code $LASTEXITCODE)."
        }
        foreach ($bootMember in @(
            @{ Iso = '/0.bin'; Local = (Join-Path $contentRoot '0.bin') },
            @{ Iso = '/GAME.BIN'; Local = (Join-Path $contentRoot 'GAME.BIN') }
        )) {
            & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
                'game.iso' $bootMember.Iso '--equals' $bootMember.Local
            if ($LASTEXITCODE -ne 0) {
                throw "Staged boot ISO verification failed for $($bootMember.Iso)."
            }
        }
        $frontendManifest = Get-Content -LiteralPath `
            (Join-Path $projectRoot 'data\avsp_frontend_assets.json') -Raw |
            ConvertFrom-Json
        foreach ($frontendAsset in $frontendManifest.assets) {
            $isoMember = '/' + ($frontendAsset.path -replace '\\', '/')
            $localMember = Join-Path $contentRoot `
                ($frontendAsset.path -replace '/', '\')
            & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
                'game.iso' $isoMember '--equals' $localMember
            if ($LASTEXITCODE -ne 0) {
                throw "Saturn frontend ISO verification failed for $isoMember with exit code $LASTEXITCODE."
            }
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
            'game.iso' '/SPR4/BKO.RLE' '--equals' `
            (Join-Path $contentRoot 'SPR4\BKO.RLE')
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn Chrysalis KO archive ISO verification failed with exit code $LASTEXITCODE."
        }
        & $PythonPath (Join-Path $projectRoot 'tools\verify_iso_file.py') `
            'game.iso' '/SPR4/TILES.BIN' '--equals' `
            (Join-Path $contentRoot 'SPR4\TILES.BIN')
        if ($LASTEXITCODE -ne 0) {
            throw "ROM tile archive ISO verification failed with exit code $LASTEXITCODE."
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
        $bossKoArchiveFile = Get-Item -LiteralPath `
            (Join-Path $contentRoot 'SPR4\BKO.RLE')
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
            'boss_ko_archive_iso_path=/SPR4/BKO.RLE'
            'boss_ko_archive_load_phase=retired-character-select-before-cdda'
            "boss_ko_archive_bytes=$($bossKoArchiveFile.Length)"
            "boss_ko_archive_sha256=$((Get-FileHash -LiteralPath $bossKoArchiveFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant())"
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
