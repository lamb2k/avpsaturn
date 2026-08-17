[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\enemy_actions'
$requiredSample = Join-Path $captureRoot 'enemy_06200.png'
$requiredMetadata = Join-Path $captureRoot 'samples.tsv'
$requiredWorkram = Join-Path $captureRoot 'workram_06200.bin'
$requiredRegisters = Join-Path $captureRoot 'cps_a_regs_06200.tsv'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'avspu'))) {
    throw 'The local avspu ROM directory is missing from the project root.'
}

& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

if (-not $Refresh -and
    (Test-Path -LiteralPath $requiredSample) -and
    (Test-Path -LiteralPath $requiredMetadata) -and
    (Test-Path -LiteralPath $requiredWorkram) -and
    (Test-Path -LiteralPath $requiredRegisters)) {
    Write-Host 'Reusing the dense enemy-action capture.'
}
else {
    $privateRoot = Join-Path $projectRoot '.deps\mame'
    New-Item -ItemType Directory -Force -Path $privateRoot | Out-Null
    if (Test-Path -LiteralPath $captureRoot) {
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        $resolvedPrivateRoot = (Resolve-Path -LiteralPath $privateRoot).Path
        if (-not $resolvedCaptureRoot.StartsWith(
                $resolvedPrivateRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear enemy capture outside $resolvedPrivateRoot."
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null

    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_enemy_actions.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Enemy-action capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
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
& $PythonPath (Join-Path $projectRoot 'tools\analyze_enemy_actions.py')
if ($LASTEXITCODE -ne 0) {
    throw "Enemy-action analysis failed with exit code $LASTEXITCODE."
}

Write-Host "Validated the dense enemy-action route under $captureRoot."
