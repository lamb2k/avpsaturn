[CmdletBinding()]
param(
    [switch]$Refresh,
    [switch]$RefreshComposites,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\enemy_contact'
$audioRoot = Join-Path $projectRoot '.deps\mame\audio_events'
$mutedWav = Join-Path $audioRoot 'enemy_contact_muted.wav'
$hitMutedWav = Join-Path $audioRoot 'enemy_hit_muted.wav'
$hitWav = Join-Path $audioRoot 'enemy_contact_voice12.wav'
$impactWav = Join-Path $audioRoot 'enemy_contact_voice13.wav'
$koMutedWav = Join-Path $audioRoot 'enemy_ko_muted.wav'
$koImpactWav = Join-Path $audioRoot 'enemy_ko_voice14.wav'
$contactMutedWav = Join-Path $audioRoot 'enemy_contact_composite_muted.wav'
$contactWav = Join-Path $audioRoot 'enemy_contact_voices12_13.wav'
$koContactMutedWav = Join-Path $audioRoot 'enemy_ko_composite_muted.wav'
$koContactWav = Join-Path $audioRoot 'enemy_ko_voices12_14.wav'
$qsoundWrites = Join-Path $captureRoot 'qsound_writes.tsv'

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

New-Item -ItemType Directory -Force -Path $captureRoot, $audioRoot | Out-Null
$captureComponents = $Refresh -or -not (Test-Path -LiteralPath $mutedWav) -or
    -not (Test-Path -LiteralPath $hitMutedWav) -or
    -not (Test-Path -LiteralPath $hitWav) -or
    -not (Test-Path -LiteralPath $impactWav) -or
    -not (Test-Path -LiteralPath $koMutedWav) -or
    -not (Test-Path -LiteralPath $koImpactWav) -or
    -not (Test-Path -LiteralPath $qsoundWrites)
$captureComposites = $Refresh -or $RefreshComposites -or
    -not (Test-Path -LiteralPath $contactMutedWav) -or
    -not (Test-Path -LiteralPath $contactWav) -or
    -not (Test-Path -LiteralPath $koContactMutedWav) -or
    -not (Test-Path -LiteralPath $koContactWav) -or
    -not (Test-Path -LiteralPath $qsoundWrites)
if ($captureComponents -or $captureComposites) {
    $captures = @()
    if ($captureComponents) {
        $captures += @(
            @{ Name = 'impact-muted'; Voices = 'none'; Start = '4244'; End = '4268'; Output = 'enemy_contact_muted.wav' },
            @{ Name = 'impact'; Voices = '13'; Start = '4244'; End = '4268'; Output = 'enemy_contact_voice13.wav' },
            @{ Name = 'hit-muted'; Voices = 'none'; Start = '4245'; End = '4274'; Output = 'enemy_hit_muted.wav' },
            @{ Name = 'hit'; Voices = '12'; Start = '4245'; End = '4274'; Output = 'enemy_contact_voice12.wav' },
            @{ Name = 'ko-muted'; Voices = 'none'; Start = '4434'; End = '4461'; Output = 'enemy_ko_muted.wav' },
            @{ Name = 'ko-impact'; Voices = '14'; Start = '4434'; End = '4461'; Output = 'enemy_ko_voice14.wav' }
        )
    }
    if ($captureComposites) {
        $captures += @(
            @{ Name = 'contact-composite-muted'; Voices = 'none'; Start = '4244'; End = '4274'; Output = 'enemy_contact_composite_muted.wav' },
            @{ Name = 'contact-composite'; Voices = '12,13'; Start = '4244'; End = '4274'; Output = 'enemy_contact_voices12_13.wav' },
            @{ Name = 'ko-composite-muted'; Voices = 'none'; Start = '4434'; End = '4464'; Output = 'enemy_ko_composite_muted.wav' },
            @{ Name = 'ko-composite'; Voices = '12,14'; Start = '4434'; End = '4464'; Output = 'enemy_ko_voices12_14.wav' }
        )
    }
    Push-Location $projectRoot
    try {
        foreach ($capture in $captures) {
            $env:AVSP_QSOUND_ISOLATE_VOICES = $capture.Voices
            $env:AVSP_QSOUND_ISOLATE_START_FRAME = $capture.Start
            $env:AVSP_QSOUND_ISOLATE_END_FRAME = $capture.End
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
    Write-Host 'Reusing deterministic player-hit and contact-impact QSound captures.'
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
    '--idle-wav' $hitMutedWav '--action-wav' $hitWav `
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

& $PythonPath (Join-Path $projectRoot 'tools\extract_qsound_event.py') `
    '--idle-wav' $mutedWav '--action-wav' $impactWav `
    '--qsound-writes' $qsoundWrites `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\IMPACT.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_impact_audio.h') `
    '--header-prefix' 'AVSP_IMPACT' `
    '--report' (Join-Path $projectRoot 'data\qsound_enemy_impact_capture.json') `
    '--action' 'alien_contact_impact' '--action-frame' '4243' `
    '--voice' '13' '--start-frame' '4245' '--end-frame' '4268'
if ($LASTEXITCODE -ne 0) {
    throw "QSound enemy-impact extraction failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_qsound_event.py') `
    '--idle-wav' $koMutedWav '--action-wav' $koImpactWav `
    '--qsound-writes' $qsoundWrites `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\KOIMP.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_ko_impact_audio.h') `
    '--header-prefix' 'AVSP_KO_IMPACT' `
    '--report' (Join-Path $projectRoot 'data\qsound_enemy_ko_impact_capture.json') `
    '--action' 'alien_contact_ko_impact' '--action-frame' '4433' `
    '--voice' '14' '--start-frame' '4435' '--end-frame' '4461'
if ($LASTEXITCODE -ne 0) {
    throw "QSound enemy-KO-impact extraction failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_qsound_event.py') `
    '--idle-wav' $contactMutedWav '--action-wav' $contactWav `
    '--qsound-writes' $qsoundWrites `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\CONTACT.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_contact_audio.h') `
    '--header-prefix' 'AVSP_CONTACT' `
    '--report' (Join-Path $projectRoot 'data\qsound_enemy_contact_composite_capture.json') `
    '--action' 'alien_contact_composite' '--action-frame' '4243' `
    '--voice-start' '13:4245' '--voice-start' '12:4246' '--end-frame' '4274'
if ($LASTEXITCODE -ne 0) {
    throw "QSound enemy-contact composite extraction failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_qsound_event.py') `
    '--idle-wav' $koContactMutedWav '--action-wav' $koContactWav `
    '--qsound-writes' $qsoundWrites `
    '--output-pcm' (Join-Path $projectRoot 'build\avsp_cd\AUDIO\KOCONT.PCM') `
    '--output-header' (Join-Path $projectRoot 'generated\avsp_ko_contact_audio.h') `
    '--header-prefix' 'AVSP_KO_CONTACT' `
    '--report' (Join-Path $projectRoot 'data\qsound_enemy_ko_contact_composite_capture.json') `
    '--action' 'alien_ko_contact_composite' '--action-frame' '4433' `
    '--voice-start' '14:4435' '--voice-start' '12:4436' '--end-frame' '4464'
if ($LASTEXITCODE -ne 0) {
    throw "QSound enemy-KO-contact composite extraction failed with exit code $LASTEXITCODE."
}

Write-Host 'Prepared capture-exact damage components and channel-safe contact composites for Saturn SCSP playback.'
