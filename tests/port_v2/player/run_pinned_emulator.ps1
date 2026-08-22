[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(1, 2)]
    [int]$Run,
    [string]$EmulatorPath
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Get-Command py.exe -ErrorAction Stop
if (-not $EmulatorPath) {
    $candidate = Get-ChildItem -LiteralPath (Join-Path $root '.deps\emulators') `
        -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $candidate) {
        throw 'Pinned Yaba Sanshiro executable was not found under .deps\\emulators.'
    }
    $EmulatorPath = $candidate.FullName
}
$emulator = (Resolve-Path -LiteralPath $EmulatorPath).Path
if ([IO.Path]::GetFileName($emulator).ToLowerInvariant() -ne 'yabasanshiro.exe') {
    throw 'PlayerPromotionBench requires the pinned Yaba Sanshiro executable.'
}

$priorIds = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Id })
& $python.Source -3 -B (Join-Path $PSScriptRoot 'normalize_iso.py') --run $Run
if ($LASTEXITCODE -ne 0) {
    throw "PlayerPromotionBench ISO normalization failed with exit code $LASTEXITCODE."
}
& $python.Source -3 -B (Join-Path $PSScriptRoot 'record_build.py') --run $Run
if ($LASTEXITCODE -ne 0) {
    throw "PlayerPromotionBench build record failed with exit code $LASTEXITCODE."
}
& (Join-Path $root 'run.ps1') -EmulatorPath $emulator
if ($LASTEXITCODE -ne 0) {
    throw "Pinned Yaba Sanshiro launch failed with exit code $LASTEXITCODE."
}
$deadline = (Get-Date).AddSeconds(45)
$player = $null
while ((Get-Date) -lt $deadline) {
    $player = Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
        Where-Object { $priorIds -notcontains $_.Id } |
        Sort-Object StartTime -Descending | Select-Object -First 1
    if ($player) { break }
    Start-Sleep -Milliseconds 250
}
if (-not $player) {
    throw 'Pinned Yaba Sanshiro did not create a new process.'
}

try {
    & $python.Source -3 -B (Join-Path $PSScriptRoot 'collect_readback.py') `
        --run $Run --emulator-pid $player.Id
    if ($LASTEXITCODE -ne 0) {
        throw "PlayerPromotionBench readback failed with exit code $LASTEXITCODE."
    }
}
finally {
    if (-not $player.HasExited) {
        Stop-Process -Id $player.Id
        $player.WaitForExit(10000)
    }
}
