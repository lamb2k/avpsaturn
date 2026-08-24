[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$feedbackRoot = Join-Path $root 'build\feedback'
$destination = Join-Path $feedbackRoot 'HW-01-PROBE-3-VDP1-BUDGET-PRETEST'
if (Test-Path -LiteralPath $destination) {
    $resolvedRoot = [IO.Path]::GetFullPath($feedbackRoot).TrimEnd('\') + '\'
    $resolvedDestination = [IO.Path]::GetFullPath($destination)
    if (-not $resolvedDestination.StartsWith($resolvedRoot,
            [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to replace an operator package outside build/feedback.'
    }
    Remove-Item -LiteralPath $resolvedDestination -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null

function Copy-Required {
    param([string]$Source, [string]$TargetName)
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "Missing operator artifact: $Source" }
    Copy-Item -LiteralPath $Source -Destination (Join-Path $destination $TargetName) -Force
}

$probe = Join-Path $root 'build\hardware\probe3'
@('probe3.iso', 'probe3.cue', 'probe3.elf', 'probe3.bin', 'probe3-track2.wav',
  'probe3-manifest.json', 'probe3-manifest.sha256', 'probe3-tile-manifest.json') |
    ForEach-Object { Copy-Required (Join-Path $probe $_) $_ }

Copy-Required (Join-Path $PSScriptRoot 'probe3-schedule.json') 'probe3-schedule.json'
Copy-Required (Join-Path $PSScriptRoot 'generated\probe3_schedule.h') 'probe3_schedule.h'
Copy-Required (Join-Path $PSScriptRoot 'TELEMETRY_LAYOUT.md') 'TELEMETRY_LAYOUT.md'
Copy-Required (Join-Path $PSScriptRoot 'operator\README.md') 'README.md'
Copy-Required (Join-Path $PSScriptRoot 'operator\HARDWARE_SETUP_TEMPLATE.md') 'HARDWARE_SETUP_TEMPLATE.md'
Copy-Required (Join-Path $PSScriptRoot 'operator\PHYSICAL_RESULT_TEMPLATE.md') 'PHYSICAL_RESULT_TEMPLATE.md'
Copy-Required (Join-Path $PSScriptRoot 'operator\physical_preflight.ps1') 'physical_preflight.ps1'

Copy-Required (Join-Path $root 'game.iso') 'integrate-03-approved.iso'
Copy-Required (Join-Path $root 'game.cue') 'integrate-03-approved.cue'
Copy-Required (Join-Path $root 'stage1_audio.wav') 'integrate-03-approved-track2.wav'
Copy-Required (Join-Path $root 'build\hardware_release_manifest.txt') 'integrate-03-hardware-release-manifest.txt'

$emulatorSource = Join-Path $probe 'emulator'
if (-not (Test-Path -LiteralPath $emulatorSource -PathType Container)) {
    throw 'Missing paired-emulator evidence.'
}
Copy-Item -LiteralPath $emulatorSource -Destination (Join-Path $destination 'emulator') -Recurse -Force

$preflight = & (Join-Path $PSScriptRoot 'operator\physical_preflight.ps1')
$preflight | Set-Content -LiteralPath (Join-Path $destination 'physical-preflight.json') -Encoding UTF8

$hashLines = Get-ChildItem -LiteralPath $destination -File -Recurse |
    Where-Object { $_.Name -ne 'HASHES.sha256' } |
    Sort-Object FullName | ForEach-Object {
        $relative = $_.FullName.Substring($destination.Length + 1).Replace('\', '/')
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $relative"
    }
$hashLines | Set-Content -LiteralPath (Join-Path $destination 'HASHES.sha256') -Encoding ASCII

Write-Host "Prepared ignored HW-01 operator package: $destination"
Write-Host "Files: $($hashLines.Count)"
