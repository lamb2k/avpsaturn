[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\enemy_contact'
$audioRoot = Join-Path $projectRoot '.deps\mame\audio_events'
$mutedWav = Join-Path $audioRoot 'enemy_contact_muted.wav'
$hitWav = Join-Path $audioRoot 'enemy_contact_voice12.wav'
$qsoundWrites = Join-Path $captureRoot 'qsound_writes.tsv'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

New-Item -ItemType Directory -Force -Path $captureRoot, $audioRoot | Out-Null
if ($Refresh -or -not (Test-Path -LiteralPath $mutedWav) -or
    -not (Test-Path -LiteralPath $hitWav) -or
    -not (Test-Path -LiteralPath $qsoundWrites)) {
    Push-Location $projectRoot
    try {
        foreach ($capture in @(
            @{ Name = 'muted'; Voices = 'none'; Output = 'enemy_contact_muted.wav' },
            @{ Name = 'hit'; Voices = '12'; Output = 'enemy_contact_voice12.wav' }
        )) {
            $env:AVSP_QSOUND_ISOLATE_VOICES = $capture.Voices
            $env:AVSP_QSOUND_ISOLATE_START_FRAME = '4245'
            $env:AVSP_QSOUND_ISOLATE_END_FRAME = '4274'
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-samplerate' '44100' `
                '-wavwrite' ".deps\mame\audio_events\$($capture.Output)" `
                '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
                '-autoboot_delay' '0' `
                '-autoboot_script' '.\tools\mame_capture_enemy_contact.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "Enemy-contact $($capture.Name) audio capture failed with exit code $LASTEXITCODE."
            }
        }
    }
    finally {
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_VOICES -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_START_FRAME -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_END_FRAME -ErrorAction SilentlyContinue
        Pop-Location
    }
}
else {
    Write-Host 'Reusing deterministic mute-all and player-hit QSound captures.'
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
        else {
            $bundledPython = Join-Path $env:LOCALAPPDATA `
                'codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonPath = $bundledPython
            }
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 is required. Pass its executable with -PythonPath.'
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_qsound_event.py') `
    '--idle-wav' $mutedWav '--action-wav' $hitWav `
    '--qsound-writes' $qsoundWrites `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\HIT.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_hit_audio.h') `
    '--header-prefix' 'AVSP_HIT' `
    '--report' (Join-Path $projectRoot 'data\qsound_player_hit_capture.json') `
    '--action' 'predator_warrior_damage' '--action-frame' '4243' `
    '--voice' '12' '--start-frame' '4246' '--end-frame' '4274'
if ($LASTEXITCODE -ne 0) {
    throw "QSound player-hit extraction failed with exit code $LASTEXITCODE."
}

Write-Host 'Prepared capture-exact Predator damage PCM for Saturn SCSP playback.'
