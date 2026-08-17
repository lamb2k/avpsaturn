[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\stage1_audio_events'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

$captures = @(
    @{ Name = 'boss_intro_muted'; Voices = 'none'; Start = 5467; End = 5509; Stop = 5511; Wav = 'boss_intro_muted.wav' },
    @{ Name = 'boss_intro_voice12'; Voices = '12'; Start = 5467; End = 5509; Stop = 5511; Wav = 'boss_intro_voice12.wav' },
    @{ Name = 'boss_clear_muted'; Voices = 'none'; Start = 14069; End = 14269; Stop = 14271; Wav = 'boss_clear_muted.wav' },
    @{ Name = 'boss_clear_voices10_12'; Voices = '10,12'; Start = 14069; End = 14269; Stop = 14271; Wav = 'boss_clear_voices10_12.wav' }
)

New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
$needsCapture = $Refresh
foreach ($capture in $captures) {
    if (-not (Test-Path -LiteralPath (Join-Path $captureRoot $capture.Wav))) {
        $needsCapture = $true
    }
}

if ($needsCapture) {
    Push-Location $projectRoot
    try {
        foreach ($capture in $captures) {
            $eventRoot = Join-Path $captureRoot $capture.Name
            New-Item -ItemType Directory -Force -Path $eventRoot | Out-Null
            $relativeRoot = ".deps/mame/stage1_audio_events/$($capture.Name)"
            $env:AVSP_QSOUND_CAPTURE_ROOT = $relativeRoot
            $env:AVSP_QSOUND_CAPTURE_END_FRAME = [string]$capture.Stop
            $env:AVSP_QSOUND_ISOLATE_VOICES = $capture.Voices
            $env:AVSP_QSOUND_ISOLATE_START_FRAME = [string]$capture.Start
            $env:AVSP_QSOUND_ISOLATE_END_FRAME = [string]$capture.End
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-samplerate' '44100' `
                '-wavwrite' ".deps\mame\stage1_audio_events\$($capture.Wav)" `
                '-nothrottle' '-skip_gameinfo' `
                '-state_directory' '.deps\mame\captures' `
                '-autoboot_delay' '0' `
                '-autoboot_script' '.\tools\mame_trace_stage1_qsound.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "Stage 1 $($capture.Name) audio capture failed with exit code $LASTEXITCODE."
            }
        }
    }
    finally {
        Remove-Item Env:\AVSP_QSOUND_CAPTURE_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_CAPTURE_END_FRAME -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_VOICES -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_START_FRAME -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_END_FRAME -ErrorAction SilentlyContinue
        Pop-Location
    }
}
else {
    Write-Host 'Reusing deterministic boss-intro and boss-clear QSound captures.'
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

$extractor = Join-Path $projectRoot 'tools\extract_qsound_event.py'
& $PythonPath $extractor `
    '--idle-wav' (Join-Path $captureRoot 'boss_intro_muted.wav') `
    '--action-wav' (Join-Path $captureRoot 'boss_intro_voice12.wav') `
    '--qsound-writes' (Join-Path $captureRoot 'boss_intro_voice12\qsound_writes.tsv') `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\BOSSIN.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_boss_intro_audio.h') `
    '--header-prefix' 'AVSP_BOSS_INTRO' `
    '--report' (Join-Path $projectRoot 'data\qsound_boss_intro_capture.json') `
    '--action' 'chrysalis_boss_intro' '--action-frame' '5460' `
    '--voice' '12' '--start-frame' '5468' '--end-frame' '5509' `
    '--capture-end-frame' '5511'
if ($LASTEXITCODE -ne 0) {
    throw "QSound boss-intro extraction failed with exit code $LASTEXITCODE."
}

& $PythonPath $extractor `
    '--idle-wav' (Join-Path $captureRoot 'boss_clear_muted.wav') `
    '--action-wav' (Join-Path $captureRoot 'boss_clear_voices10_12.wav') `
    '--qsound-writes' (Join-Path $captureRoot 'boss_clear_voices10_12\qsound_writes.tsv') `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\BOSSCLR.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_boss_clear_audio.h') `
    '--header-prefix' 'AVSP_BOSS_CLEAR' `
    '--report' (Join-Path $projectRoot 'data\qsound_boss_clear_capture.json') `
    '--action' 'chrysalis_defeat_stage_clear' '--action-frame' '13920' `
    '--voice-start' '12:14070' '--voice-start' '10:14126' `
    '--voice-start' '12:14190' '--end-frame' '14269' `
    '--capture-end-frame' '14271'
if ($LASTEXITCODE -ne 0) {
    throw "QSound boss-clear extraction failed with exit code $LASTEXITCODE."
}

Write-Host 'Prepared capture-exact boss-intro and boss-clear PCM for Saturn SCSP playback.'
