[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

# Capture the character-confirm wipe at cadence 1 to pin the start frame and
# per-frame rate that the cadence-2 frontend capture leaves ambiguous. This
# writes to its own directory so .deps\mame\frontend, which backs the tracked
# frontend reports, is never touched.

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\frontend_wipe'
$requiredFirst = Join-Path $captureRoot 'frontend_1870.png'
$requiredLast = Join-Path $captureRoot 'frontend_1912.png'
$requiredMetadata = Join-Path $captureRoot 'samples.tsv'

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

if ($Refresh -or -not (Test-Path -LiteralPath $requiredFirst) -or
    -not (Test-Path -LiteralPath $requiredLast) -or
    -not (Test-Path -LiteralPath $requiredMetadata)) {
    if (Test-Path -LiteralPath $captureRoot) {
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        $resolvedMameRoot = (Resolve-Path -LiteralPath (Split-Path $captureRoot)).Path
        if (-not $resolvedCaptureRoot.StartsWith(
                $resolvedMameRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear wipe capture outside $resolvedMameRoot."
        }
        if ($resolvedCaptureRoot -eq (Join-Path $resolvedMameRoot 'frontend')) {
            throw 'Refusing to clear the cadence-2 frontend capture.'
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_frontend_wipe.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Wipe capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host 'Reusing the deterministic cadence-1 wipe capture.'
}

if (-not $PythonPath) {
    $bundledPython = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) {
        $PythonPath = $bundledPython
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 with Pillow and numpy is required. Pass it with -PythonPath.'
}
& $PythonPath (Join-Path $projectRoot 'tools\analyze_frontend_geometry.py') `
    '--capture-root' '.deps/mame/frontend_wipe' '--cadence' '1' `
    '--first' '1870' '--last' '1912' '--static-frame' '1870' `
    '--output' 'data/frontend_geometry_cadence1.json' '--report'
if ($LASTEXITCODE -ne 0) {
    throw "Wipe geometry analysis failed with exit code $LASTEXITCODE."
}

Write-Host "Validated cadence-1 wipe capture under $captureRoot."
