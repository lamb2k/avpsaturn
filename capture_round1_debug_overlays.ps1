[CmdletBinding()]
param(
    [switch]$Refresh,
    [ValidateSet('Hitboxes', 'Collision')]
    [string]$Mode = 'Hitboxes'
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mameRoot = Join-Path $projectRoot '.deps\mame'
$mame = Join-Path $mameRoot 'mame0289\mame.exe'
$modeSettings = @{
    Hitboxes  = @{
        Seed = 'debugoverlay_hitboxes'
        Directory = 'round1_debug_hitboxes'
        Row2 = '0x80'
        Cadence = 1
        FinalFrame = 15000
    }
    Collision = @{
        Seed = 'debugoverlay_collision'
        Directory = 'round1_debug_collision'
        Row2 = '0x40'
        Cadence = 30
        # First post-boss dialogue frame; Round 2 play starts shortly after.
        FinalFrame = 17791
    }
}
$setting = $modeSettings[$Mode]
$stateName = 'avspu_stage1_debug_{0}' -f $Mode.ToLowerInvariant()
$captureRoot = Join-Path $mameRoot $setting.Directory
$metadata = Join-Path $captureRoot 'samples.tsv'
$stateFile = Join-Path $captureRoot 'actor_state.bin'
$expectedSamples = [int][Math]::Floor(($setting.FinalFrame - 4201) / $setting.Cadence) + 1
$lastSampleFrame = 4201 + ($expectedSamples - 1) * $setting.Cadence
$requiredScreenshot = Join-Path $captureRoot `
    ('overlay_{0:D5}.png' -f $lastSampleFrame)

if ($Refresh -or -not (Test-Path -LiteralPath $metadata) -or
    -not (Test-Path -LiteralPath $stateFile) -or
    -not (Test-Path -LiteralPath $requiredScreenshot)) {
    & (Join-Path $projectRoot 'capture_debug_overlays.ps1') `
        -Refresh -Mode $Mode
    if ($LASTEXITCODE -ne 0) {
        throw "The $Mode cold-boot seed capture failed with exit code $LASTEXITCODE."
    }

    if (Test-Path -LiteralPath $captureRoot) {
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        $resolvedMameRoot = (Resolve-Path -LiteralPath $mameRoot).Path
        if (-not $resolvedCaptureRoot.StartsWith(
                $resolvedMameRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear Round 1 debug capture outside $resolvedMameRoot."
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null

    $priorCaptureRoot = $env:AVSP_DEBUG_CAPTURE_ROOT
    $priorStateName = $env:AVSP_DEBUG_STATE_NAME
    $priorRow2 = $env:AVSP_DEBUG_ROW2
    $priorCadence = $env:AVSP_DEBUG_CADENCE
    $priorFinalFrame = $env:AVSP_DEBUG_FINAL_FRAME
    try {
        $env:AVSP_DEBUG_CAPTURE_ROOT =
            ('.deps/mame/{0}' -f $setting.Directory)
        $env:AVSP_DEBUG_STATE_NAME = $stateName
        $env:AVSP_DEBUG_ROW2 = $setting.Row2
        $env:AVSP_DEBUG_CADENCE = [string]$setting.Cadence
        $env:AVSP_DEBUG_FINAL_FRAME = [string]$setting.FinalFrame
        Push-Location $projectRoot
        try {
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-nothrottle' '-skip_gameinfo' `
                '-cfg_directory' '.deps\mame\cfg_debugoverlay' `
                '-nvram_directory' '.deps\mame\nvram_debugoverlay' `
                '-state_directory' '.deps\mame\captures' `
                '-snapshot_directory' '.deps\mame' '-autoboot_delay' '0' `
                '-autoboot_script' `
                '.\tools\mame_capture_round1_debug_overlays.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "$Mode Round 1 capture failed with exit code $LASTEXITCODE."
            }
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:AVSP_DEBUG_CAPTURE_ROOT = $priorCaptureRoot
        $env:AVSP_DEBUG_STATE_NAME = $priorStateName
        $env:AVSP_DEBUG_ROW2 = $priorRow2
        $env:AVSP_DEBUG_CADENCE = $priorCadence
        $env:AVSP_DEBUG_FINAL_FRAME = $priorFinalFrame
    }
}
else {
    Write-Host "Reusing the deterministic Round 1 $Mode capture."
}

$rows = @(Import-Csv -LiteralPath $metadata -Delimiter "`t")
if ($rows.Count -ne $expectedSamples) {
    throw "Expected $expectedSamples $Mode samples, found $($rows.Count)."
}
if ([int]$rows[0].frame -ne 4201 -or
    [int]$rows[-1].frame -ne $lastSampleFrame) {
    throw "$Mode frame endpoints changed."
}
$expectedStateBytes = [int64]$expectedSamples * 0x2d00
$actualStateBytes = (Get-Item -LiteralPath $stateFile).Length
if ($actualStateBytes -ne $expectedStateBytes) {
    throw "Expected $expectedStateBytes actor-state bytes, found $actualStateBytes."
}
$requiredRow2 = [Convert]::ToByte($setting.Row2.Substring(2), 16)
$badFlags = @($rows | Where-Object {
    [Convert]::ToByte($_.debug_enable, 16) -eq 0 -or
    ([Convert]::ToByte($_.dip_row2, 16) -band $requiredRow2) -ne $requiredRow2
})
if ($badFlags.Count -ne 0) {
    throw "$Mode debug flags were lost in $($badFlags.Count) samples."
}

Write-Host (("Validated Round 1 {0}: frames 4201..{1}, cadence {2}, " +
    "{3} samples, {4} actor-state bytes.") -f
    $Mode, $lastSampleFrame, $setting.Cadence, $expectedSamples, $actualStateBytes)
Write-Host "Raw screenshots, metadata, and actor RAM: $captureRoot"
