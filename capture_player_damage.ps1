[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\player_actions'
$damageRoot = Join-Path $captureRoot 'damage'
$requiredSample = Join-Path $damageRoot 'damage_03400.png'
$requiredMetadata = Join-Path $damageRoot 'samples.tsv'

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
    (Test-Path -LiteralPath $requiredMetadata)) {
    Write-Host 'Reusing the natural player-damage capture.'
}
else {
    New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
    if (Test-Path -LiteralPath $damageRoot) {
        $resolvedDamageRoot = (Resolve-Path -LiteralPath $damageRoot).Path
        $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
        if (-not $resolvedDamageRoot.StartsWith(
                $resolvedCaptureRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clear damage capture outside $resolvedCaptureRoot."
        }
        Remove-Item -LiteralPath $resolvedDamageRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $damageRoot | Out-Null

    Push-Location $projectRoot
    try {
        $env:AVSP_ACTION_PROBE = 'damage'
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_player_action.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Natural player-damage capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Remove-Item Env:\AVSP_ACTION_PROBE -ErrorAction SilentlyContinue
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
& $PythonPath (Join-Path $projectRoot 'tools\analyze_player_damage.py')
if ($LASTEXITCODE -ne 0) {
    throw "Player-damage analysis failed with exit code $LASTEXITCODE."
}

Write-Host "Validated the natural player-damage route under $damageRoot."
