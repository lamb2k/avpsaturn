[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

# ROM-truth frontend capture: the state the ROM COMPOSES the title and
# character-select screens from (gfxram tilemaps + cps_a/cps_b registers +
# objram + palette), not screen pixels. capture_frontend.ps1 remains the
# pixel capture used by the segmentation report; this one is what a faithful
# rebuild from original assets needs.
#
# Writes the private capture to .deps\mame\frontend_rom (git-ignored) and
# leaves the tracked structural report to
# tools\analyze_frontend_rom_composition.py.

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\frontend_rom'
$requiredMetadata = Join-Path $captureRoot 'samples.tsv'
$requiredKey = Join-Path $captureRoot 'cps_a_regs_1760.tsv'

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

if ($Refresh -or -not (Test-Path -LiteralPath $requiredKey) -or
    -not (Test-Path -LiteralPath $requiredMetadata)) {
    if (Test-Path -LiteralPath $captureRoot) {
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        $resolvedMameRoot = (Resolve-Path -LiteralPath (Split-Path $captureRoot)).Path
        if (-not $resolvedCaptureRoot.StartsWith(
                $resolvedMameRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear frontend capture outside $resolvedMameRoot."
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_frontend_rom.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend ROM-truth capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "Reusing the existing frontend ROM-truth capture."
}

if (-not $PythonPath) {
    $bundledPython = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) {
        $PythonPath = $bundledPython
    }
    else {
        $pythonCommand = Get-Command 'py.exe' -ErrorAction SilentlyContinue
        if ($pythonCommand) { $PythonPath = $pythonCommand.Source }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 is required to derive the frontend composition report.'
}

& $PythonPath (Join-Path $projectRoot 'tools\analyze_frontend_rom_composition.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend composition analysis failed with exit code $LASTEXITCODE."
}
