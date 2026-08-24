[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle06_round1_encounter',
    [ValidateSet('cold_run_1', 'cold_run_2', 'entry_hold', 'clear_attack_suppression')]
    [string[]]$Variants = @(
        'cold_run_1', 'cold_run_2', 'entry_hold', 'clear_attack_suppression'),
    [int]$FirstFrame = 2200,
    [int]$LastFrame = 7200
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'

foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required private input is missing: $required" }
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-06 raw evidence; use a new CaptureName: $rawRoot"
}

& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$manifest = [ordered]@{
    schema = 1
    route = 'repeated Coin pulses 1200..2400; Start 2405..2407; story skip 2500..2504; default Predator Warrior confirm 3300..3304; gameplay inputs from 3700'
    frame_window = @($FirstFrame, $LastFrame)
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
    if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $mode = if ($name -like 'cold_run_*') { 'baseline' } else { $name }
    $env:AVSP_ORACLE06_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE06_VARIANT = $mode
    $env:AVSP_ORACLE06_FIRST_FRAME = [string]$FirstFrame
    $env:AVSP_ORACLE06_LAST_FRAME = [string]$LastFrame
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' '-autoboot_script' '.\tools\mame_capture_oracle06_encounter.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name capture failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE06_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE06_VARIANT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE06_FIRST_FRAME -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE06_LAST_FRAME -ErrorAction SilentlyContinue
        Pop-Location
    }
    $files = [ordered]@{}
    foreach ($file in @('samples.tsv', 'actors.tsv', 'controller_writes.tsv', 'qsound.tsv')) {
        $files[$file] = (Get-FileHash -LiteralPath (Join-Path $runRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{ name = $name; mode = $mode; sha256 = $files }
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
