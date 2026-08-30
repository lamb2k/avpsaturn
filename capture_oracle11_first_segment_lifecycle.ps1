[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [ValidateSet('a', 'b', 's', 's2', 't1a', 't1b', 't1s', 't2a', 't2b', 't2s', 'csa', 'csb', 'css', 'cs2a', 'cs2b', 'cs2s', 'cs3a', 'cs3b', 'cs3s', 'cs4a', 'cs4b', 'cs4s', 'cs5a', 'cs5b', 'cs5s', 'cs6a', 'cs6b', 'cs6s', 'cs7a', 'cs7b', 'cs7s', 'cs8a', 'cs8b', 'cs9a', 'cs9b', 'cs10a', 'cs10b', 'cs10s', 'cs11a', 'cs11b', 'cs12a', 'cs12b', 'cs13a', 'cs13b', 'cs14a', 'cs14b', 'cs15a', 'cs15b', 'cs15s3', 'cs15s4', 'cs15s4all', 'cs15s5', 'cs15se', 'cs16a', 'cs16b', 'cs17a', 'cs17b', 'cs17s201', 'cs17s202', 'cs17s20f', 'cs17s245', 'cs17s24a', 'cs17s2420', 'cs17s280', 'cs17s28c', 'cs17s28e', 'cs18a', 'cs18b', 'cs18s', 'cs19a', 'cs19b', 'cs19s', 'cs20a', 'cs20b', 'cs20s', 'cs21a', 'cs21b', 'cs21s', 'cs22a', 'cs22b', 'cs23a', 'cs23b', 'cs24a', 'cs24b', 'cs25a', 'cs25b', 'cs26a', 'cs26b', 'cs27a', 'cs27b', 'cs30a', 'cs30b', 'cs30s', 'cs31a', 'cs31b', 'cs32a', 'cs32b', 'cs32s', 'cs33a', 'cs33b', 'cs33c', 'cs33d', 'cs33e', 'cs33f', 'cs33m', 'cs33m2', 'cs33m3', 'cs34a', 'cs34b', 'cs34c', 'cs34d', 'cs34m', 'cs34m2', 'cs35a', 'cs35b', 'cs35m', 'cs36a', 'cs36b', 'cs36m', 'cs36m2', 'cs36m3', 'cs36m4', 'cs37a', 'cs38a', 'cs38b', 'cs38s')]
    [string]$Variant,
    [string]$TransitionWriter = ''
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mame = Join-Path $root '.deps\mame\mame0289\mame.exe'
$baseline = Join-Path $root '.deps\mame\full_route_nvram_baseline'
$captureName = "oracle11_progression_lifecycle_$Variant"
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
$env:AVSP_ORACLE11_PROGRESSION_SUPPRESS_SPAWN = '0'
$env:AVSP_ORACLE11_PROGRESSION_SUPPRESS_GUARD = '0'
$env:AVSP_ORACLE11_PROGRESSION_LIFECYCLE = '1'
$env:AVSP_ORACLE11_PROGRESSION_SUPPRESS_LIFECYCLE = if ($Variant -in @('s', 's2')) { '1' } else { '0' }
$env:AVSP_ORACLE11_PROGRESSION_SUPPRESS_TRANSITION_PC = if ($Variant -in @('t1s', 't2s', 'cs30s')) { $TransitionWriter } else { '' }
$env:AVSP_ORACLE11_COFFEE_SHOP_SCENE = if ($Variant -match '^cs') { '1' } else { '0' }
$env:AVSP_ORACLE11_SUPPRESS_ACTION4_TIMER = if ($Variant -in @('css', 'cs2s', 'cs3s', 'cs4s', 'cs5s', 'cs6s')) { '1' } else { '0' }
$env:AVSP_ORACLE11_SUPPRESS_TYPE4_CLASS03_PC = if ($Variant -eq 'cs7s') { $TransitionWriter } else { '' }
$env:AVSP_ORACLE11_SUPPRESS_COFFEE_STAGE_RNG = if ($Variant -eq 'cs10s') { '1' } else { '0' }
$env:AVSP_ORACLE11_SUPPRESS_TYPE36_PC = if ($Variant -match '^cs15s') { $TransitionWriter } else { '' }
$env:AVSP_ORACLE11_SUPPRESS_TYPE36_PC2 = if ($Variant -eq 'cs15s4all') { '023946' } else { '' }
$env:AVSP_ORACLE11_SUPPRESS_TYPE36_CLASS = switch ($Variant) {
    'cs15s3' { '03' }
    { $_ -in 'cs15s4','cs15s4all' } { '04' }
    'cs15s5' { '05' }
    'cs15se' { '0e' }
    default { '' }
}
$env:AVSP_ORACLE11_SUPPRESS_SCENE_PAIR_TYPE = switch -Regex ($Variant) {
    '^cs17s20' { '20' }
    '^cs17s24' { '24' }
    '^cs17s28' { '28' }
    default { '' }
}
$env:AVSP_ORACLE11_SUPPRESS_SCENE_PAIR_CLASS = switch ($Variant) {
    'cs17s201' { '01' }
    'cs17s202' { '02' }
    'cs17s20f' { '0f' }
    'cs17s245' { '05' }
    'cs17s24a' { '0a' }
    'cs17s2420' { '20' }
    'cs17s280' { '00' }
    'cs17s28c' { '0c' }
    'cs17s28e' { '0e' }
    default { '' }
}
$env:AVSP_ORACLE11_SUPPRESS_OBSTACLE_TRANSITION = if ($Variant -in @('cs19s', 'cs20s', 'cs21s')) { '1' } else { '0' }
$env:AVSP_ORACLE11_COLLISION_GUARD_CAPTURE = if ($Variant -match '^cs32') { '1' } else { '0' }
$env:AVSP_ORACLE11_COLLISION_GUARD_MUTATE = if ($Variant -eq 'cs32s') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_HIT_CAPTURE = if ($Variant -match '^cs3[3456]') { '1' } else { '0' }
$env:AVSP_ORACLE11_MUTATE_CLASS1F_HIT_SELECTOR = if ($Variant -in @('cs33m', 'cs33m2', 'cs33m3', 'cs34m', 'cs34m2', 'cs35m', 'cs36m', 'cs36m2', 'cs36m3', 'cs36m4')) { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_HIT_SLOT = if ($Variant -match '^cs36') { 'ffa3c0' } else { 'ffa180' }
$env:AVSP_ORACLE11_CLASS1F_HIT_FIRST_FRAME = if ($Variant -match '^cs36') { '2358' } else { '2304' }
$env:AVSP_ORACLE11_CLASS1F_HIT_LAST_FRAME = if ($Variant -match '^cs36') { '2510' } else { '2450' }
$env:AVSP_ORACLE11_CLASS1F_HIT_SELECTOR_ENTRY = '1fd3c'
$env:AVSP_ORACLE11_CONTROLLER_SUBSTATE_CAPTURE = if ($Variant -match '^cs38') { '1' } else { '0' }
$env:AVSP_ORACLE11_SUPPRESS_CONTROLLER_SUBSTATE_PC = if ($Variant -eq 'cs38s') { $TransitionWriter } else { '' }
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT = $out.Replace('\', '/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT = 'baseline'
$env:AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND = '1'
$env:AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME = if ($Variant -match '^cs') { '5566' } else { '4100' }

Push-Location $root
try {
    & $mame avspu -rompath $RomRoot -video none -sound none -nothrottle `
        -skip_gameinfo -autoboot_delay 0 -nvram_directory $nv `
        -cfg_directory $cfg `
        -autoboot_script '.\tools\mame_capture_oracle11_first_segment_progression.lua'
    if ($LASTEXITCODE) {
        throw "MAME progression lifecycle capture failed: $LASTEXITCODE"
    }
}
finally {
    @(
        'AVSP_ORACLE11_PROGRESSION_ROOT',
        'AVSP_ORACLE11_PROGRESSION_SUPPRESS_SPAWN',
        'AVSP_ORACLE11_PROGRESSION_SUPPRESS_GUARD',
        'AVSP_ORACLE11_PROGRESSION_LIFECYCLE',
        'AVSP_ORACLE11_PROGRESSION_SUPPRESS_LIFECYCLE',
        'AVSP_ORACLE11_PROGRESSION_SUPPRESS_TRANSITION_PC',
        'AVSP_ORACLE11_COFFEE_SHOP_SCENE',
        'AVSP_ORACLE11_SUPPRESS_ACTION4_TIMER',
        'AVSP_ORACLE11_SUPPRESS_TYPE4_CLASS03_PC',
        'AVSP_ORACLE11_SUPPRESS_COFFEE_STAGE_RNG',
        'AVSP_ORACLE11_SUPPRESS_TYPE36_PC',
        'AVSP_ORACLE11_SUPPRESS_TYPE36_PC2',
        'AVSP_ORACLE11_SUPPRESS_TYPE36_CLASS',
        'AVSP_ORACLE11_SUPPRESS_SCENE_PAIR_TYPE',
        'AVSP_ORACLE11_SUPPRESS_SCENE_PAIR_CLASS',
        'AVSP_ORACLE11_SUPPRESS_OBSTACLE_TRANSITION',
        'AVSP_ORACLE11_COLLISION_GUARD_CAPTURE',
        'AVSP_ORACLE11_COLLISION_GUARD_MUTATE',
        'AVSP_ORACLE11_CLASS1F_HIT_CAPTURE',
        'AVSP_ORACLE11_MUTATE_CLASS1F_HIT_SELECTOR',
        'AVSP_ORACLE11_CLASS1F_HIT_SLOT',
        'AVSP_ORACLE11_CLASS1F_HIT_FIRST_FRAME',
        'AVSP_ORACLE11_CLASS1F_HIT_LAST_FRAME',
        'AVSP_ORACLE11_CLASS1F_HIT_SELECTOR_ENTRY',
        'AVSP_ORACLE11_CONTROLLER_SUBSTATE_CAPTURE',
        'AVSP_ORACLE11_SUPPRESS_CONTROLLER_SUBSTATE_PC',
        'AVSP_ORACLE11_PLAYER_AUDIO_ROOT',
        'AVSP_ORACLE11_PLAYER_AUDIO_VARIANT',
        'AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND',
        'AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME'
    ) | ForEach-Object {
        Remove-Item "Env:\$_" -ErrorAction SilentlyContinue
    }
    Pop-Location
}
