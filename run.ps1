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
    $candidates = @(
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
        if ($settings -match '(?m)^Cartridge\\Type=') {
            $settings = $settings -replace '(?m)^Cartridge\\Type=.*$', 'Cartridge\Type=7'
        }
        else {
            $settings = $settings.TrimEnd() + [Environment]::NewLine +
                'Cartridge\Type=7' + [Environment]::NewLine
        }
        Set-Content -LiteralPath $settingsPath -Value $settings -NoNewline
    }
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
$arguments = switch -Regex ($emulatorName) {
    '^kronos$' { @('-i', $cue); break }
    '^(yabasanshiro|yabause)$' { @('-a', '-i', $cue); break }
    default { @($cue) }
}
Start-Process -FilePath $EmulatorPath -ArgumentList $arguments -WorkingDirectory $PSScriptRoot
