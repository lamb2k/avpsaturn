[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_route_events_a'
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'
foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing private source input: $required" }
}
if (Test-Path -LiteralPath $rawRoot) { throw "Preserving raw evidence; choose a new CaptureName: $rawRoot" }
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null
if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
    if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
}
$env:AVSP_ORACLE11_PLAYER_EVENTS_ROOT = $rawRoot.Replace('\', '/')
Push-Location $projectRoot
try {
    & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
        '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
        '-autoboot_script' '.\tools\mame_capture_oracle11_player_route_events.lua'
    if ($LASTEXITCODE -ne 0) { throw "MAME route events failed: $LASTEXITCODE" }
}
finally { Remove-Item Env:\AVSP_ORACLE11_PLAYER_EVENTS_ROOT -ErrorAction SilentlyContinue; Pop-Location }
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'predator-warrior-route-audio-load-ownership'
    frame_window = @(1970, 18000)
    mame = [ordered]@{ version = (& $mame -version).Trim(); sha256 = (Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant() }
    nvram_baseline_sha256 = (Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    sha256 = [ordered]@{}
}
foreach ($file in @('samples.tsv','audio_writes.tsv','gfx_writes.tsv')) {
    $manifest.sha256[$file] = (Get-FileHash (Join-Path $rawRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
