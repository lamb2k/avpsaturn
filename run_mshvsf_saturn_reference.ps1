[CmdletBinding()]
param(
    [string]$EmulatorPath,
    [string]$PlayRecordDirectory,
    [switch]$EnableMcpDebugServer,
    [switch]$NoLaunch
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$saturnRoot = Join-Path $projectRoot `
    'Marvel Super Heroes vs. Street Fighter\Saturn'
$sourceCue = Join-Path $saturnRoot 'Marvel Super Heroes vs. Street Fighter.cue'
$sourceBin = Join-Path $saturnRoot 'Marvel Super Heroes vs. Street Fighter.bin'

if (-not (Test-Path -LiteralPath $sourceCue) -or
    -not (Test-Path -LiteralPath $sourceBin)) {
    throw 'The authorized MSHvSF Saturn cue/bin reference is incomplete.'
}

if (-not $EmulatorPath) {
    $candidate = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.deps\emulators') `
        -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($candidate) {
        $EmulatorPath = $candidate.FullName
    }
}
if (-not $EmulatorPath -or -not (Test-Path -LiteralPath $EmulatorPath)) {
    throw 'Pinned Yaba Sanshiro was not found. Run .\setup_emulator.ps1 first.'
}

$tempRoot = Join-Path ([IO.Path]::GetTempPath()) 'MSHvSFReferenceLane'
if (-not (Test-Path -LiteralPath $tempRoot)) {
    New-Item -ItemType Directory -Path $tempRoot | Out-Null
}
$launchCue = Join-Path $tempRoot 'mshvsf.yaba.cue'
$resolvedBin = (Resolve-Path -LiteralPath $sourceBin).Path
$cueLines = Get-Content -LiteralPath $sourceCue
$cueLines[0] = 'FILE "{0}" BINARY' -f $resolvedBin
Set-Content -LiteralPath $launchCue -Value $cueLines -Encoding ASCII

$settingsPath = Join-Path $env:APPDATA 'YabaSanshiro\yabause.ini'
if (-not (Test-Path -LiteralPath $settingsPath)) {
    throw 'Run Yaba Sanshiro once to complete first-run setup, then retry.'
}
$settings = Get-Content -LiteralPath $settingsPath -Raw
$values = [ordered]@{
    'General\CdRom' = '1'
    'General\CdRomISO' = $launchCue.Replace('\', '/')
    'Cartridge\Type' = '7'
    'autostart' = 'false'
}
if ($EnableMcpDebugServer) {
    $values['Debug\McpServerEnabled'] = 'true'
}
foreach ($entry in $values.GetEnumerator()) {
    $pattern = '(?m)^' + [regex]::Escape($entry.Key) + '=.*$'
    $line = $entry.Key + '=' + $entry.Value
    if ($settings -match $pattern) {
        $settings = $settings -replace $pattern, $line
    }
    else {
        $settings = $settings.TrimEnd() + [Environment]::NewLine +
            $line + [Environment]::NewLine
    }
}
Set-Content -LiteralPath $settingsPath -Value $settings -NoNewline

$cueHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $launchCue).Hash
Write-Host "Temporary corrected cue: $launchCue"
Write-Host "Temporary cue SHA-256: $cueHash"
Write-Host 'Cartridge: 32 Mbit (4 MB) DRAM'
if ($EnableMcpDebugServer) {
    Write-Host 'MCP debug server: enabled on the emulator-configured localhost port'
}

if ($NoLaunch) {
    return
}

$quotedCue = '"' + $launchCue + '"'
$arguments = @('-nb', '-a', '-i', $quotedCue)
if ($PlayRecordDirectory) {
    $resolvedPlayRecord = (Resolve-Path -LiteralPath $PlayRecordDirectory).Path
    $arguments += @('-p', ('"' + $resolvedPlayRecord + '"'))
    Write-Host "Deterministic play record: $resolvedPlayRecord"
}
$process = Start-Process -FilePath $EmulatorPath `
    -ArgumentList $arguments `
    -WorkingDirectory $projectRoot -PassThru
Write-Host "Started Yaba Sanshiro PID $($process.Id)."
