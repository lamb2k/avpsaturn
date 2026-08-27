[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [Parameter(Mandatory = $true)][string]$CaptureName
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mame = Join-Path $root '.deps\mame\mame0289\mame.exe'
$out = Join-Path $root ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $root '.deps\mame\full_route_nvram_baseline'
if (Test-Path -LiteralPath $out) { throw "Preserving evidence: $out" }
New-Item -ItemType Directory -Path $out | Out-Null
$nvram = Join-Path $out 'nvram'
$cfg = Join-Path $out 'cfg'
New-Item -ItemType Directory -Path $nvram, $cfg | Out-Null
Copy-Item -LiteralPath $baseline -Destination (Join-Path $nvram 'avspu') -Recurse
$env:AVSP_REIMPLEMENT13_NAV_ROOT = $out.Replace('\', '/')
Push-Location $root
try {
    & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
        '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
        '-nvram_directory' $nvram '-cfg_directory' $cfg `
        '-autoboot_script' '.\tools\mame_capture_reimplement13_navigation_fields.lua'
    if ($LASTEXITCODE -ne 0) { throw "MAME navigation-field capture failed: $LASTEXITCODE" }
}
finally {
    Remove-Item Env:\AVSP_REIMPLEMENT13_NAV_ROOT -ErrorAction SilentlyContinue
    Pop-Location
}
$files = 'navigation_fields.tsv', 'navigation_resolves.tsv', 'camera_bound_writes.tsv', 'terrain_map.bin'
$hashes = [ordered]@{}
foreach ($file in $files) {
    $hashes[$file] = (Get-FileHash (Join-Path $out $file) -Algorithm SHA256).Hash.ToLowerInvariant()
}
[ordered]@{
    schema = 1
    task = 'REIMPLEMENT-13-SOURCE-CLOSED-ROUND1'
    authority_family = 'round1-navigation-terrain-camera-corrective-oracle'
    frame_window = @(3400, 5200)
    mame_sha256 = (Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    nvram_baseline_sha256 = (Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    sha256 = $hashes
} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out 'input_manifest.json') -Encoding utf8
