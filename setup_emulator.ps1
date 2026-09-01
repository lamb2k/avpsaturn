[CmdletBinding()]
param(
    [ValidateSet('DebugRigMcp', 'DebugRigMcpD776', 'Aug10')]
    [string]$Package = 'DebugRigMcp'
)

$ErrorActionPreference = 'Stop'
$packages = @{
    DebugRigMcp = @{
        Name = 'yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34'
        DownloadUrl = $null
        ArchiveSha256 = '0D6B44AFAE0F99A76F5BA3090A3CE307137C9FC305FFA67D0C0A04BF040DD34B'
        ExeSha256 = 'DA2FFB341532F10808D8F9659C875A96CBC29EBC10A454426415059C7CEF8746'
        Identity = 'owner-built debug rig with framebuffer_screenshot/framebuffer_burst/save_state'
    }
    DebugRigMcpD776 = @{
        Name = 'yabasanshiro-1.20.37-2986eb-debug-rig-mcp-d7767591'
        DownloadUrl = $null
        ArchiveSha256 = '6F157F15DA4D01CCA9EF044D32352B8E6D3CF6B71A44AD3303AAEB9939015864'
        ExeSha256 = 'D77675912421A7435D02D844625A6EF68BA0E55EF17C9845F08651EB98F54B45'
        Identity = 'owner-built framebuffer-only debug-rig control'
    }
    Aug10 = @{
        Name = 'yabasanshiro-1.20.37-2986eb'
        DownloadUrl = 'https://d1t36rsydvwkyk.cloudfront.net/yabasanshiro-1.20.37-2986eb.zip'
        ArchiveSha256 = 'C34FF6766633F319BDB993481E4B82C9297D4E2A1FF1FDA73A3CFF4D380C2F5C'
        ExeSha256 = '016112708FC77EC53B8A36C4EF52E300A78B3FB079E815F60B1A51FA1661999C'
        Identity = 'Aug-10 clean package pin'
    }
}
$selected = $packages[$Package]
$packageName = $selected.Name
$emulatorRoot = Join-Path $PSScriptRoot '.deps\emulators'
$archivePath = Join-Path $emulatorRoot ($packageName + '.zip')
$installRoot = Join-Path $emulatorRoot $packageName

function Confirm-EmulatorExe([IO.FileInfo]$Executable) {
    $actualExeSha256 = (Get-FileHash -Algorithm SHA256 `
        -LiteralPath $Executable.FullName).Hash
    if ($actualExeSha256 -ne $selected.ExeSha256) {
        throw "Yaba Sanshiro EXE hash mismatch. Expected $($selected.ExeSha256) but found $actualExeSha256."
    }
    Write-Host "Yaba Sanshiro $($selected.Identity) is ready at $($Executable.FullName)"
}

$installedExe = Get-ChildItem -LiteralPath $installRoot `
    -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($installedExe) {
    Confirm-EmulatorExe $installedExe
    return
}

if (-not (Test-Path -LiteralPath $emulatorRoot)) {
    New-Item -ItemType Directory -Path $emulatorRoot | Out-Null
}

if (-not (Test-Path -LiteralPath $archivePath)) {
    if (-not $selected.DownloadUrl) {
        throw "The owner-built debug-rig archive is missing at $archivePath. Repackage the smoke-tested owner EXE under docs/EMULATOR_MCP_CAPTURE.md."
    }
    Invoke-WebRequest -Uri $selected.DownloadUrl -OutFile $archivePath
}

$actualArchiveSha256 = (Get-FileHash -Algorithm SHA256 `
    -LiteralPath $archivePath).Hash
if ($actualArchiveSha256 -ne $selected.ArchiveSha256) {
    throw "Yaba Sanshiro archive hash mismatch. Expected $($selected.ArchiveSha256) but found $actualArchiveSha256."
}

Expand-Archive -LiteralPath $archivePath -DestinationPath $installRoot -Force
$installedExe = Get-ChildItem -LiteralPath $installRoot `
    -Filter 'yabasanshiro.exe' -File -Recurse | Select-Object -First 1
if (-not $installedExe) {
    throw 'The verified emulator archive did not contain yabasanshiro.exe.'
}
Confirm-EmulatorExe $installedExe
