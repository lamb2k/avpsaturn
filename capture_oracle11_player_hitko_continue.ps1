[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_hitko_continue_a',
    [string[]]$VariantNames = @()
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

$variants = @(
    [ordered]@{ name = 'baseline_hitko_1'; mode = 'baseline_hitko' },
    [ordered]@{ name = 'baseline_hitko_2'; mode = 'baseline_hitko' },
    [ordered]@{ name = 'no_continue'; mode = 'no_continue' },
    [ordered]@{ name = 'coin_only'; mode = 'coin_only' },
    [ordered]@{ name = 'start_only'; mode = 'start_only' },
    [ordered]@{ name = 'delayed_start'; mode = 'delayed_start' },
    [ordered]@{ name = 'survive_contact'; mode = 'survive_contact' },
    [ordered]@{ name = 'respawn_input_suppressed'; mode = 'respawn_input_suppressed' },
    [ordered]@{ name = 'continue_confirm_gun'; mode = 'continue_confirm_gun' },
    [ordered]@{ name = 'continue_confirm_attack'; mode = 'continue_confirm_attack' },
    [ordered]@{ name = 'continue_confirm_jump'; mode = 'continue_confirm_jump' },
    [ordered]@{ name = 'continue_confirm_right'; mode = 'continue_confirm_right' }
)
if ($VariantNames.Count -gt 0) {
    $variants = @($variants | Where-Object { $_.name -in $VariantNames })
    if ($variants.Count -ne $VariantNames.Count) {
        throw 'One or more requested ORACLE-11 HIT/KO variants are unknown or duplicated'
    }
}
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'predator-warrior-hit-ko-failure-continue-respawn-return'
    frame_window = @(5800, 6900)
    declared_counterfactuals = @(
        'baseline_hitko_1 and baseline_hitko_2 are independently launched byte-identity controls',
        'no_continue suppresses only Coin and Start after frame 5600',
        'coin_only and start_only separate the two continue input authorities after frame 5600',
        'delayed_start suppresses the normal frame-6690 Start edge and adds a four-frame Start pulse at frame 6750',
        'survive_contact holds current and latched health at 50 only through frame 6080, before the natural contact',
        'respawn_input_suppressed removes movement and gameplay buttons from frame 6700 while preserving Coin and Start',
        'continue_confirm_gun, continue_confirm_attack, and continue_confirm_jump isolate each gameplay-button confirmation edge',
        'continue_confirm_right preserves only direction after frame 6700 and must not activate the player'
    )
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    variants = @()
}

foreach ($variant in $variants) {
    $runRoot = Join-Path $rawRoot $variant.name
    New-Item -ItemType Directory -Path $runRoot, (Join-Path $runRoot 'frames') | Out-Null
    if (Test-Path -LiteralPath $liveNvram) {
        Remove-Item -LiteralPath $liveNvram -Recurse -Force
    }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'),
            (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $env:AVSP_ORACLE11_HITKO_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE11_HITKO_VARIANT = $variant.mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle11_player_hitko_continue.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $($variant.name) failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE11_HITKO_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE11_HITKO_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('samples.tsv', 'player_writes.tsv',
            'global_writes.tsv', 'qsound_writes.tsv')) {
        $path = Join-Path $runRoot $file
        $hashes[$file] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{
        name = $variant.name
        mode = $variant.mode
        sha256 = $hashes
    }
}
$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
