[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_air_a',
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
    [ordered]@{ name = 'air_cold_1'; mode = 'air_cold' },
    [ordered]@{ name = 'air_cold_2'; mode = 'air_cold' },
    [ordered]@{ name = 'dash_right'; mode = 'isolated_dash_right' },
    [ordered]@{ name = 'dash_left'; mode = 'isolated_dash_left' },
    [ordered]@{ name = 'dash_up'; mode = 'isolated_dash_up' },
    [ordered]@{ name = 'dash_down'; mode = 'isolated_dash_down' },
    [ordered]@{ name = 'air_button2_neutral'; mode = 'air_button2_neutral' },
    [ordered]@{ name = 'air_button2_right'; mode = 'air_button2_right' },
    [ordered]@{ name = 'air_button2_left'; mode = 'air_button2_left' },
    [ordered]@{ name = 'air_button2_up'; mode = 'air_button2_up' },
    [ordered]@{ name = 'air_button2_down'; mode = 'air_button2_down' },
    [ordered]@{ name = 'air_button2_hold'; mode = 'air_button2_hold' },
    [ordered]@{ name = 'air_button2_followup_4436'; mode = 'air_button2_followup_4436' },
    [ordered]@{ name = 'air_button2_followup_4442'; mode = 'air_button2_followup_4442' },
    [ordered]@{ name = 'air_button2_followup_4449'; mode = 'air_button2_followup_4449' },
    [ordered]@{ name = 'air_button2_followup_4454'; mode = 'air_button2_followup_4454' },
    [ordered]@{ name = 'air_button2_midair_down'; mode = 'air_button2_midair_down' },
    [ordered]@{ name = 'air_button2_midair_down_followup_4440'; mode = 'air_button2_midair_down_followup_4440' },
    [ordered]@{ name = 'air_button2_midair_down_followup_4448'; mode = 'air_button2_midair_down_followup_4448' },
    [ordered]@{ name = 'dash_right_jump_reverse'; mode = 'dash_right_jump_reverse' },
    [ordered]@{ name = 'air_button1_resource'; mode = 'air_button1_resource' },
    [ordered]@{ name = 'air_button3_repeat'; mode = 'air_button3_repeat' },
    [ordered]@{ name = 'air_button1'; mode = 'air_button1' },
    [ordered]@{ name = 'air_special_combo'; mode = 'air_special_combo' }
)
if ($VariantNames.Count -gt 0) {
    $variants = @($variants | Where-Object { $_.name -in $VariantNames })
    if ($variants.Count -ne $VariantNames.Count) {
        throw 'One or more requested ORACLE-11 air variants are unknown or duplicated'
    }
}
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'predator-warrior-directional-dash-airborne-action-interruption'
    frame_window = @(2400, 5469)
    declared_counterfactuals = @(
        'air_cold_1 and air_cold_2 are independently launched byte-identity controls',
        'direction variants change only held direction around the Button3 edge',
        'air Button1, Button2, Button3-repeat, held-Button2, and Button1+Button2 variants change only the declared airborne edge',
        'active class-0x1f enemies are removed from frame 4200 to prevent natural HIT from masking player action dispatch',
        'the previously captured unmodified dash_right route remains the natural HIT interruption witness'
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
    $env:AVSP_ORACLE07_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE07_VARIANT = $variant.mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle07_player_action.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $($variant.name) failed: $LASTEXITCODE" }
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
    $manifest.variants += [ordered]@{
        name = $variant.name
        mode = $variant.mode
        sha256 = $hashes
    }
}

$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
