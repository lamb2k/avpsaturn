[CmdletBinding()]
param(
    [string]$RomRoot = $PSScriptRoot,
    [string]$CaptureName = 'oracle10_round1_system_census',
    [ValidateSet(
        'baseline', 'route_perturbed', 'hold_navigation', 'suppress_street_offense',
        'suppress_warehouse_offense', 'suppress_boss_offense', 'no_continue',
        'remove_class_1f', 'remove_class_00', 'remove_class_01',
        'remove_class_06', 'remove_navigation_bodies',
        'remove_auxiliary_classes', 'freeze_rng')]
    [string[]]$Variants = @(
        'route_perturbed', 'hold_navigation', 'suppress_street_offense',
        'suppress_warehouse_offense', 'suppress_boss_offense', 'no_continue',
        'remove_class_1f', 'remove_class_00', 'remove_class_01',
        'remove_class_06', 'remove_navigation_bodies',
        'remove_auxiliary_classes', 'freeze_rng')
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'

foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing private ORACLE-10 input: $required"
    }
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-10 raw evidence; choose a new CaptureName: $rawRoot"
}

& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS'
    frame_window = @(1972, 18000)
    source_controls = @('full_route', 'full_route_rerun')
    declared_counterfactuals = @(
        'route_perturbed changes only controller schedule and must still reach stable Round 2',
        'hold_navigation suppresses forward input from frames 2600 through 3200',
        'offense variants suppress player gun, attack, and jump only in named route windows',
        'no_continue suppresses coin/start after frame 5600',
        'remove_class variants deactivate only matching active actor records in the fixed source pool',
        'remove_navigation_bodies deactivates classes 0x07 through 0x0a type 0x14',
        'remove_auxiliary_classes deactivates observed classes 0x10/0x3d/0x43/0x45/0x49/0x4b/0x4e/0x80',
        'freeze_rng holds source RNG word 0xff81a8 at its Round 1 entry value')
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    roms = [ordered]@{}
    variants = @()
}
Get-ChildItem -LiteralPath (Join-Path $RomRoot 'avspu') -File |
    Sort-Object Name | ForEach-Object {
        $manifest.roms[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }

foreach ($name in $Variants) {
    $runRoot = Join-Path $rawRoot $name
    New-Item -ItemType Directory -Path $runRoot, (Join-Path $runRoot 'frames') | Out-Null
    if (Test-Path -LiteralPath $liveNvram) {
        Remove-Item -LiteralPath $liveNvram -Recurse -Force
    }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $env:AVSP_ORACLE10_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE10_VARIANT = $name
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle10_round1.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE10_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE10_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('samples.tsv', 'actor_events.tsv', 'actor_writers.tsv',
            'route_writers.tsv', 'qsound_writers.tsv', 'video_events.tsv')) {
        $path = Join-Path $runRoot $file
        $hashes[$file] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{
        name = $name
        sha256 = $hashes
        frame_count = ((Get-Content -LiteralPath (Join-Path $runRoot 'samples.tsv') | Measure-Object -Line).Lines - 1)
    }
}

$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
