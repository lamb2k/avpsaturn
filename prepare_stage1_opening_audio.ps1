[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\opening_audio_events'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

$captures = @(
    @{ Name = 'round_title_a_muted'; Voices = 'none'; Start = 2030; End = 2070; Stop = 2072; Wav = 'round_title_a_muted.wav' },
    @{ Name = 'round_title_a_voices13_14'; Voices = '13,14'; Start = 2030; End = 2070; Stop = 2072; Wav = 'round_title_a_voices13_14.wav' },
    @{ Name = 'round_title_b_muted'; Voices = 'none'; Start = 2075; End = 2107; Stop = 2109; Wav = 'round_title_b_muted.wav' },
    @{ Name = 'round_title_b_voice14'; Voices = '14'; Start = 2075; End = 2107; Stop = 2109; Wav = 'round_title_b_voice14.wav' },
    @{ Name = 'withdraw_muted'; Voices = 'none'; Start = 2254; End = 2388; Stop = 2390; Wav = 'withdraw_muted.wav' },
    @{ Name = 'withdraw_voices9_10_14'; Voices = '9,10,14'; Start = 2254; End = 2388; Stop = 2390; Wav = 'withdraw_voices9_10_14.wav' },
    @{ Name = 'breach_muted'; Voices = 'none'; Start = 2418; End = 2518; Stop = 2520; Wav = 'breach_muted.wav' },
    @{ Name = 'breach_voices10_12_13_14'; Voices = '10,12,13,14'; Start = 2418; End = 2518; Stop = 2520; Wav = 'breach_voices10_12_13_14.wav' }
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
            $env:AVSP_QSOUND_COLD_BOOT = '1'
            $env:AVSP_QSOUND_CAPTURE_ROOT =
                ".deps/mame/opening_audio_events/$($capture.Name)"
            $env:AVSP_QSOUND_CAPTURE_END_FRAME = [string]$capture.Stop
            $env:AVSP_QSOUND_ISOLATE_VOICES = $capture.Voices
            $env:AVSP_QSOUND_ISOLATE_START_FRAME = [string]$capture.Start
            $env:AVSP_QSOUND_ISOLATE_END_FRAME = [string]$capture.End
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-samplerate' '44100' `
                '-wavwrite' ".deps\mame\opening_audio_events\$($capture.Wav)" `
                '-nothrottle' '-skip_gameinfo' '-autoboot_delay' '0' `
                '-autoboot_script' '.\tools\mame_trace_stage1_qsound.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "Opening $($capture.Name) audio capture failed with exit code $LASTEXITCODE."
            }
        }
    }
    finally {
        Remove-Item Env:\AVSP_QSOUND_COLD_BOOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_CAPTURE_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_CAPTURE_END_FRAME -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_VOICES -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_START_FRAME -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_QSOUND_ISOLATE_END_FRAME -ErrorAction SilentlyContinue
        Pop-Location
    }
}
else {
    Write-Host 'Reusing deterministic opening QSound captures.'
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
    '--idle-wav' (Join-Path $captureRoot 'round_title_a_muted.wav') `
    '--action-wav' (Join-Path $captureRoot 'round_title_a_voices13_14.wav') `
    '--qsound-writes' (Join-Path $captureRoot 'round_title_a_voices13_14\qsound_writes.tsv') `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\RND1A.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_round_title_a_audio.h') `
    '--header-prefix' 'AVSP_ROUND_TITLE_A' `
    '--report' (Join-Path $projectRoot 'data\qsound_round_title_a_capture.json') `
    '--action' 'round_1_title_lead' '--action-frame' '2031' `
    '--voice-start' '13:2031' '--voice-start' '14:2035' `
    '--end-frame' '2070' '--capture-end-frame' '2072'
if ($LASTEXITCODE -ne 0) { throw "Round-title lead extraction failed: $LASTEXITCODE." }

& $PythonPath $extractor `
    '--idle-wav' (Join-Path $captureRoot 'round_title_b_muted.wav') `
    '--action-wav' (Join-Path $captureRoot 'round_title_b_voice14.wav') `
    '--qsound-writes' (Join-Path $captureRoot 'round_title_b_voice14\qsound_writes.tsv') `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\RND1B.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_round_title_b_audio.h') `
    '--header-prefix' 'AVSP_ROUND_TITLE_B' `
    '--report' (Join-Path $projectRoot 'data\qsound_round_title_b_capture.json') `
    '--action' 'round_1_title_tail' '--action-frame' '2076' `
    '--voice' '14' '--start-frame' '2076' '--end-frame' '2107' `
    '--capture-end-frame' '2109'
if ($LASTEXITCODE -ne 0) { throw "Round-title tail extraction failed: $LASTEXITCODE." }

& $PythonPath $extractor `
    '--idle-wav' (Join-Path $captureRoot 'withdraw_muted.wav') `
    '--action-wav' (Join-Path $captureRoot 'withdraw_voices9_10_14.wav') `
    '--qsound-writes' (Join-Path $captureRoot 'withdraw_voices9_10_14\qsound_writes.tsv') `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\WITHDRW.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_withdraw_audio.h') `
    '--header-prefix' 'AVSP_WITHDRAW' `
    '--report' (Join-Path $projectRoot 'data\qsound_withdraw_capture.json') `
    '--action' 'withdraw_sequence' '--action-frame' '2160' `
    '--voice-start' '10:2255' '--voice-start' '9:2262' `
    '--voice-start' '10:2325' '--voice-start' '14:2333' `
    '--voice-start' '10:2340' '--voice-start' '10:2356' `
    '--voice-start' '10:2373' '--end-frame' '2388' `
    '--capture-end-frame' '2390'
if ($LASTEXITCODE -ne 0) { throw "Withdraw-sequence extraction failed: $LASTEXITCODE." }

& $PythonPath $extractor `
    '--idle-wav' (Join-Path $captureRoot 'breach_muted.wav') `
    '--action-wav' (Join-Path $captureRoot 'breach_voices10_12_13_14.wav') `
    '--qsound-writes' (Join-Path $captureRoot 'breach_voices10_12_13_14\qsound_writes.tsv') `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\BREACH.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_breach_audio.h') `
    '--header-prefix' 'AVSP_BREACH' `
    '--report' (Join-Path $projectRoot 'data\qsound_breach_capture.json') `
    '--action' 'barricade_breach_sequence' '--action-frame' '2400' `
    '--voice-start' '13:2419' '--voice-start' '10:2421' `
    '--voice-start' '13:2428' '--voice-start' '12:2429' `
    '--voice-start' '10:2437' '--voice-start' '14:2479' `
    '--voice-start' '13:2489' '--voice-start' '12:2490' `
    '--end-frame' '2518' '--capture-end-frame' '2520'
if ($LASTEXITCODE -ne 0) { throw "Barricade-breach extraction failed: $LASTEXITCODE." }

Write-Host 'Prepared capture-exact Round 1, withdraw, and barricade-breach PCM.'
