[CmdletBinding()]
param(
    [switch]$Refresh,
    [ValidateSet('Combined', 'Hitboxes', 'Collision')]
    [string]$Mode = 'Combined'
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mameRoot = Join-Path $projectRoot '.deps\mame'
$mame = Join-Path $mameRoot 'mame0289\mame.exe'
$modeSettings = @{
    Combined  = @{ Directory = 'debugoverlay';           Row2 = '0xc0' }
    Hitboxes  = @{ Directory = 'debugoverlay_hitboxes';  Row2 = '0x80' }
    Collision = @{ Directory = 'debugoverlay_collision'; Row2 = '0x40' }
}
$setting = $modeSettings[$Mode]
$captureRoot = Join-Path $mameRoot $setting.Directory
$stateName = 'avspu_stage1_debug_{0}' -f $Mode.ToLowerInvariant()
$cfgRoot = Join-Path $mameRoot 'cfg_debugoverlay'
$metadata = Join-Path $captureRoot 'samples.tsv'
$requiredScreenshot = Join-Path $captureRoot 'coldboot_04200.png'

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

if ($Refresh -or -not (Test-Path -LiteralPath $metadata) -or
    -not (Test-Path -LiteralPath $requiredScreenshot)) {
    if (Test-Path -LiteralPath $captureRoot) {
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        $resolvedMameRoot = (Resolve-Path -LiteralPath $mameRoot).Path
        if (-not $resolvedCaptureRoot.StartsWith(
                $resolvedMameRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear debug capture outside $resolvedMameRoot."
        }
        Remove-Item -LiteralPath $resolvedCaptureRoot -Recurse -Force
    }
    if (Test-Path -LiteralPath $cfgRoot) {
        $resolvedCfgRoot = (Resolve-Path -LiteralPath $cfgRoot).Path
        $resolvedMameRoot = (Resolve-Path -LiteralPath $mameRoot).Path
        if (-not $resolvedCfgRoot.StartsWith(
                $resolvedMameRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear debug config outside $resolvedMameRoot."
        }
        Remove-Item -LiteralPath $resolvedCfgRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $cfgRoot | Out-Null
    Push-Location $projectRoot
    try {
        # First launch writes the development hardware mode and active-low DIP
        # settings into the isolated cfg.  The second launch is therefore a
        # genuine cold boot with those values present before game init.
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' `
            '-cfg_directory' '.deps\mame\cfg_debugoverlay' `
            '-nvram_directory' '.deps\mame\nvram_debugoverlay' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_configure_debug_switches.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Debug-switch configuration failed with exit code $LASTEXITCODE."
        }

        $priorCaptureRoot = $env:AVSP_DEBUG_CAPTURE_ROOT
        $priorRow2 = $env:AVSP_DEBUG_ROW2
        $priorStateName = $env:AVSP_DEBUG_STATE_NAME
        try {
            $env:AVSP_DEBUG_CAPTURE_ROOT =
                ('.deps/mame/{0}' -f $setting.Directory)
            $env:AVSP_DEBUG_ROW2 = $setting.Row2
            $env:AVSP_DEBUG_STATE_NAME = $stateName
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-nothrottle' '-skip_gameinfo' `
                '-cfg_directory' '.deps\mame\cfg_debugoverlay' `
                '-nvram_directory' '.deps\mame\nvram_debugoverlay' `
                '-state_directory' '.deps\mame\captures' `
                '-snapshot_directory' '.deps\mame' '-autoboot_delay' '0' `
                '-autoboot_script' '.\tools\mame_probe_debug_overlays.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "Cold-boot debug-overlay capture failed with exit code $LASTEXITCODE."
            }
        }
        finally {
            $env:AVSP_DEBUG_CAPTURE_ROOT = $priorCaptureRoot
            $env:AVSP_DEBUG_ROW2 = $priorRow2
            $env:AVSP_DEBUG_STATE_NAME = $priorStateName
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host 'Reusing the deterministic cold-boot debug-overlay capture.'
}

$rows = Import-Csv -LiteralPath $metadata -Delimiter "`t"
if ($rows.Count -lt 2) {
    throw 'Debug-overlay metadata is incomplete.'
}
$requiredRow2 = [Convert]::ToByte($setting.Row2.Substring(2), 16)
$enabledRows = @($rows | Where-Object {
    [Convert]::ToByte($_.debug_enable, 16) -ne 0 -and
    ([Convert]::ToByte($_.dip_row2, 16) -band $requiredRow2) -eq $requiredRow2
})
if ($enabledRows.Count -eq 0) {
    $last = $rows[-1]
    throw ("Debug flags never enabled: last frame={0}, master={1}, row2={2}." -f
        $last.frame, $last.debug_enable, $last.dip_row2)
}

$first = $enabledRows[0]
Write-Host ("Validated cached debug flags from frame {0}: master={1}, row2={2}." -f
    $first.frame, $first.debug_enable, $first.dip_row2)
Write-Host "Raw screenshots and metadata: $captureRoot"
