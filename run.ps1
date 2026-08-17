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
$launchImage = $cue
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
    # Yaba Sanshiro resolves relative FILE entries in a cue against stale
    # process state on this Windows build. Give its parser an emulator-only
    # cue whose track paths are absolute while retaining the portable cue next
    # to the ISO for discs and optical-drive emulators.
    $stageAudio = Join-Path $PSScriptRoot 'stage1_audio.wav'
    if (-not (Test-Path -LiteralPath $stageAudio)) {
        throw 'stage1_audio.wav is missing. Run .\build.ps1 first.'
    }
    $yabaCueRoot = Join-Path ([IO.Path]::GetTempPath()) `
        'AvPSaturnCapabilityTest'
    if (-not (Test-Path -LiteralPath $yabaCueRoot)) {
        New-Item -ItemType Directory -Path $yabaCueRoot | Out-Null
    }
    $launchImage = Join-Path $yabaCueRoot 'game.yaba.cue'
    $resolvedIso = (Resolve-Path -LiteralPath $iso).Path
    $resolvedAudio = (Resolve-Path -LiteralPath $stageAudio).Path
    $yabaCueLines = @(
        ('FILE "{0}" BINARY' -f $resolvedIso),
        '  TRACK 01 MODE1/2048',
        '    INDEX 01 00:00:00',
        '    POSTGAP 00:02:00',
        ('FILE "{0}" WAVE' -f $resolvedAudio),
        '  TRACK 02 AUDIO',
        '    PREGAP 00:02:00',
        '    INDEX 01 00:00:00'
    )
    Set-Content -LiteralPath $launchImage -Value $yabaCueLines -Encoding ASCII

    $settingsPath = Join-Path $env:APPDATA 'YabaSanshiro\yabause.ini'
    if (-not (Test-Path -LiteralPath $settingsPath)) {
        throw 'Run Yaba Sanshiro once to complete its first-run setup, then rerun this launcher.'
    }
    $settings = Get-Content -LiteralPath $settingsPath -Raw
    $yabaValues = [ordered]@{
        'General\CdRom' = '1'
        'General\CdRomISO' = $launchImage.Replace('\', '/')
        # Yaba Sanshiro cartridge type 7 is 32 Mbit DRAM, or 4 MB.
        'Cartridge\Type' = '7'
        # Keep the persistent config from starting a remembered image. The
        # exact cue for this checkout is supplied once on the command line.
        'autostart' = 'false'
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
$quotedLaunchImage = '"' + $launchImage + '"'
$arguments = switch -Regex ($emulatorName) {
    '^kronos$' { @('-i', $quotedLaunchImage); break }
    # Config autostart is disabled above, so this is the single launch path.
    '^yabasanshiro$' { @('-nb', '-a', '-i', $quotedLaunchImage); break }
    '^yabause$' { @('-a', '-i', $quotedLaunchImage); break }
    default { @($quotedLaunchImage) }
}
Start-Process -FilePath $EmulatorPath -ArgumentList $arguments -WorkingDirectory $PSScriptRoot
