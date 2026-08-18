param(
    [string]$State = 'avspu_stage1_replay4200',
    [int]$StateFrame = 4200,
    [int]$FrameA = 4214,
    [int]$FrameB = 4253,
    [string]$ObjectListBase = '7080A0',
    [int]$Words = 20,
    # Word-write watchpoints installed from ObjectListBase. Defaults to $Words.
    # The alien's slot run starts at a run-dependent list index, so a window as
    # wide as the gated word count can attribute only a prefix of the burst on
    # frames where non-alien objects precede it; widen this (staying under the
    # empirical 34-watchpoint ceiling, watchpoints + 1 bank) to attribute every
    # gated word. It never changes what is decoded - decoding reads the dumps.
    [int]$WatchWords = 0,
    [string]$BankSelectRegister = '8040E0',
    [string]$ActorBase = 'FFA000',
    [string]$RawDir = '.deps\mame\object_emission',
    # Post-anchor route tail of the oracle instrument
    # (tools/mame_capture_enemy_actions.lua). Replaying the anchor state without
    # it is a different route: the player never turns, so the scroll origin and
    # the alien's approach diverge from the fixture.
    [string]$TailHoldAddress = 'FF83C1',
    [string]$TailHoldValue = '65',
    [string]$TailDirection = 'Left',
    [int]$TailDirectionOn = 4201,
    [int]$TailDirectionOff = 4210,
    [switch]$SkipSave
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$python = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'

if (-not (Test-Path $python)) { throw "Python runtime not found at $python" }
if (-not (Test-Path $mame)) { throw "MAME not found at $mame" }

$rawFull = Join-Path $projectRoot $RawDir
if (-not (Test-Path $rawFull)) { New-Item -ItemType Directory -Path $rawFull | Out-Null }
Get-ChildItem -Path $rawFull -File | Remove-Item -Force
Get-ChildItem -Path $projectRoot -File -Filter '*.log' | Remove-Item -Force -ErrorAction SilentlyContinue
# MAME stores states under a per-driver subdirectory of -state_directory
# (avspu/), so the saved .sta lands in captures\avspu\, not captures\.
$statePath = Join-Path $projectRoot ".deps\mame\captures\avspu\$State.sta"

function Invoke-Mame([string]$script, [bool]$debugger, [int]$seconds) {
    $args_ = @(
        'avspu'
        '-rompath', '.'
        '-video', 'none'
        '-sound', 'none'
        '-nothrottle'
        '-skip_gameinfo'
        '-seconds_to_run', "$seconds"
        '-cfg_directory', '.deps\mame\cfg_watchpoint'
        '-nvram_directory', '.deps\mame\nvram_debugoverlay'
        '-state_directory', '.deps\mame\captures'
    )
    if ($debugger) {
        $args_ += @('-debug', '-debugger', 'windows', '-log')
    }
    $args_ += @('-autoboot_script', ".\tools\$script")
    $consoleLog = Join-Path $rawFull 'mame_console.log'
    $stderrLog = Join-Path $rawFull 'mame_stderr.log'
    $proc = Start-Process -FilePath $mame -ArgumentList $args_ -WorkingDirectory $projectRoot `
        -NoNewWindow -Wait -PassThru -RedirectStandardOutput $consoleLog -RedirectStandardError $stderrLog
    if ($proc.ExitCode -ne 0) { throw "MAME ($script) exited with code $($proc.ExitCode)" }
}

# Phase 1: fast debugger-free cold boot that saves the frame-4200 anchor state.
if (-not $SkipSave -or -not (Test-Path $statePath)) {
    Write-Host "Phase 1: cold-boot save of $State ..."
    Push-Location $projectRoot
    try {
        $env:AVSP_REPLAY_STATE = $State
        Invoke-Mame 'mame_save_replay_state.lua' $false 120
    }
    finally {
        $env:AVSP_REPLAY_STATE = $null
        Pop-Location
    }
    if (-not (Test-Path $statePath)) { throw "Anchor state $statePath was not produced." }
} else {
    Write-Host "Phase 1: reusing existing anchor state $statePath"
}

# Phase 2: short instrumented capture of the two target frames from the state.
Write-Host "Phase 2: object-emission capture for frames $FrameA and $FrameB ..."
$envVars = @{
    'AVP_OE_STATE'      = $State
    'AVP_OE_STATE_FRAME'= "$StateFrame"
    'AVP_OE_FRAME_A'    = "$FrameA"
    'AVP_OE_FRAME_B'    = "$FrameB"
    'AVP_OE_OBJ_BASE'   = $ObjectListBase
    'AVP_OE_WORDS'      = "$(if ($WatchWords -gt 0) { $WatchWords } else { $Words })"
    'AVP_OE_BANK_REG'   = $BankSelectRegister
    'AVP_OE_ACTOR'      = $ActorBase
    'AVP_OE_RAWDIR'     = $RawDir
    'AVP_OE_TAIL_HOLD_ADDR'  = $TailHoldAddress
    'AVP_OE_TAIL_HOLD_VALUE' = $TailHoldValue
    'AVP_OE_TAIL_DIR'        = $TailDirection
    'AVP_OE_TAIL_DIR_ON'     = "$TailDirectionOn"
    'AVP_OE_TAIL_DIR_OFF'    = "$TailDirectionOff"
}
$previous = @{}
try {
    foreach ($name in $envVars.Keys) {
        $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $envVars[$name], 'Process')
    }
    Push-Location $projectRoot
    try {
        Invoke-Mame 'mame_watch_street_alien_object_emission.lua' $true 90
    }
    finally {
        Pop-Location
    }

    # Phase 3: analyze.
    $pyArgs = @(
        "tools\analyze_street_alien_object_emission.py"
        '--state', $State
        '--state-frame', "$StateFrame"
        '--frame-a', "$FrameA"
        '--frame-b', "$FrameB"
        '--object-list-base', $ObjectListBase
        '--word-count', "$Words"
        '--bank-select-register', $BankSelectRegister
        '--actor-base', $ActorBase
        '--raw-dir', $RawDir
    )
    & $python @pyArgs
    if ($LASTEXITCODE -ne 0) { throw "Analyzer exited with code $LASTEXITCODE" }
}
finally {
    foreach ($name in $envVars.Keys) {
        if ($null -eq $previous[$name]) {
            [Environment]::SetEnvironmentVariable($name, $null, 'Process')
        } else {
            [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
        }
    }
}
