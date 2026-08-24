[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest'
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot '.deps\mame\oracle05_street_alien_ai'
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'
$variants = @(
    'cold_run_1', 'cold_run_2', 'distance_far', 'lane_far',
    'attack_timing', 'enemy_health', 'ai_timer', 'rng_state'
)

foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required private input is missing: $required" }
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-05 raw evidence; move it explicitly before recapture: $rawRoot"
}

& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$manifest = [ordered]@{
    schema = 1
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

foreach ($name in $variants) {
    $runRoot = Join-Path $rawRoot $name
    New-Item -ItemType Directory -Path $runRoot | Out-Null
    if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $variant = if ($name -like 'cold_run_*') { 'baseline' } else { $name }
    $env:AVSP_ORACLE05_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE05_VARIANT = $variant
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' '-autoboot_script' '.\tools\mame_capture_oracle05_ai.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name capture failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE05_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE05_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $manifest.variants += [ordered]@{
        name = $name
        mode = $variant
        samples_sha256 = (Get-FileHash -LiteralPath (Join-Path $runRoot 'samples.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        rng_calls_sha256 = (Get-FileHash -LiteralPath (Join-Path $runRoot 'rng_calls.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        scheduler_sha256 = (Get-FileHash -LiteralPath (Join-Path $runRoot 'scheduler.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
        class_entries_sha256 = (Get-FileHash -LiteralPath (Join-Path $runRoot 'class_entries.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
