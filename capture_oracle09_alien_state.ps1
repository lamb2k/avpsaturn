[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle09_alien_state_source_closure',
    [ValidateSet('cold_run_1', 'cold_run_2', 'left_static', 'right_static',
        'above_static', 'below_static', 'cross_left_to_right',
        'cross_right_to_left', 'move_during_attack', 'attack_during_approach',
        'attack_during_attack', 'inside_range', 'outside_range')]
    [string[]]$Variants = @('cold_run_1', 'cold_run_2', 'left_static',
        'right_static', 'above_static', 'below_static', 'cross_left_to_right',
        'cross_right_to_left', 'move_during_attack', 'attack_during_approach',
        'attack_during_attack', 'inside_range', 'outside_range')
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'
foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing private input: $required" }
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-09 raw evidence; choose a new CaptureName: $rawRoot"
}
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION'
    frame_window = @(3900, 4600)
    declared_mutations = @(
        'named player world-position holds or crossings from frame 3975 through 4375',
        'named real-input schedules during approach or attack',
        'P1 high health byte held at 0x65 from frame 3900')
    mame = [ordered]@{ version = (& $mame -version).Trim(); sha256 = (Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant() }
    nvram_baseline_sha256 = (Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    roms = [ordered]@{}
    variants = @()
}
Get-ChildItem -LiteralPath (Join-Path $RomRoot 'avspu') -File |
    Sort-Object Name | ForEach-Object {
        $manifest.roms[$_.Name] = (Get-FileHash -LiteralPath $_.FullName `
            -Algorithm SHA256).Hash.ToLowerInvariant()
    }
foreach ($name in $Variants) {
    $runRoot = Join-Path $rawRoot $name
    New-Item -ItemType Directory -Path $runRoot | Out-Null
    if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $mode = if ($name -like 'cold_run_*') { 'baseline' } else { $name }
    $env:AVSP_ORACLE09_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE09_VARIANT = $mode
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle09_alien_state.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE09_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE09_VARIANT -ErrorAction SilentlyContinue
    }
    $manifest.variants += [ordered]@{
        name = $name; mode = $mode
        samples_sha256 = (Get-FileHash (Join-Path $runRoot 'samples.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        writes_sha256 = (Get-FileHash (Join-Path $runRoot 'enemy_writes.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        class_entries_sha256 = (Get-FileHash (Join-Path $runRoot 'class_entries.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        rng_calls_sha256 = (Get-FileHash (Join-Path $runRoot 'rng_calls.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
