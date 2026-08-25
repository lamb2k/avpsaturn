[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_locomotion_a',
    [ValidateSet('cold_run_1', 'cold_run_2', 'skip_right_edge',
        'hold_right', 'reverse_without_neutral')]
    [string[]]$Variants = @('cold_run_1', 'cold_run_2',
        'skip_right_edge', 'hold_right', 'reverse_without_neutral')
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
    authority_family = 'predator-warrior-locomotion-neutral-facing'
    frame_window = @(2500, 2760)
    declared_counterfactuals = @(
        'skip_right_edge removes only the first right-input frame',
        'hold_right preserves right input through the neutral-transition window',
        'reverse_without_neutral replaces the release window with left input')
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    variants = @()
}

foreach ($name in $Variants) {
    $runRoot = Join-Path $rawRoot $name
    New-Item -ItemType Directory -Path $runRoot, (Join-Path $runRoot 'frames') | Out-Null
    if (Test-Path -LiteralPath $liveNvram) {
        Remove-Item -LiteralPath $liveNvram -Recurse -Force
    }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'),
            (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) {
            Remove-Item -LiteralPath $stale -Force
        }
    }
    $mode = if ($name -like 'cold_run_*') { 'baseline' } else { $name }
    $env:AVSP_ORACLE11_PLAYER_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE11_PLAYER_VARIANT = $mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle11_player_locomotion.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "MAME $name failed: $LASTEXITCODE"
        }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE11_PLAYER_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE11_PLAYER_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('samples.tsv', 'player_writes.tsv', 'player_entries.tsv')) {
        $path = Join-Path $runRoot $file
        $hashes[$file] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{ name = $name; mode = $mode; sha256 = $hashes }
}

$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
