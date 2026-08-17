[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\boss_ko'
$stateFile = Join-Path $projectRoot `
    '.deps\mame\captures\avspu\avspu_stage1_boss_12660.sta'
$terminalSample = Join-Path $captureRoot 'workram_14260.bin'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'avspu'))) {
    throw 'The local avspu ROM directory is missing from the project root.'
}
if (-not (Test-Path -LiteralPath $stateFile)) {
    throw 'The verified frame-12660 Chrysalis save state is missing.'
}

& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

if (-not $Refresh -and (Test-Path -LiteralPath $terminalSample)) {
    Write-Host 'Reusing the deterministic Chrysalis KO capture.'
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
            throw "Refusing to clear boss KO capture outside $resolvedPrivateRoot."
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null

    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' `
            '-snapshot_directory' '.deps\mame\boss_ko' `
            '-state_directory' '.deps\mame\captures' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_boss_ko.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Chrysalis KO capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $terminalSample)) {
    throw 'The Chrysalis KO capture did not produce its terminal sample.'
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
& $PythonPath (Join-Path $projectRoot 'tools\analyze_boss_ko.py')
if ($LASTEXITCODE -ne 0) {
    throw "Chrysalis KO analysis failed with exit code $LASTEXITCODE."
}
Write-Host "Validated deterministic Chrysalis KO under $captureRoot."
