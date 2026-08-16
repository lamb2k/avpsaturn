[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$packageName = 'yabasanshiro-1.20.37-2986eb'
$downloadUrl = 'https://d1t36rsydvwkyk.cloudfront.net/yabasanshiro-1.20.37-2986eb.zip'
$expectedSha256 = 'C34FF6766633F319BDB993481E4B82C9297D4E2A1FF1FDA73A3CFF4D380C2F5C'
$emulatorRoot = Join-Path $PSScriptRoot '.deps\emulators'
$archivePath = Join-Path $emulatorRoot ($packageName + '.zip')
$installRoot = Join-Path $emulatorRoot $packageName

$installedExe = Get-ChildItem -LiteralPath $installRoot -Filter 'yabasanshiro.exe' `
    -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($installedExe) {
    Write-Host "Yaba Sanshiro is ready at $($installedExe.FullName)"
    return
}

if (-not (Test-Path -LiteralPath $emulatorRoot)) {
    New-Item -ItemType Directory -Path $emulatorRoot | Out-Null
}

if (-not (Test-Path -LiteralPath $archivePath)) {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath
}

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash
if ($actualSha256 -ne $expectedSha256) {
    throw "Yaba Sanshiro archive hash mismatch. Expected $expectedSha256 but found $actualSha256."
}

Expand-Archive -LiteralPath $archivePath -DestinationPath $installRoot -Force
$installedExe = Get-ChildItem -LiteralPath $installRoot -Filter 'yabasanshiro.exe' `
    -File -Recurse | Select-Object -First 1
if (-not $installedExe) {
    throw 'The verified emulator archive did not contain yabasanshiro.exe.'
}

Write-Host "Yaba Sanshiro is ready at $($installedExe.FullName)"
