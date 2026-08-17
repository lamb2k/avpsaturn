[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\stalker_actions'
$stateFile = Join-Path $projectRoot `
    '.deps\mame\captures\avspu\avspu_stage1.sta'
$requiredMetadata = Join-Path $captureRoot 'samples.tsv'
$requiredWorkram = Join-Path $captureRoot 'workram_07800.bin'
$requiredObjectRam = Join-Path $captureRoot 'objram_active_07800.tsv'
$requiredRegisters = Join-Path $captureRoot 'cps_a_regs_07800.tsv'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'avspu'))) {
    throw 'The local avspu ROM directory is missing from the project root.'
}
if (-not (Test-Path -LiteralPath $stateFile)) {
    throw 'The verified frame-4200 Stage 1 save is missing. Run prepare_avsp_port.ps1 -RefreshCapture first.'
}

& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

if (-not $Refresh -and
    (Test-Path -LiteralPath $requiredMetadata) -and
    (Test-Path -LiteralPath $requiredWorkram) -and
    (Test-Path -LiteralPath $requiredObjectRam) -and
    (Test-Path -LiteralPath $requiredRegisters)) {
    Write-Host 'Reusing the dense Stage 1 Stalker capture.'
}
else {
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' `
            '-snapshot_directory' '.deps\mame\stalker_actions' `
            '-state_directory' '.deps\mame\captures' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_stalker_actions.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Stalker-action capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $requiredMetadata) -or
    -not (Test-Path -LiteralPath $requiredWorkram) -or
    -not (Test-Path -LiteralPath $requiredObjectRam) -or
    -not (Test-Path -LiteralPath $requiredRegisters)) {
    throw 'The Stalker-action capture did not produce its terminal sample.'
}

if (-not $PythonPath) {
    $pythonCommand = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $PythonPath = $pythonCommand.Source
    }
    else {
        $pythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
        if ($pythonCommand -and $pythonCommand.Source -notlike '*WindowsApps*') {
            $PythonPath = $pythonCommand.Source
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 with Pillow is required. Pass its executable with -PythonPath.'
}
& $PythonPath (Join-Path $projectRoot 'tools\analyze_stalker_actions.py')
if ($LASTEXITCODE -ne 0) {
    throw "Stalker-action analysis failed with exit code $LASTEXITCODE."
}

Write-Host "Validated dense Stage 1 Stalker actions under $captureRoot."
