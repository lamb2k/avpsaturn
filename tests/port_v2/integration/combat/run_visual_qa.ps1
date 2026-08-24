[CmdletBinding()]
param(
    [ValidateSet(1, 2)]
    [int]$VisualRun = 1,
    [string]$EmulatorPath
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
$paired = Get-Content -LiteralPath (Join-Path $root `
    'build\port_v2\integration\combat\run-1\readback.json') -Raw |
    ConvertFrom-Json
$isoHash = (Get-FileHash -LiteralPath (Join-Path $root 'game.iso') `
    -Algorithm SHA256).Hash.ToLowerInvariant()
if ($isoHash -ne $paired.iso_sha256) {
    throw 'Visual-QA ISO does not match the paired passing emulator evidence.'
}
$priorIds = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Id })
& (Join-Path $root 'run.ps1') -EmulatorPath (Resolve-Path $EmulatorPath).Path
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
    & $python.Source -3 -B (Join-Path $PSScriptRoot 'collect_visual_trace.py') `
        --emulator-pid $player.Id --run $VisualRun
    if ($LASTEXITCODE -ne 0) { throw 'Cadence-1 visual trace failed.' }
}
finally {
    if (-not $player.HasExited) {
        Stop-Process -Id $player.Id
        $player.WaitForExit(10000)
    }
}
