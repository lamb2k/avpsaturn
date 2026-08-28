[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [ValidateSet('a', 'b', 's', 'g')]
    [string]$Variant
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mame = Join-Path $root '.deps\mame\mame0289\mame.exe'
$baseline = Join-Path $root '.deps\mame\full_route_nvram_baseline'
$captureName = "oracle11_progression_owner3_$Variant"
$out = Join-Path $root ".deps\mame\$captureName"
if (Test-Path -LiteralPath $out) {
    throw "Preserving evidence: $out"
}

New-Item -ItemType Directory -Path $out | Out-Null
$nv = Join-Path $out 'nvram'
$cfg = Join-Path $out 'cfg'
New-Item -ItemType Directory -Path $nv, $cfg | Out-Null
Copy-Item -LiteralPath $baseline -Destination (Join-Path $nv 'avspu') -Recurse

$env:AVSP_ORACLE11_PROGRESSION_ROOT = $out.Replace('\', '/')
$env:AVSP_ORACLE11_PROGRESSION_SUPPRESS_SPAWN = if ($Variant -eq 's') { '1' } else { '0' }
$env:AVSP_ORACLE11_PROGRESSION_SUPPRESS_GUARD = if ($Variant -eq 'g') { '1' } else { '0' }
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT = $out.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT = if ($Variant -eq 's') { 'mutant' } else { 'baseline' }
$env:AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND = '1'
$env:AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME = '4100'

Push-Location $root
try {
    & $mame avspu -rompath $RomRoot -video none -sound none -nothrottle `
        -skip_gameinfo -autoboot_delay 0 -nvram_directory $nv `
        -cfg_directory $cfg `
        -autoboot_script '.\tools\mame_capture_oracle11_first_segment_progression.lua'
    if ($LASTEXITCODE) {
        throw "MAME progression capture failed: $LASTEXITCODE"
    }
}
finally {
    @(
        'AVSP_ORACLE11_PROGRESSION_ROOT',
        'AVSP_ORACLE11_PROGRESSION_SUPPRESS_SPAWN',
        'AVSP_ORACLE11_PROGRESSION_SUPPRESS_GUARD',
        'AVSP_ORACLE11_PLAYER_AUDIO_ROOT',
        'AVSP_ORACLE11_PLAYER_AUDIO_VARIANT',
        'AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND',
        'AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME'
    ) | ForEach-Object {
        Remove-Item "Env:\$_" -ErrorAction SilentlyContinue
    }
    Pop-Location
}
