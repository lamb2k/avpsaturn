[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(1, 2)]
    [int]$Run,
    [string]$EmulatorPath,
    [switch]$NoClip
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$python = Get-Command py.exe -ErrorAction Stop
if (-not $EmulatorPath) {
    $candidate = Get-ChildItem -LiteralPath (Join-Path $root '.deps\emulators') `
        -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like '*yabasanshiro-1.20.37-2986eb*' } |
        Select-Object -First 1
    if (-not $candidate) {
        throw 'Pinned Yaba Sanshiro 1.20.37-2986eb was not found.'
    }
    $EmulatorPath = $candidate.FullName
}
$emulator = (Resolve-Path -LiteralPath $EmulatorPath).Path
$priorIds = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Id })
& (Join-Path $root 'run.ps1') -EmulatorPath $emulator
if (-not $?) { throw 'Pinned Yaba scene-trace launch failed.' }
$deadline = (Get-Date).AddSeconds(45)
$player = $null
while ((Get-Date) -lt $deadline) {
    $player = Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
        Where-Object { $priorIds -notcontains $_.Id } |
        Sort-Object StartTime -Descending | Select-Object -First 1
    if ($player) { break }
    Start-Sleep -Milliseconds 250
}
if (-not $player) { throw 'Pinned Yaba did not create a scene-trace process.' }
try {
    $arguments = @('-3', '-B',
        (Join-Path $PSScriptRoot 'collect_scene_trace.py'),
        '--run', $Run, '--emulator-pid', $player.Id)
    if ($NoClip) { $arguments += '--no-clip' }
    & $python.Source @arguments
    if ($LASTEXITCODE -ne 0) {
        throw 'Playable-slice synchronized scene trace failed.'
    }
}
finally {
    if (-not $player.HasExited) {
        Stop-Process -Id $player.Id
        $player.WaitForExit(10000)
    }
}
