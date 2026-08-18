[CmdletBinding()]
param(
    [string]$PythonPath,
    [string]$PlayRecordDirectory =
        '.\.deps\mshvsf_saturn_playrecord\saturn_ryu_first_pass_b',
    [string]$OutputRoot = '.\.deps\mshvsf_saturn_state',
    [string[]]$Anchor = @(
        'idle:3540',
        'normal_active:3828',
        'impact:3840',
        'recovery:3900'
    )
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if (-not $PythonPath) {
    $PythonPath = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
}
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python runtime not found: $PythonPath"
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Refusing to overwrite existing raw capture: $OutputRoot"
}

$running = @(Get-Process -Name 'yabasanshiro' -ErrorAction SilentlyContinue)
if ($running.Count -ne 0) {
    throw 'Close existing Yaba Sanshiro processes before starting this capture.'
}

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

$captureArguments = @(
    '.\tools\capture_mshvsf_saturn_mcp.py',
    '--output-root', $OutputRoot,
    '--resume-after-final'
)
foreach ($item in $Anchor) {
    $captureArguments += @('--anchor', $item)
}
& $PythonPath @captureArguments
if ($LASTEXITCODE -ne 0) {
    throw 'Synchronized Saturn memory capture failed; preserve the raw directory.'
}

& $PythonPath .\tools\analyze_mshvsf_saturn_memory.py `
    --capture-root $OutputRoot
if ($LASTEXITCODE -ne 0) {
    throw 'Saturn memory analysis failed.'
}

Write-Host "Raw Saturn memory evidence: $((Resolve-Path -LiteralPath $OutputRoot).Path)"
Write-Host 'Tracked report: data\mshvsf_saturn_runtime_memory.json'
