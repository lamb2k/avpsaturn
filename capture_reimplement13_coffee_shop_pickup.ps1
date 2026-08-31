[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'reimplement13_coffee_shop_pickup_a'
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'
foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing private corrective Oracle input: $required" }
}
if (Test-Path -LiteralPath $rawRoot) { throw "Preserving raw evidence; choose a new CaptureName: $rawRoot" }
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null

$variants = @(
    [ordered]@{ name = 'baseline_1'; mode = 'baseline' },
    [ordered]@{ name = 'baseline_2'; mode = 'baseline' },
    [ordered]@{ name = 'pickup_suppressed'; mode = 'pickup_suppressed' }
)
$manifest = [ordered]@{
    schema = 1
    task = 'REIMPLEMENT-13-SOURCE-CLOSED-ROUND1'
    authority = 'coffee-shop-record28-class0a-health-pickup-corrective-oracle'
    frame_window = @(2600, 3120)
    controls = @(
        'baseline_1 and baseline_2 are independent cold-run identity controls',
        'pickup_suppressed clears only the naturally allocated record28 slot after source allocation and before the next scheduler pass'
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
    $env:AVSP_REIMPLEMENT13_PICKUP_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_REIMPLEMENT13_PICKUP_VARIANT = $variant.mode
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_reimplement13_coffee_shop_pickup.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $($variant.name) failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_REIMPLEMENT13_PICKUP_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_REIMPLEMENT13_PICKUP_VARIANT -ErrorAction SilentlyContinue
        Pop-Location
    }
    $hashes = [ordered]@{}
    foreach ($file in @('record28_writes.tsv', 'samples.tsv', 'source_spawn_guard.tsv')) {
        $hashes[$file] = (Get-FileHash -LiteralPath (Join-Path $runRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest.variants += [ordered]@{ name = $variant.name; mode = $variant.mode; sha256 = $hashes }
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
