[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [ValidateSet('a', 'b', 's', 's2', 't1a', 't1b', 't1s', 't2a', 't2b', 't2s', 'csa', 'csb', 'css', 'cs2a', 'cs2b', 'cs2s', 'cs3a', 'cs3b', 'cs3s', 'cs4a', 'cs4b', 'cs4s', 'cs5a', 'cs5b', 'cs5s', 'cs6a', 'cs6b', 'cs6s', 'cs7a', 'cs7b', 'cs7s', 'cs8a', 'cs8b', 'cs9a', 'cs9b', 'cs10a', 'cs10b', 'cs10s', 'cs11a', 'cs11b', 'cs12a', 'cs12b', 'cs13a', 'cs13b', 'cs14a', 'cs14b', 'cs15a', 'cs15b', 'cs15s3', 'cs15s4', 'cs15s4all', 'cs15s5', 'cs15se', 'cs16a', 'cs17a', 'cs17b', 'cs17s201', 'cs17s202', 'cs17s20f', 'cs17s245', 'cs17s24a', 'cs17s2420', 'cs17s280', 'cs17s28c', 'cs17s28e', 'cs18a', 'cs18b', 'cs18s', 'cs19a', 'cs19b', 'cs19s', 'cs20a', 'cs20b', 'cs20s', 'cs21a', 'cs21b', 'cs21s', 'cs22a', 'cs22b', 'cs23a', 'cs23b', 'cs24a', 'cs24b', 'cs25a', 'cs25b', 'cs26a', 'cs26b', 'cs27a', 'cs27b', 'cs30a', 'cs30b', 'cs30s', 'cs31a', 'cs31b', 'cs32a', 'cs32b', 'cs32s', 'cs33a', 'cs33b', 'cs33c', 'cs33d', 'cs33e', 'cs33f', 'cs33m', 'cs33m2', 'cs33m3', 'cs34a', 'cs34b', 'cs34c', 'cs34d', 'cs34m', 'cs34m2', 'cs35a', 'cs35b', 'cs35m', 'cs36a', 'cs36b', 'cs36m', 'cs36m2', 'cs36m3', 'cs36m4', 'cs37a', 'cs38a', 'cs38b', 'cs38s', 'cs39a', 'cs39b', 'cs40a', 'cs40b', 'cs41a', 'cs41b', 'cs42a', 'cs42b', 'cs43a', 'cs43b', 'cs44a', 'cs44b', 'cs45a', 'cs45b', 'cs46a', 'cs46b', 'cs47a', 'cs47b', 'cs47m', 'cs48a', 'cs48b', 'cs48m', 'cs49a', 'cs49b', 'cs49m', 'cs50a', 'cs50b', 'cs50m', 'cs51a', 'cs51b', 'cs51m', 'cs52a', 'cs52b', 'cs52m', 'cs53a', 'cs53b', 'cs53m', 'cs54a', 'cs54b', 'cs54m', 'cs55a', 'cs55b', 'cs55m', 'cs56a', 'cs56b', 'cs56m', 'cs57a', 'cs57b', 'cs57m', 'cs58a', 'cs58b', 'cs58m', 'cs59a', 'cs59b', 'cs60a', 'cs60b', 'cs61a', 'cs61b', 'cs61m1', 'cs61m2', 'cs65a', 'cs65a2', 'cs65a3', 'cs65a4', 'cs65b', 'cs65b2', 'cs65b3', 'cs65m1', 'cs65m2', 'cs65m3', 'cs65m4', 'cs65m5', 'cs65m6', 'cs66a', 'cs66b', 'cs67a', 'cs67b', 'cs68a', 'cs68b', 'cs69a', 'cs69b', 'cs69m', 'cs16b')]
    [string]$Variant,
    [string]$TransitionWriter = '',
    [string]$CaptureNameOverride = '',
    [switch]$Class0aCounterfactual,
    [switch]$Class00InitCounterfactual,
    [switch]$Class0cContactCounterfactual
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mame = Join-Path $root '.deps\mame\mame0289\mame.exe'
$baseline = Join-Path $root '.deps\mame\full_route_nvram_baseline'
$captureName = if ($CaptureNameOverride) {
    $CaptureNameOverride
}
else {
    "oracle11_progression_lifecycle_$Variant"
}
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
$env:AVSP_ORACLE11_COMPONENT20_PHASE_CAPTURE = if ($Variant -match '^cs4[2345]') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS0F_STATE_COUNTERFACTUAL = if ($Variant -match '^cs61m') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS0A_VARIANT_COUNTERFACTUAL = if ($Class0aCounterfactual) { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS00_INIT_COUNTERFACTUAL = if ($Class00InitCounterfactual) { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS0C_PROGRAM_CAPTURE = if ($Variant -match '^cs69') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS0C_CONTACT_COUNTERFACTUAL = if ($Class0cContactCounterfactual) { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_ACTION4_GUARD_CAPTURE = if ($Variant -match '^cs46') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_INNER8_GROUP_CAPTURE = if ($Variant -match '^cs(4[789]|50)') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_INNER8_GROUP_MUTATE = if ($Variant -in @('cs47m', 'cs48m', 'cs49m', 'cs50m')) { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_ACTION0C_CAPTURE = if ($Variant -match '^cs5[12]') { '1' } else { '0' }
$env:AVSP_ORACLE11_CLASS1F_ACTION0C_MUTATE = if ($Variant -in @('cs51m', 'cs52m')) { '1' } else { '0' }
$env:AVSP_ORACLE11_PLAYER_HIT_CAPTURE = if ($Variant -match '^cs53') { '1' } else { '0' }
$env:AVSP_ORACLE11_PLAYER_HIT_MUTATE_BODY = if ($Variant -in @('cs53m', 'cs53m2')) { '1' } else { '0' }
$env:AVSP_ORACLE11_TERRAIN_PATCH_CAPTURE = if ($Variant -match '^cs(5[4-9]|60)') { '1' } else { '0' }
$env:AVSP_ORACLE11_TERRAIN_STREAM_CAPTURE = if ($Variant -match '^cs(5[6-9]|60)') { '1' } else { '0' }
$env:AVSP_ORACLE11_TERRAIN_STREAM_BACKTRACK = if ($Variant -match '^cs(59|60)') { '1' } else { '0' }
$env:AVSP_ORACLE11_TERRAIN_STREAM_FORCE_BACKTRACK = if ($Variant -match '^cs60') { '1' } else { '0' }
$env:AVSP_ORACLE11_TERRAIN_PATCH_MUTATE = if ($Variant -in @('cs54m', 'cs55m', 'cs56m', 'cs57m', 'cs58m')) { '1' } else { '0' }
$env:AVSP_ORACLE11_TERRAIN_PATCH_MUTATION_PC = if ($Variant -in @('cs54m', 'cs55m', 'cs56m', 'cs57m', 'cs58m')) { $TransitionWriter } else { '' }
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
        'AVSP_ORACLE11_COMPONENT20_PHASE_CAPTURE',
        'AVSP_ORACLE11_CLASS0F_STATE_COUNTERFACTUAL',
        'AVSP_ORACLE11_CLASS0A_VARIANT_COUNTERFACTUAL',
        'AVSP_ORACLE11_CLASS00_INIT_COUNTERFACTUAL',
        'AVSP_ORACLE11_CLASS0C_PROGRAM_CAPTURE',
        'AVSP_ORACLE11_CLASS0C_CONTACT_COUNTERFACTUAL',
        'AVSP_ORACLE11_CLASS1F_ACTION4_GUARD_CAPTURE',
        'AVSP_ORACLE11_CLASS1F_INNER8_GROUP_CAPTURE',
        'AVSP_ORACLE11_CLASS1F_INNER8_GROUP_MUTATE',
        'AVSP_ORACLE11_CLASS1F_ACTION0C_CAPTURE',
        'AVSP_ORACLE11_CLASS1F_ACTION0C_MUTATE',
        'AVSP_ORACLE11_PLAYER_HIT_CAPTURE',
        'AVSP_ORACLE11_PLAYER_HIT_MUTATE_BODY',
        'AVSP_ORACLE11_TERRAIN_PATCH_CAPTURE',
        'AVSP_ORACLE11_TERRAIN_STREAM_CAPTURE',
        'AVSP_ORACLE11_TERRAIN_STREAM_BACKTRACK',
        'AVSP_ORACLE11_TERRAIN_STREAM_FORCE_BACKTRACK',
        'AVSP_ORACLE11_TERRAIN_PATCH_MUTATE',
        'AVSP_ORACLE11_TERRAIN_PATCH_MUTATION_PC',
        'AVSP_ORACLE11_PLAYER_AUDIO_ROOT',
        'AVSP_ORACLE11_PLAYER_AUDIO_VARIANT',
        'AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND',
        'AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME'
    ) | ForEach-Object {
        Remove-Item "Env:\$_" -ErrorAction SilentlyContinue
    }
    Pop-Location
}
