[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_jump_a'
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
        throw "Missing private ORACLE-11 input: $required"
    }
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-11 raw evidence; choose a new CaptureName: $rawRoot"
}

& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'predator-warrior-normal-jump-air-landing'
    frame_window = @(2400, 5469)
    declared_counterfactuals = @(
        'jump_cold_1 and jump_cold_2 are independently launched with identical Button3-only schedules',
        'dash_right adds only held Right to the same Button3 edge and remains a falsification control, not normal-jump authority')
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    variants = @()
}

foreach ($name in @('jump_cold_1', 'jump_cold_2', 'dash_right')) {
    $runRoot = Join-Path $rawRoot $name
    New-Item -ItemType Directory -Path $runRoot, (Join-Path $runRoot 'frames') | Out-Null
    if (Test-Path -LiteralPath $liveNvram) {
        Remove-Item -LiteralPath $liveNvram -Recurse -Force
    }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'),
            (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $mode = if ($name -like 'jump_cold_*') { 'jump_only' } else { 'dash_right' }
    $env:AVSP_ORACLE07_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE07_VARIANT = $mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle07_player_action.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $name failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE07_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE07_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('samples.tsv', 'player_writes.tsv', 'player_global_writes.tsv')) {
        $path = Join-Path $runRoot $file
        $hashes[$file] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{ name = $name; mode = $mode; sha256 = $hashes }
}

$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
