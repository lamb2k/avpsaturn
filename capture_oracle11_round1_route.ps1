[CmdletBinding()]
param([string]$RomRoot='C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest',
 [Parameter(Mandatory=$true)][string]$CaptureName)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$mame=Join-Path $root '.deps\mame\mame0289\mame.exe'
$out=Join-Path $root ('.deps\mame\'+$CaptureName)
$baseline=Join-Path $root '.deps\mame\full_route_nvram_baseline'
if(Test-Path -LiteralPath $out){throw "Preserving evidence: $out"}
New-Item -ItemType Directory $out|Out-Null
$nv=Join-Path $out nvram;$cfg=Join-Path $out cfg
New-Item -ItemType Directory $nv,$cfg|Out-Null
Copy-Item $baseline (Join-Path $nv avspu) -Recurse
$env:AVSP_ORACLE11_ROUTE_ROOT=$out.Replace('\','/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_ROOT=$out.Replace('\','/')
$env:AVSP_ORACLE11_PLAYER_AUDIO_VARIANT='round1_route_baseline'
$env:AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND='1'
Push-Location $root
try{
 &$mame avspu -rompath $RomRoot -video none -sound none -nothrottle -skip_gameinfo -autoboot_delay 0 -nvram_directory $nv -cfg_directory $cfg -autoboot_script '.\tools\mame_capture_oracle11_round1_route.lua'
 if($LASTEXITCODE){throw "MAME route capture failed: $LASTEXITCODE"}
}finally{
 @('AVSP_ORACLE11_ROUTE_ROOT','AVSP_ORACLE11_PLAYER_AUDIO_ROOT','AVSP_ORACLE11_PLAYER_AUDIO_VARIANT','AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND')|ForEach-Object{Remove-Item ('Env:\'+$_) -ErrorAction SilentlyContinue}
 Pop-Location
}
$files='route_samples.tsv','route_writes.tsv','route_writer_summary.tsv','lifecycle_writes.tsv','route_rng.tsv','samples.tsv','dispatches.tsv','projectiles.tsv','score_writes.tsv','result.tsv'
$hash=[ordered]@{}
foreach($f in $files){$hash[$f]=(Get-FileHash (Join-Path $out $f) -Algorithm SHA256).Hash.ToLowerInvariant()}
[ordered]@{schema=1;task='ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE';authority_family='encounters-waves-scripted-triggers';variant='baseline';mame_sha256=(Get-FileHash $mame -Algorithm SHA256).Hash.ToLowerInvariant();nvram_baseline_sha256=(Get-FileHash (Join-Path $baseline eeprom) -Algorithm SHA256).Hash.ToLowerInvariant();sha256=$hash}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $out input_manifest.json) -Encoding utf8
