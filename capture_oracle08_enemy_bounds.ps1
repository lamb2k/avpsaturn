[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle08_enemy_bounds_source_closure',
    [ValidateSet('cold_run_1', 'cold_run_2', 'beyond_left', 'beyond_right',
        'beyond_lower', 'beyond_upper')]
    [string[]]$Variants = @('cold_run_1', 'cold_run_2', 'beyond_left',
        'beyond_right', 'beyond_lower', 'beyond_upper')
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
    throw "Preserving existing ORACLE-08 raw evidence; choose a new CaptureName: $rawRoot"
}
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS'
    frame_window = @(4150, 4300)
    declared_mutations = @(
        'named one-frame class-0x1f position perturbations at frame 4210',
        'all other active class-0x1f actors deactivated from frame 4200',
        'target slot 0xffa000 health held at 0x65 from frame 4150')
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
    $env:AVSP_ORACLE08_ENEMY_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE08_ENEMY_VARIANT = $mode
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle08_enemy_bounds.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE08_ENEMY_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE08_ENEMY_VARIANT -ErrorAction SilentlyContinue
    }
    $manifest.variants += [ordered]@{
        name = $name; mode = $mode
        samples_sha256 = (Get-FileHash (Join-Path $runRoot 'samples.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        writes_sha256 = (Get-FileHash (Join-Path $runRoot 'enemy_writes.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
