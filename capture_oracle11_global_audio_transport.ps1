[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_global_audio_transport_a',
    [switch]$SampleDescriptors,
    [switch]$SuppressDescriptorBank
)
$ErrorActionPreference = 'Stop'
if ($SuppressDescriptorBank -and -not $SampleDescriptors) { throw 'Descriptor control requires -SampleDescriptors' }
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
$env:AVSP_ORACLE11_GLOBAL_AUDIO_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT = $rawRoot.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT = 'baseline'
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER = ''
$env:AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT = '1'
$env:AVSP_ORACLE11_SAMPLE_DESCRIPTORS = $(if ($SampleDescriptors) { '1' } else { '' })
$env:AVSP_ORACLE11_SUPPRESS_DESCRIPTOR_BANK = $(if ($SuppressDescriptorBank) { '1' } else { '' })
$env:AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME = $(if ($SampleDescriptors) { '15193' } else { '18000' })
Push-Location $projectRoot
try {
    & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' `
        '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
        '-nvram_directory' $runNvramRoot '-cfg_directory' $runCfgRoot `
        '-autoboot_script' '.\tools\mame_capture_oracle11_global_audio_transport.lua'
    if ($LASTEXITCODE -ne 0) { throw "MAME global-audio capture failed: $LASTEXITCODE" }
}
finally {
    @('AVSP_ORACLE11_GLOBAL_AUDIO_ROOT','AVSP_ORACLE11_PLAYER_AUDIO_ROOT',
      'AVSP_ORACLE11_PLAYER_AUDIO_VARIANT','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION','AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER',
      'AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT','AVSP_ORACLE11_SAMPLE_DESCRIPTORS',
      'AVSP_ORACLE11_SUPPRESS_DESCRIPTOR_BANK','AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME') | ForEach-Object {
        Remove-Item ("Env:\" + $_) -ErrorAction SilentlyContinue
    }
    Pop-Location
}
$files = @('samples.tsv','dispatches.tsv','qsound.tsv','projectiles.tsv',
  'score_writes.tsv','result.tsv','audio_shared_reads.tsv','audio_bus_writers.tsv',
  'audio_queue_reads.tsv','audio_state_writers.tsv','audio_shared_commands.tsv',
  'audio_command_dispatches.tsv')
if ($SampleDescriptors) { $files += 'audio_sample_descriptors.tsv' }
$manifest = [ordered]@{
    schema = 1
    task = 'ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE'
    authority_family = 'global-gameplay-audio-load-release'
    variant = 'baseline'
    frame_window = @(1972, $(if ($SampleDescriptors) { 15193 } else { 18000 }))
    sample_descriptor_capture = [bool]$SampleDescriptors
    sample_descriptor_bank_control = [bool]$SuppressDescriptorBank
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    audio_rom_sha256 = (Get-FileHash (Join-Path $RomRoot 'avspu\avp.01') -Algorithm SHA256).Hash.ToLowerInvariant()
    nvram_baseline_sha256 = (Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    sha256 = [ordered]@{}
}
foreach ($file in $files) {
    $manifest.sha256[$file] = (Get-FileHash (Join-Path $rawRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
