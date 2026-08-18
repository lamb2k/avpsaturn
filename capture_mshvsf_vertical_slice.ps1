[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$captureRoot = Join-Path $projectRoot '.deps\mame\mshvsf_vertical_slice'
$launcher = Join-Path $projectRoot 'tools\run_mshvsf_mame.py'
$analyzer = Join-Path $projectRoot 'tools\analyze_mshvsf_vertical_slice.py'
$report = Join-Path $projectRoot 'data\mshvsf_cps2_vertical_slice.json'
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'

if (-not $PythonPath) {
    $PythonPath = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
}
if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python runtime not found: $PythonPath"
}
if (-not (Test-Path -LiteralPath $mame)) {
    throw "Pinned MAME runtime not found: $mame"
}

$requiredSample = Join-Path $captureRoot 'frame_01860.png'
$requiredMetadata = Join-Path $captureRoot 'samples.tsv'
if (-not $Refresh -and (Test-Path -LiteralPath $requiredSample) -and
    (Test-Path -LiteralPath $requiredMetadata)) {
    Write-Host "Reusing MSHvSF vertical-slice capture under $captureRoot."
}
elseif ($Refresh -and (Test-Path -LiteralPath $captureRoot)) {
    $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
    $resolvedDepsRoot = (Resolve-Path -LiteralPath `
        (Join-Path $projectRoot '.deps\mame')).Path
    if (-not $resolvedCaptureRoot.StartsWith(
            $resolvedDepsRoot + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clear capture outside $resolvedDepsRoot."
    }
    Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    Push-Location $projectRoot
    try {
        & $PythonPath $launcher '--' 'mshvsf' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-nvram_directory' '.deps\mame\mshvsf_nvram' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_mshvsf_vertical_slice.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "MSHvSF vertical-slice capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    Push-Location $projectRoot
    try {
        & $PythonPath $launcher '--' 'mshvsf' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-nvram_directory' '.deps\mame\mshvsf_nvram' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_mshvsf_vertical_slice.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "MSHvSF vertical-slice capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $requiredSample) -or
    -not (Test-Path -LiteralPath $requiredMetadata)) {
    throw 'MSHvSF vertical-slice capture completed without required evidence.'
}
& $PythonPath $analyzer '--capture-root' $captureRoot '--output' $report
if ($LASTEXITCODE -ne 0) {
    throw "MSHvSF vertical-slice analysis failed with exit code $LASTEXITCODE."
}
Write-Host "Validated deterministic MSHvSF vertical slice and refreshed $report."
