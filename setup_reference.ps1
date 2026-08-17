[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$version = '0.289'
$archiveName = 'mame0289b_x64.exe'
$expectedSha256 = 'A1AA7912168C9D1B05E611906BC21B8B9BE3935822AEAD36D12A1DA363150B7D'
$downloadUri = 'https://github.com/mamedev/mame/releases/download/mame0289/mame0289b_x64.exe'
$dependencyRoot = Join-Path $PSScriptRoot '.deps\mame'
$archivePath = Join-Path $dependencyRoot $archiveName
$installRoot = Join-Path $dependencyRoot 'mame0289'
$mamePath = Join-Path $installRoot 'mame.exe'

if (Test-Path -LiteralPath $mamePath) {
    Write-Host "MAME $version reference runtime is already installed: $mamePath"
    return
}

New-Item -ItemType Directory -Force -Path $dependencyRoot | Out-Null
if (Test-Path -LiteralPath $archivePath) {
    $existingSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash
    if ($existingSha256 -ne $expectedSha256) {
        Remove-Item -LiteralPath $archivePath -Force
    }
}
if (-not (Test-Path -LiteralPath $archivePath)) {
    Write-Host "Downloading official MAME $version Windows x64 package..."
    Invoke-WebRequest -Uri $downloadUri -OutFile $archivePath
}

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash
if ($actualSha256 -ne $expectedSha256) {
    throw "MAME archive hash mismatch. Expected $expectedSha256 but found $actualSha256."
}

New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
& $archivePath '-y' "-o$installRoot"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $mamePath)) {
    throw "MAME extraction failed with exit code $LASTEXITCODE."
}

Write-Host "Installed verified MAME $version reference runtime: $mamePath"
