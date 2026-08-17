[CmdletBinding()]
param(
    [string]$PythonPath,
    [switch]$RefreshCapture
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$romRoot = Join-Path $projectRoot 'avspu'
if (-not (Test-Path -LiteralPath $romRoot)) {
    throw 'The local avspu ROM directory is missing from the project root.'
}

& (Join-Path $projectRoot 'setup_reference.ps1')

$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

$captureRoot = Join-Path $projectRoot '.deps\mame\captures'
New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
$requiredCaptures = @('gfx_region.bin', 'gfxram.tsv', 'palette.tsv', 'objram1.tsv',
    'animation_samples.tsv', 'active_object_bank.txt', 'objram_active_2880.tsv',
    'palette_2880.tsv', 'stage1_sample_2880.png')
$captureMissing = $false
foreach ($captureName in $requiredCaptures) {
    if (-not (Test-Path -LiteralPath (Join-Path $captureRoot $captureName))) {
        $captureMissing = $true
        break
    }
}
if ($RefreshCapture -or $captureMissing) {
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' '-nothrottle' `
            '-skip_gameinfo' '-snapshot_directory' '.deps\mame\captures' `
            '-state_directory' '.deps\mame\captures' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_stage1.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Deterministic Stage 1 capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host 'Reusing the existing verified deterministic Stage 1 capture.'
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
        else {
            $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonPath = $bundledPython
            }
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 with Pillow is required. Pass its executable with -PythonPath.'
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_avspu_stage1.py')
if ($LASTEXITCODE -ne 0) {
    throw "CPS2 extraction and Saturn conversion failed with exit code $LASTEXITCODE."
}

Write-Host 'Prepared verified local AvP Stage 1 assets for the Saturn-native build.'
