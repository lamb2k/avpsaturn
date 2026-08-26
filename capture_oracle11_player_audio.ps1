[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_audio_a',
    [string]$Variant = 'baseline',
    [string]$SuppressCaller = '',
    [string]$SuppressCommand = '',
    [string]$SuppressState = '',
    [string]$SuppressAction = '',
    [string]$SuppressInner = '',
    [int]$SuppressLimit = 1,
    [switch]$CompactQsound
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
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }
New-Item -ItemType Directory -Path $rawRoot | Out-Null
$runNvramRoot = Join-Path $rawRoot 'nvram'
$runCfgRoot = Join-Path $rawRoot 'cfg'
New-Item -ItemType Directory -Path $runNvramRoot, $runCfgRoot | Out-Null
Copy-Item -LiteralPath $baseline -Destination (Join-Path $runNvramRoot 'avspu') -Recurse
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT = $Variant
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER = $SuppressCaller
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND = $SuppressCommand
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE = $SuppressState
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION = $SuppressAction
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER = $SuppressInner
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT = [string]$SuppressLimit
$env:AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND = if ($CompactQsound) { '1' } else { '' }
Push-Location $projectRoot
try {
    & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
        '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
        '-nvram_directory' $runNvramRoot '-cfg_directory' $runCfgRoot `
        '-autoboot_script' '.\tools\mame_capture_oracle11_player_audio.lua'
    if ($LASTEXITCODE -ne 0) { throw "MAME player-audio capture failed: $LASTEXITCODE" }
}
finally {
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_ROOT -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_VARIANT -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT -ErrorAction SilentlyContinue
    Remove-Item Env:\AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND -ErrorAction SilentlyContinue
    Pop-Location
}
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'predator-warrior-player-origin-gameplay-audio'
    variant = $Variant
    frame_window = @(1972, 18000)
    mutation = [ordered]@{
        caller = $SuppressCaller; command = $SuppressCommand; state = $SuppressState
        action = $SuppressAction; inner = $SuppressInner
    }
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    sha256 = [ordered]@{}
}
foreach ($file in @('samples.tsv','dispatches.tsv','qsound.tsv','projectiles.tsv','score_writes.tsv','result.tsv')) {
    $manifest.sha256[$file] = (Get-FileHash (Join-Path $rawRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
