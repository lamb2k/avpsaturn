[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(1, 2)]
    [int]$Run,
    [string]$EmulatorPath,
    [switch]$Release
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$python = Get-Command py.exe -ErrorAction Stop
if (-not $EmulatorPath) {
    $candidate = Get-ChildItem -LiteralPath (Join-Path $root '.deps\emulators') `
        -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like '*yabasanshiro-1.20.37-2986eb*' } |
        Select-Object -First 1
    if (-not $candidate) { throw 'Pinned Yaba Sanshiro 1.20.37-2986eb was not found.' }
    $EmulatorPath = $candidate.FullName
}
$emulator = (Resolve-Path -LiteralPath $EmulatorPath).Path
& $python.Source -3 -B (Join-Path $PSScriptRoot 'normalize_iso.py') --run $Run
if ($LASTEXITCODE -ne 0) { throw 'Playable-slice ISO normalization failed.' }
$recordArguments = @('-3', '-B', (Join-Path $PSScriptRoot 'record_build.py'),
    '--run', $Run)
if ($Release) { $recordArguments += '--release' }
& $python.Source @recordArguments
if ($LASTEXITCODE -ne 0) { throw 'Playable-slice build recording failed.' }
$runRoot = Join-Path $root "build\port_v2\integration\slice\run-$Run"
foreach ($name in @('hit-checkpoint.json', 'ko-checkpoint.json',
        'final-checkpoint.json', 'readback.json', 'hit.png', 'ko.png',
        'scene-trace.json', 'scene-after.gif')) {
    $path = Join-Path $runRoot $name
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
}
Get-ChildItem -LiteralPath $runRoot -Filter 'scene-*.png' -File `
    -ErrorAction SilentlyContinue | Remove-Item -Force
foreach ($checkpoint in @('hit', 'ko', 'final')) {
    $priorIds = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Id })
    & (Join-Path $root 'run.ps1') -EmulatorPath $emulator
    if ($LASTEXITCODE -ne 0) { throw 'Pinned Yaba launch failed.' }
    $deadline = (Get-Date).AddSeconds(45)
    $player = $null
    while ((Get-Date) -lt $deadline) {
        $player = Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
            Where-Object { $priorIds -notcontains $_.Id } |
            Sort-Object StartTime -Descending | Select-Object -First 1
        if ($player) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $player) { throw 'Pinned Yaba did not create a new process.' }
    try {
        & $python.Source -3 -B (Join-Path $PSScriptRoot 'collect_readback.py') `
            --run $Run --checkpoint $checkpoint --emulator-pid $player.Id
        if ($LASTEXITCODE -ne 0) {
            throw "Playable-slice $checkpoint emulator readback failed."
        }
    }
    finally {
        if (-not $player.HasExited) {
            Stop-Process -Id $player.Id
            $player.WaitForExit(10000)
        }
    }
}

$priorIds = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Id })
& (Join-Path $root 'run.ps1') -EmulatorPath $emulator
if ($LASTEXITCODE -ne 0) { throw 'Pinned Yaba scene-trace launch failed.' }
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
    $traceArguments = @('-3', '-B',
        (Join-Path $PSScriptRoot 'collect_scene_trace.py'),
        '--run', $Run, '--emulator-pid', $player.Id)
    if ($Run -eq 2) { $traceArguments += '--no-clip' }
    & $python.Source @traceArguments
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
