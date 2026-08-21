[CmdletBinding()]
param(
    [string]$PythonPath,
    [string]$EmulatorPath,
    [switch]$BuildOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
if (-not $PythonPath) {
    $python = Get-Command py.exe -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python.exe -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        throw 'Python 3 is required.'
    }
    $PythonPath = $python.Source
}
$recorder = Join-Path $PSScriptRoot 'record_build.py'
$collector = Join-Path $PSScriptRoot 'collect_readback.py'
$validator = Join-Path $PSScriptRoot 'test_contract.py'

foreach ($run in 1, 2) {
    & (Join-Path $projectRoot 'build.ps1') -Clean -StreetTest -SkipHostTests `
        -PythonPath $PythonPath
    if ($LASTEXITCODE -ne 0) {
        throw "OldBuildBaseline build $run failed."
    }
    & $PythonPath -B $recorder --run $run
    if ($LASTEXITCODE -ne 0) {
        throw "OldBuildBaseline build record $run failed."
    }
}
& $PythonPath -B $validator --evidence build --negative-control
if ($LASTEXITCODE -ne 0) {
    throw 'OldBuildBaseline build repeat or negative control failed.'
}
if ($BuildOnly) {
    return
}

if (-not $EmulatorPath) {
    $EmulatorPath = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.deps\emulators') `
        -Filter yabasanshiro.exe -File -Recurse | Where-Object {
            $_.FullName -like '*yabasanshiro-1.20.37-2986eb*'
        } | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $EmulatorPath -or -not (Test-Path -LiteralPath $EmulatorPath)) {
    throw 'Pinned Yaba Sanshiro 1.20.37-2986eb is missing.'
}
$resolvedEmulator = (Resolve-Path -LiteralPath $EmulatorPath).Path

foreach ($run in 1, 2) {
    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'yabasanshiro.exe' -and
        $_.ExecutablePath -eq $resolvedEmulator
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

    $before = @(Get-Process yabasanshiro -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Id)
    & (Join-Path $projectRoot 'run.ps1') -EmulatorPath $resolvedEmulator
    $deadline = (Get-Date).AddSeconds(30)
    $emulator = $null
    while ((Get-Date) -lt $deadline -and -not $emulator) {
        Start-Sleep -Milliseconds 250
        $emulator = Get-Process yabasanshiro -ErrorAction SilentlyContinue |
            Where-Object { $_.Id -notin $before } | Select-Object -First 1
    }
    if (-not $emulator) {
        throw "Pinned emulator did not start for readback $run."
    }
    try {
        & $PythonPath -B $collector --run $run --emulator-pid $emulator.Id
        if ($LASTEXITCODE -ne 0) {
            throw "OldBuildBaseline emulator readback $run failed."
        }
    }
    finally {
        Stop-Process -Id $emulator.Id -Force -ErrorAction SilentlyContinue
    }
}

& $PythonPath -B $validator --evidence full
if ($LASTEXITCODE -ne 0) {
    throw 'OldBuildBaseline emulator repeat failed.'
}
