[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle07_player_action_equipment',
    [ValidateSet(
        'cold_run_1', 'cold_run_2', 'single_attack', 'long_idle',
        'delayed_second_60', 'delayed_second_120', 'hold_attack',
        'startup_repeat', 'recovery_repeat', 'movement_attack',
        'reverse_attack', 'gun_only', 'special_only', 'hit_overlap',
        'no_gameplay_buttons', 'isolated_combo_48', 'isolated_combo_49',
        'close_combo_delay_50', 'close_combo_delay_51', 'close_combo_hold',
        'close_combo_startup_repeat', 'close_combo_recovery_repeat',
        'jump_only', 'dash_right')]
    [string[]]$Variants = @(
        'cold_run_1', 'cold_run_2', 'single_attack', 'long_idle',
        'delayed_second_60', 'delayed_second_120', 'hold_attack',
        'startup_repeat', 'recovery_repeat', 'movement_attack',
        'reverse_attack', 'gun_only', 'special_only', 'hit_overlap',
        'no_gameplay_buttons')
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
        throw "Required private input is missing: $required"
    }
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-07 raw evidence; use a new CaptureName: $rawRoot"
}

& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT'
    frame_window = @(2400, 5469)
    declared_mutations = @(
        'input schedules vary by named experiment',
        'P1 high health byte is held at 0x65 from frame 4200 as a survival guard',
        'isolated_combo variants deactivate active class-0x1f enemy slots after frame 4200')
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    variants = @()
    roms = @()
}
Get-ChildItem -LiteralPath (Join-Path $RomRoot 'avspu') -File | Sort-Object Name | ForEach-Object {
    $manifest.roms += [ordered]@{
        name = $_.Name
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
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
    $mode = if ($name -like 'cold_run_*') { 'baseline' } else { $name }
    $env:AVSP_ORACLE07_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE07_VARIANT = $mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle07_player_action.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name capture failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE07_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE07_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('samples.tsv', 'player_writes.tsv', 'player_global_writes.tsv')) {
        $hashes[$file] = (Get-FileHash -LiteralPath (Join-Path $runRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{ name = $name; mode = $mode; sha256 = $hashes }
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
