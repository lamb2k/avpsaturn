[CmdletBinding()]
param(
    [int]$Frames = 600
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$watchRoot = Join-Path $projectRoot '.deps\mame\watchpoints'
New-Item -ItemType Directory -Force -Path $watchRoot | Out-Null

$priorState = $env:AVSP_WATCH_STATE
$priorLog = $env:AVSP_WATCH_LOG
$priorFrames = $env:AVSP_WATCH_FRAMES
try {
    $env:AVSP_WATCH_STATE = 'avspu_stage1_debug_hitboxes'
    $env:AVSP_WATCH_LOG = '.deps/mame/watchpoints/actor_writers.log'
    $env:AVSP_WATCH_FRAMES = [string]$Frames
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-nothrottle' '-skip_gameinfo' '-debug' '-debugger' 'windows' `
            '-log' '-cfg_directory' '.deps\mame\cfg_watchpoint' `
            '-nvram_directory' '.deps\mame\nvram_debugoverlay' `
            '-state_directory' '.deps\mame\captures' `
            '-autoboot_script' '.\tools\mame_watch_actor_writers.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Stock MAME watchpoint capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:AVSP_WATCH_STATE = $priorState
    $env:AVSP_WATCH_LOG = $priorLog
    $env:AVSP_WATCH_FRAMES = $priorFrames
}

$python = Join-Path $env:USERPROFILE `
    '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python (Join-Path $projectRoot 'tools\analyze_watchpoint_log.py')
if ($LASTEXITCODE -ne 0) {
    throw "The stock-MAME watchpoint analyzer failed with exit code $LASTEXITCODE."
}
