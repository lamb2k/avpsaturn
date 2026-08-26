[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_route_ownership_a',
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
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing private ORACLE-11 input: $required" }
}
if (Test-Path -LiteralPath $rawRoot) { throw "Preserving raw evidence; choose a new CaptureName: $rawRoot" }
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$variants = @(
    [ordered]@{ name = 'route_interaction_1'; mode = 'baseline' },
    [ordered]@{ name = 'route_interaction_2'; mode = 'baseline' },
    [ordered]@{ name = 'health_max'; mode = 'health_max' },
    [ordered]@{ name = 'effect_pool_unavailable'; mode = 'effect_pool_unavailable' },
    [ordered]@{ name = 'interaction_uninterrupted'; mode = 'interaction_uninterrupted' },
    [ordered]@{ name = 'resource_pickup_near'; mode = 'resource_pickup_near' }
)
if ($VariantNames.Count -gt 0) {
    $variants = @($variants | Where-Object { $_.name -in $VariantNames })
    if ($variants.Count -ne $VariantNames.Count) { throw 'Unknown or duplicated player-route variant' }
}
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'predator-warrior-route-pickup-resource-audio-load-ownership'
    frame_window = @(2800, 4200)
    declared_counterfactuals = @(
        'route_interaction_1 and route_interaction_2 are independent cold-run identity controls',
        'health_max holds current and latched health at the source maximum only before the natural health interaction',
        'effect_pool_unavailable makes only the record24 allocator unavailable across the natural effect allocation',
        'interaction_uninterrupted removes gameplay-button edges after the natural frame-4032 interaction entry while preserving route movement',
        'resource_pickup_near changes only the current record28 class0x0e world position and supplies one real Button2 edge after native target acquisition; source targeting, grant, and actor allocation remain authoritative'
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
    New-Item -ItemType Directory -Path $runRoot | Out-Null
    if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $env:AVSP_ORACLE11_PLAYER_ROUTE_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE11_PLAYER_ROUTE_VARIANT = $variant.mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle11_player_route_ownership.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $($variant.name) failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE11_PLAYER_ROUTE_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE11_PLAYER_ROUTE_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('samples.tsv', 'writes.tsv', 'actors.tsv', 'qsound.tsv')) {
        $path = Join-Path $runRoot $file
        $hashes[$file] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{ name = $variant.name; mode = $variant.mode; sha256 = $hashes }
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
