[CmdletBinding()]
param(
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
    [string]$CaptureName = 'oracle11_player_weapon_a',
    [ValidateSet('legacy','predator_warrior')]
    [string]$CharacterRoute = 'legacy',
    [string[]]$Variants = @('cold_run_1','cold_run_2','resource_empty','b1_held',
        'repeat_startup','repeat_active','repeat_recovery','special_ok','special_low_health',
        'special_zero_health','target_inside','target_outside','allocation_unavailable',
        'target_removed','lifetime_writer_suppressed','recharge_writer_frozen',
        'pickup_actor_removed','projectile_class_removed','facing_reversed')
)
$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$mame=Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot=Join-Path $projectRoot ('.deps\mame\'+$CaptureName)
$baseline=Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram=Join-Path $projectRoot 'nvram\avspu'
$cfgDir=Join-Path $projectRoot 'cfg'
foreach($required in @($mame,$baseline,(Join-Path $RomRoot 'avspu'))){if(-not(Test-Path -LiteralPath $required)){throw "Missing private ORACLE-11 input: $required"}}
if(Test-Path -LiteralPath $rawRoot){throw "Preserving existing raw evidence; choose a new CaptureName: $rawRoot"}
& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'; if($LASTEXITCODE -ne 0){throw "avspu verification failed"}
New-Item -ItemType Directory -Path $rawRoot|Out-Null
$manifest=[ordered]@{schema=1;task='ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE';authority_family='predator-warrior-weapon-projectile-resource';character_route=$CharacterRoute;frame_window=@(4380,4760);declared_counterfactuals=$Variants[2..($Variants.Count-1)];mame=[ordered]@{version=(& $mame -version).Trim();sha256=(Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant()};nvram_baseline_sha256=(Get-FileHash (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant();variants=@()}
foreach($name in $Variants){
 $runRoot=Join-Path $rawRoot $name;New-Item -ItemType Directory -Path $runRoot|Out-Null
 if(Test-Path -LiteralPath $liveNvram){Remove-Item -LiteralPath $liveNvram -Recurse -Force};Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
 foreach($stale in @((Join-Path $cfgDir 'avspu.cfg'),(Join-Path $cfgDir 'default.cfg'))){if(Test-Path -LiteralPath $stale){Remove-Item -LiteralPath $stale -Force}}
 $mode=if($name -like 'cold_run_*'){'baseline'}else{$name};$env:AVSP_ORACLE11_WEAPON_ROOT=$runRoot.Replace('\','/');$env:AVSP_ORACLE11_WEAPON_VARIANT=$mode;$env:AVSP_ORACLE11_WEAPON_CHARACTER_ROUTE=$CharacterRoute
 if($name -eq 'cold_run_1'){$env:AVSP_ORACLE11_WEAPON_PRESENTATION_PROBE_FRAME=if($CharacterRoute -eq 'predator_warrior'){'4428'}else{'4498'}}
 Push-Location $projectRoot;try{& $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' '-autoboot_script' '.\tools\mame_capture_oracle11_player_weapon.lua';if($LASTEXITCODE -ne 0){throw "MAME $name failed"}}finally{Remove-Item Env:\AVSP_ORACLE11_WEAPON_ROOT -ErrorAction SilentlyContinue;Remove-Item Env:\AVSP_ORACLE11_WEAPON_VARIANT -ErrorAction SilentlyContinue;Remove-Item Env:\AVSP_ORACLE11_WEAPON_CHARACTER_ROUTE -ErrorAction SilentlyContinue;Remove-Item Env:\AVSP_ORACLE11_WEAPON_PRESENTATION_PROBE_FRAME -ErrorAction SilentlyContinue;Pop-Location}
 $hashes=[ordered]@{};foreach($file in @('samples.tsv','writes.tsv','actors.tsv','qsound.tsv','damage.tsv','impact_audio.tsv','objects.tsv','character_samples.tsv')){if(Test-Path -LiteralPath (Join-Path $runRoot $file)){$hashes[$file]=(Get-FileHash (Join-Path $runRoot $file) -Algorithm SHA256).Hash.ToLowerInvariant()}};$manifest.variants += [ordered]@{name=$name;mode=$mode;sha256=$hashes}
}
$manifest|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8
