[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [Parameter(Mandatory = $true)][string]$CaptureName,
    [string]$SuppressFrame = '',
    [ValidateSet('', 'gfxram0', 'gfxram1', 'gfxram2')][string]$SuppressRegion = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
if (Test-Path -LiteralPath $rawRoot) { throw "Preserving evidence: $rawRoot" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null
$runNvramRoot = Join-Path $rawRoot 'nvram'; $runCfgRoot = Join-Path $rawRoot 'cfg'
New-Item -ItemType Directory -Path $runNvramRoot, $runCfgRoot | Out-Null
Copy-Item -LiteralPath $baseline -Destination (Join-Path $runNvramRoot 'avspu') -Recurse
$env:AVSP_ORACLE11_LOAD_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_LOAD_SUPPRESS_FRAME = $SuppressFrame
$env:AVSP_ORACLE11_LOAD_SUPPRESS_REGION = $SuppressRegion
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT = 'global_load_release'
$env:AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND = '1'
Push-Location $projectRoot
try {
    & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
        '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
        '-nvram_directory' $runNvramRoot '-cfg_directory' $runCfgRoot `
        '-autoboot_script' '.\tools\mame_capture_oracle11_global_load_release.lua'
    if ($LASTEXITCODE -ne 0) { throw "MAME load/release capture failed: $LASTEXITCODE" }
}
finally {
    @('AVSP_ORACLE11_LOAD_ROOT','AVSP_ORACLE11_LOAD_SUPPRESS_FRAME',
      'AVSP_ORACLE11_LOAD_SUPPRESS_REGION','AVSP_ORACLE11_PLAYER_AUDIO_ROOT',
      'AVSP_ORACLE11_PLAYER_AUDIO_VARIANT','AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND') |
        ForEach-Object { Remove-Item ("Env:\" + $_) -ErrorAction SilentlyContinue }
    Pop-Location
}
$files = @('gfx_writes.tsv','route_windows.tsv','load_result.tsv','samples.tsv',
  'dispatches.tsv','projectiles.tsv','score_writes.tsv','result.tsv')
$files += 5565,5566,6200,12799 | ForEach-Object {
    $f=$_; 'gfxram0_{0:d5}.bin' -f $f; 'gfxram1_{0:d5}.bin' -f $f; 'gfxram2_{0:d5}.bin' -f $f }
$hashes = [ordered]@{}
foreach ($file in $files) { $hashes[$file]=(Get-FileHash (Join-Path $rawRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant() }
[ordered]@{schema=1; task='ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE';
  authority_family='global-gameplay-audio-load-release';
  suppression=[ordered]@{frame=$SuppressFrame;region=$SuppressRegion};
  mame_sha256=(Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant();
  nvram_baseline_sha256=(Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant();
  sha256=$hashes} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
