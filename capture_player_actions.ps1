[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\player_actions'
$actions = @('idle', 'walk', 'gun', 'melee', 'jump', 'dash', 'special')

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

New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
Push-Location $projectRoot
try {
    foreach ($action in $actions) {
        $actionRoot = Join-Path $captureRoot $action
        $requiredSample = Join-Path $actionRoot ("{0}_02525.png" -f $action)
        $requiredMetadata = Join-Path $actionRoot 'samples.tsv'
        $requiredHudState = Join-Path $actionRoot 'hud_state.tsv'
        $requiredQSoundWrites = Join-Path $actionRoot 'qsound_writes.tsv'
        if (-not $Refresh -and
            (Test-Path -LiteralPath $requiredSample) -and
            (Test-Path -LiteralPath $requiredMetadata) -and
            (Test-Path -LiteralPath $requiredHudState) -and
            (Test-Path -LiteralPath $requiredQSoundWrites)) {
            Write-Host "Reusing isolated $action capture."
            continue
        }
        if (Test-Path -LiteralPath $actionRoot) {
            $resolvedActionRoot = (Resolve-Path -LiteralPath $actionRoot).Path
            $resolvedCaptureRoot = (Resolve-Path -LiteralPath $captureRoot).Path
            if (-not $resolvedActionRoot.StartsWith(
                    $resolvedCaptureRoot + [IO.Path]::DirectorySeparatorChar,
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw "Refusing to clear action capture outside $resolvedCaptureRoot."
            }
            Remove-Item -LiteralPath $resolvedActionRoot -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path $actionRoot | Out-Null
        $env:AVSP_ACTION_PROBE = $action
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
            '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_player_action.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Isolated $action capture failed with exit code $LASTEXITCODE."
        }
    }
}
finally {
    Remove-Item Env:\AVSP_ACTION_PROBE -ErrorAction SilentlyContinue
    Pop-Location
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
& $PythonPath (Join-Path $projectRoot 'tools\analyze_player_actions.py')
if ($LASTEXITCODE -ne 0) {
    throw "Player-action analysis failed with exit code $LASTEXITCODE."
}

Write-Host "Validated isolated player actions under $captureRoot."
