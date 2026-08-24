[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet(1,2)][int]$Run,[string]$EmulatorPath)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python=(Get-Command py.exe -ErrorAction Stop).Source
if (-not $EmulatorPath) {
    $candidate=Get-ChildItem -LiteralPath (Join-Path $root '.deps\emulators') -Filter yabasanshiro.exe -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like '*yabasanshiro-1.20.37-2986eb*' } | Select-Object -First 1
    if (-not $candidate) { throw 'Pinned Yaba Sanshiro 1.20.37-2986eb was not found.' }
    $EmulatorPath=$candidate.FullName
}
$emulator=(Resolve-Path -LiteralPath $EmulatorPath).Path
$prior=@(Get-Process yabasanshiro -ErrorAction SilentlyContinue | ForEach-Object Id)
& $python -3 -B (Join-Path $PSScriptRoot 'normalize_iso.py') --run $Run
if ($LASTEXITCODE -ne 0) { throw 'PROMOTE-11 ISO normalization failed.' }
& $python -3 -B (Join-Path $PSScriptRoot 'record_build.py') --run $Run
if ($LASTEXITCODE -ne 0) { throw 'PROMOTE-11 build recording failed.' }
& (Join-Path $root 'run.ps1') -EmulatorPath $emulator
$deadline=(Get-Date).AddSeconds(45); $player=$null
while ((Get-Date) -lt $deadline) {
    $player=Get-Process yabasanshiro -ErrorAction SilentlyContinue | Where-Object { $prior -notcontains $_.Id } | Sort-Object StartTime -Descending | Select-Object -First 1
    if ($player) { break }; Start-Sleep -Milliseconds 250
}
if (-not $player) { throw 'Pinned Yaba did not create a new process.' }
try {
    & $python -3 -B (Join-Path $PSScriptRoot 'collect_readback.py') --run $Run --emulator-pid $player.Id
    if ($LASTEXITCODE -ne 0) { throw 'PROMOTE-11 emulator readback failed.' }
}
finally { if (-not $player.HasExited) { Stop-Process -Id $player.Id; $player.WaitForExit(10000) } }
