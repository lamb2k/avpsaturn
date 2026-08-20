[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$CaptureName = 'full_route',
    [int]$FinalFrame = 18000
)

# RP2 full-route cadence-1 capture (cold boot -> held Round 2 title).
#
# Determinism contract: MAME 0.289 is deterministic from cold boot given the
# same ROM set, the same NVRAM (EEPROM) contents, and the same frame-indexed
# input schedule. This runner therefore snapshots nvram\avspu once as the
# recorded baseline and restores it before every run, so re-runs reproduce
# identical machine state. -CaptureName lets the determinism check record a
# second run (e.g. full_route_rerun) without clobbering the first.
#
# All raw output is private and git-ignored under .deps\mame\<CaptureName>.
# The tracked census comes from tools\census_full_route.py.

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot (".deps\mame\" + $CaptureName)
$requiredKey = Join-Path $captureRoot 'samples.tsv'
$nvramLive = Join-Path $projectRoot 'nvram\avspu'
$nvramBaseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'

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

# Record the NVRAM baseline once, then restore it before every run.
if (-not (Test-Path -LiteralPath $nvramBaseline)) {
    if (-not (Test-Path -LiteralPath $nvramLive)) {
        throw 'nvram\avspu is missing; the recorded capture baseline is gone.'
    }
    Copy-Item -LiteralPath $nvramLive -Destination $nvramBaseline -Recurse
}
if (Test-Path -LiteralPath $nvramLive) {
    Remove-Item -LiteralPath $nvramLive -Recurse -Force
}
Copy-Item -LiteralPath $nvramBaseline -Destination $nvramLive -Recurse

if ($Refresh -or -not (Test-Path -LiteralPath $requiredKey)) {
    if (Test-Path -LiteralPath $captureRoot) {
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        $resolvedMameRoot = (Resolve-Path -LiteralPath (Split-Path $captureRoot)).Path
        if (-not $resolvedCaptureRoot.StartsWith(
                $resolvedMameRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear route capture outside $resolvedMameRoot."
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null

    # The Lua script writes to the fixed .deps/mame/full_route paths; for a
    # named re-run, generate a copy with the capture root substituted.
    $luaSource = Join-Path $projectRoot 'tools\mame_capture_full_route.lua'
    $luaScript = $luaSource
    if ($CaptureName -ne 'full_route' -or $FinalFrame -ne 18000) {
        $luaScript = Join-Path $captureRoot 'capture.lua'
        (Get-Content -LiteralPath $luaSource -Raw).
            Replace('.deps/mame/full_route', ".deps/mame/$CaptureName").
            Replace('full_route/reference_', "$CaptureName/reference_").
            Replace('local final_frame = 18000', "local final_frame = $FinalFrame") |
            Set-Content -LiteralPath $luaScript -Encoding ascii
    }

    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' '-autoboot_script' $luaScript
        if ($LASTEXITCODE -ne 0) {
            throw "Full-route capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $requiredKey)) {
    throw 'The full-route capture did not produce samples.tsv.'
}
Write-Host "Full-route capture present at $captureRoot"
