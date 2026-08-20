<#
.SYNOPSIS
Re-read the official port's VDP2 priority registers through every SH-2
view of the register block.

The tracked capture reports that block as 288 zero bytes and the handoff
records that as an instrument limit. This wrapper replays the same
deterministic play record, pauses on the same anchors, and reads the
block through both the cached and the uncached views with a colour-RAM
positive control, so an all-zero result is reported as an unreadable
instrument rather than as a measurement of zero priorities.

It writes one JSON report per anchor and stops the emulator afterwards.
#>
[CmdletBinding()]
param(
    [string]$PythonPath,
    [string]$PlayRecordDirectory =
        '.\.deps\mshvsf_saturn_playrecord\saturn_ryu_first_pass_b',
    [string]$OutputRoot = '.\data\mshvsf_vdp2_priority',
    [string[]]$Anchor = @(
        'idle:3540',
        'normal_active:3828',
        'impact:3840',
        'recovery:3900'
    )
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not $PythonPath) {
    $PythonPath = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
}
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python runtime not found: $PythonPath"
}

$running = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue)
if ($running.Count -ne 0) {
    throw 'Close existing Yaba Sanshiro processes before starting this probe.'
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

& .\run_mshvsf_saturn_reference.ps1 `
    -PlayRecordDirectory $PlayRecordDirectory `
    -EnableMcpDebugServer

$ready = $false
for ($attempt = 0; $attempt -lt 80; $attempt++) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync('127.0.0.1', 9640)
        if ($task.Wait(250) -and $client.Connected) {
            $ready = $true
            break
        }
    }
    finally {
        $client.Dispose()
    }
    Start-Sleep -Milliseconds 250
}
if (-not $ready) {
    throw 'Yaba Sanshiro MCP debug server did not listen on localhost:9640.'
}

try {
    foreach ($item in $Anchor) {
        $parts = $item.Split(':')
        $label = $parts[0]
        $frame = [int]$parts[1]
        $output = Join-Path $OutputRoot "$label.json"
        & $PythonPath .\tools\probe_mshvsf_vdp2_priority.py `
            --frame $frame --label $label --output $output
        if ($LASTEXITCODE -eq 3) {
            throw ("Memory reader control failed at anchor {0}; the run " +
                   'proves nothing about VDP2.') -f $label
        }
        if ($LASTEXITCODE -ne 0) {
            throw "VDP2 priority probe failed at anchor $label."
        }
    }
}
finally {
    Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
}

Write-Host "VDP2 priority probe reports written under $OutputRoot"
