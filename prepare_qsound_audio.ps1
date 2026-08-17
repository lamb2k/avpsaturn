[CmdletBinding()]
param(
    [string]$PythonPath,
    [switch]$Refresh
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$audioRoot = Join-Path $projectRoot '.deps\mame\audio_events'
$idleWav = Join-Path $audioRoot 'idle_voice12_event.wav'
$gunWav = Join-Path $audioRoot 'gun_voice12_event.wav'
$gunWrites = Join-Path $projectRoot '.deps\mame\player_actions\gun\qsound_writes.tsv'

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

New-Item -ItemType Directory -Force -Path $audioRoot | Out-Null
foreach ($action in @('idle', 'gun')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot `
        ".deps\mame\player_actions\$action") | Out-Null
}

if ($Refresh -or -not (Test-Path -LiteralPath $idleWav) -or
    -not (Test-Path -LiteralPath $gunWav) -or
    -not (Test-Path -LiteralPath $gunWrites)) {
    Push-Location $projectRoot
    try {
        foreach ($action in @('idle', 'gun')) {
            $env:AVSP_ACTION_PROBE = $action
            $env:AVSP_QSOUND_ISOLATE_VOICE = '12'
            $env:AVSP_QSOUND_ISOLATE_END_FRAME = '2582'
            $wavName = "${action}_voice12_event.wav"
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-samplerate' '44100' '-wavwrite' ".deps\mame\audio_events\$wavName" `
                '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
                '-autoboot_delay' '0' `
                '-autoboot_script' '.\tools\mame_capture_player_action.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "Isolated QSound $action capture failed with exit code $LASTEXITCODE."
            }
        }
    }
    finally {
        Remove-Item Env:\AVSP_ACTION_PROBE -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_VOICE -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_END_FRAME -ErrorAction SilentlyContinue
        Pop-Location
    }
}
else {
    Write-Host 'Reusing deterministic isolated QSound idle and gun captures.'
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
    throw 'Python 3 is required. Pass its executable with -PythonPath.'
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_qsound_event.py') `
    '--idle-wav' $idleWav `
    '--action-wav' $gunWav `
    '--qsound-writes' $gunWrites `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\GUN.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_audio.h') `
    '--report' (Join-Path $projectRoot 'data\qsound_gun_capture.json') `
    '--voice' '12' '--action-frame' '2525' '--start-frame' '2530' `
    '--end-frame' '2582'
if ($LASTEXITCODE -ne 0) {
    throw "QSound event extraction failed with exit code $LASTEXITCODE."
}

Write-Host 'Prepared capture-exact Predator weapon PCM for Saturn SCSP playback.'
