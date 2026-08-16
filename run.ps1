[CmdletBinding()]
param(
    [string]$EmulatorPath,
    [string]$JoEngineRoot
)

$ErrorActionPreference = 'Stop'
if (-not $JoEngineRoot) {
    $JoEngineRoot = Join-Path $PSScriptRoot '.deps\joengine'
}
$cue = Join-Path $PSScriptRoot 'game.cue'
$iso = Join-Path $PSScriptRoot 'game.iso'
if (-not (Test-Path -LiteralPath $cue) -or -not (Test-Path -LiteralPath $iso)) {
    throw 'game.cue or game.iso is missing. Run .\build.ps1 first.'
}

if (-not $EmulatorPath) {
    $candidates = @()
    $downloadedYabaRoot = Join-Path $PSScriptRoot '.deps\emulators'
    if (Test-Path -LiteralPath $downloadedYabaRoot) {
        $downloadedYaba = Get-ChildItem -LiteralPath $downloadedYabaRoot `
            -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($downloadedYaba) {
            $candidates += $downloadedYaba.FullName
        }
    }
    $candidates += @(
        (Join-Path $JoEngineRoot 'Emulators\kronos\kronos.exe'),
        (Join-Path $JoEngineRoot 'Emulators\yabause\yabause.exe'),
        (Join-Path $JoEngineRoot 'Emulators\YabaSanshiro\yabasanshiro.exe'),
        (Join-Path $JoEngineRoot 'Emulators\mednafen\mednafen.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            $EmulatorPath = $candidate
            break
        }
    }
}
if (-not $EmulatorPath -or -not (Test-Path -LiteralPath $EmulatorPath)) {
    throw 'No Saturn emulator was found. Pass its executable with -EmulatorPath.'
}

$emulatorName = [IO.Path]::GetFileNameWithoutExtension($EmulatorPath).ToLowerInvariant()
if ($emulatorName -eq 'kronos') {
    $settingsPath = Join-Path $env:LOCALAPPDATA 'kronos\kronos.ini'
    if (Test-Path -LiteralPath $settingsPath) {
        $settings = Get-Content -LiteralPath $settingsPath -Raw
        $kronosValues = [ordered]@{
            'General\EnableEmulatedBios' = 'true'
            'General\CdRom' = '1'
            'General\CdRomISO' = $cue.Replace('\', '/')
            'Cartridge\Type' = '7'
            'autostart' = 'true'
        }
        foreach ($entry in $kronosValues.GetEnumerator()) {
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
    }
}
elseif ($emulatorName -eq 'yabasanshiro') {
    $settingsPath = Join-Path $env:APPDATA 'YabaSanshiro\yabause.ini'
    if (-not (Test-Path -LiteralPath $settingsPath)) {
        throw 'Run Yaba Sanshiro once to complete its first-run setup, then rerun this launcher.'
    }
    $settings = Get-Content -LiteralPath $settingsPath -Raw
    $yabaValues = [ordered]@{
        'General\CdRom' = '1'
        'General\CdRomISO' = $iso.Replace('\', '/')
        # Yaba Sanshiro cartridge type 7 is 32 Mbit DRAM, or 4 MB.
        'Cartridge\Type' = '7'
        'autostart' = 'true'
    }
    foreach ($entry in $yabaValues.GetEnumerator()) {
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
}
elseif ($emulatorName -eq 'yabause') {
    $settingsRoot = Join-Path $env:LOCALAPPDATA 'yabause'
    $settingsPath = Join-Path $settingsRoot 'yabause.ini'
    if (-not (Test-Path -LiteralPath $settingsRoot)) {
        New-Item -ItemType Directory -Path $settingsRoot | Out-Null
    }
    $settings = if (Test-Path -LiteralPath $settingsPath) {
        Get-Content -LiteralPath $settingsPath -Raw
    }
    else {
        '[0.9.14]' + [Environment]::NewLine
    }
    if ($settings -match '(?m)^Cartridge\\Type=') {
        $settings = $settings -replace '(?m)^Cartridge\\Type=.*$', 'Cartridge\Type=7'
    }
    else {
        $settings = $settings.TrimEnd() + [Environment]::NewLine +
            'Cartridge\Type=7' + [Environment]::NewLine
    }
    Set-Content -LiteralPath $settingsPath -Value $settings -NoNewline
}
$quotedCue = '"' + $cue + '"'
$arguments = switch -Regex ($emulatorName) {
    '^kronos$' { @('-i', $quotedCue); break }
    '^yabasanshiro$' { @('-nb', '-ns', '-a', '-i', $quotedCue); break }
    '^yabause$' { @('-a', '-i', $quotedCue); break }
    default { @($quotedCue) }
}
Start-Process -FilePath $EmulatorPath -ArgumentList $arguments -WorkingDirectory $PSScriptRoot
