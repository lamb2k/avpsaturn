[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [Parameter(Mandatory = $true)][string]$CaptureName,
    [Parameter(Mandatory = $true)][string]$SuppressA6,
    [Parameter(Mandatory = $true)][string]$SuppressReturn0,
    [Parameter(Mandatory = $true)][string]$SuppressCommand,
    [int]$LastFrame = 18000
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot ('.deps\mame\' + $CaptureName)
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
foreach ($required in @($mame, $baseline, (Join-Path $RomRoot 'avspu'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing private source input: $required" }
}
if (Test-Path -LiteralPath $rawRoot) { throw "Preserving raw evidence; choose a new CaptureName: $rawRoot" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null
$runNvramRoot = Join-Path $rawRoot 'nvram'
$runCfgRoot = Join-Path $rawRoot 'cfg'
New-Item -ItemType Directory -Path $runNvramRoot, $runCfgRoot | Out-Null
Copy-Item -LiteralPath $baseline -Destination (Join-Path $runNvramRoot 'avspu') -Recurse
$env:AVSP_ORACLE11_GLOBAL_AUDIO_MUTATION_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT = 'global_trigger_suppression'
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND = [string][Convert]::ToInt32($SuppressCommand, 16)
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_A6 = [string][Convert]::ToInt32($SuppressA6, 16)
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_RETURN0 = [string][Convert]::ToInt32($SuppressReturn0, 16)
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT = '1'
$env:AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND = '1'
$env:AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME = [string]$LastFrame
Push-Location $projectRoot
try {
    & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
        '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
        '-nvram_directory' $runNvramRoot '-cfg_directory' $runCfgRoot `
        '-autoboot_script' '.\tools\mame_capture_oracle11_global_audio_mutation.lua'
    if ($LASTEXITCODE -ne 0) { throw "MAME global-audio mutation failed: $LASTEXITCODE" }
}
finally {
    @('AVSP_ORACLE11_GLOBAL_AUDIO_MUTATION_ROOT','AVSP_ORACLE11_PLAYER_AUDIO_ROOT',
      'AVSP_ORACLE11_PLAYER_AUDIO_VARIANT','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_A6','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_RETURN0',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT','AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND',
      'AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME') |
      ForEach-Object { Remove-Item ("Env:\" + $_) -ErrorAction SilentlyContinue }
    Pop-Location
}
$files = @('samples.tsv','dispatches.tsv','projectiles.tsv','score_writes.tsv',
  'result.tsv','audio_bus_stream.bin')
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'global-gameplay-audio-load-release'
    variant = 'global_trigger_suppression'
    selector = [ordered]@{a6=$SuppressA6;return0=$SuppressReturn0;command=$SuppressCommand}
    frame_window = @(1972, $LastFrame)
    mame_sha256 = (Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    nvram_baseline_sha256 = (Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    sha256 = [ordered]@{}
}
foreach ($file in $files) {
    $manifest.sha256[$file] = (Get-FileHash (Join-Path $rawRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
