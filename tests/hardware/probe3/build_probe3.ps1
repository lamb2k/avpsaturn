[CmdletBinding()]
param(
    [string]$PythonPath,
    [switch]$SkipHostTests
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
if (-not $PythonPath) {
    $python = Get-Command py.exe -ErrorAction Stop
    $PythonPath = $python.Source
}

& (Join-Path $root 'build.ps1') -Release -Clean -Probe3 `
    -PythonPath $PythonPath -SkipHostTests:$SkipHostTests
if ($LASTEXITCODE -ne 0) {
    throw "Probe 3 Saturn build failed with exit code $LASTEXITCODE."
}

$output = Join-Path $root 'build\hardware\probe3'
New-Item -ItemType Directory -Path $output -Force | Out-Null
$copies = @{
    'game.iso' = 'probe3.iso'
    'game.elf' = 'probe3.elf'
    'game.raw' = 'probe3.bin'
    'stage1_audio.wav' = 'probe3-track2.wav'
}
foreach ($sourceName in $copies.Keys) {
    $source = Join-Path $root $sourceName
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Probe 3 build output is missing: $source"
    }
    Copy-Item -LiteralPath $source -Destination `
        (Join-Path $output $copies[$sourceName]) -Force
}
$cueText = Get-Content -LiteralPath (Join-Path $root 'game.cue') -Raw
$cueText = $cueText.Replace('game.iso', 'probe3.iso').Replace(
    'stage1_audio.wav', 'probe3-track2.wav')
[IO.File]::WriteAllText((Join-Path $output 'probe3.cue'), $cueText,
                        [Text.Encoding]::ASCII)

$nm = Join-Path $root '.deps\joengine\Compiler\WINDOWS\sh-elf\bin\nm.exe'
$symbolLine = & $nm '--target=coff-sh' (Join-Path $root 'game.elf') |
    Where-Object { $_ -match '_avsp_probe3_telemetry$' } |
    Select-Object -First 1
if (-not $symbolLine) { throw 'Probe 3 telemetry symbol is missing from game.elf.' }
$telemetryAddress = '0x' + (($symbolLine -split '\s+')[0]).ToLowerInvariant()

function Artifact([string]$path) {
    $item = Get-Item -LiteralPath $path
    [ordered]@{
        file = $item.FullName.Substring($root.Length + 1).Replace('\', '/')
        bytes = $item.Length
        sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$schedulePath = Join-Path $PSScriptRoot 'probe3-schedule.json'
$tileManifestPath = Join-Path $output 'probe3-tile-manifest.json'
$profileStamp = Join-Path $root 'build\last_compile_profile.txt'
$manifest = [ordered]@{
    schema = 'avsp-probe3-manifest-v1'
    task = 'HW-01-PROBE-3-VDP1-BUDGET-PRETEST'
    profile = (Get-Content -LiteralPath $profileStamp -Raw).Trim()
    source_commit = (git -C $root rev-parse HEAD).Trim()
    preserved = [ordered]@{
        workflow_control_plane = 'edb02ee135fb1b30188ba5e089b3fdf126a90cff'
        accepted_source_combat_interface = '417ed808e10f0f255948b1e6ecf0223399509c74'
        approved_runtime_candidate = '82965ef80223a03937e0b527d16161ed68d874a0'
        approved_normalized_iso_sha256 = '4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef'
    }
    telemetry = [ordered]@{
        symbol = 'avsp_probe3_telemetry'
        work_ram_address = $telemetryAddress
        schema = 1
        fixed_size_bytes = 252
        overlay_during_measurement = $false
    }
    modes = @('PROBE3_REPRESENTATIVE', 'PROBE3_PEAK_909', 'PROBE3_OVERLOAD')
    physical_saturn = 'UNRUN'
    timing_claim = 'EMULATOR_SEMANTICS_ONLY'
    artifacts = [ordered]@{
        iso = Artifact (Join-Path $output 'probe3.iso')
        cue = Artifact (Join-Path $output 'probe3.cue')
        track2 = Artifact (Join-Path $output 'probe3-track2.wav')
        executable_elf = Artifact (Join-Path $output 'probe3.elf')
        executable_bin = Artifact (Join-Path $output 'probe3.bin')
        schedule = Artifact $schedulePath
        tile_archive_manifest = Artifact $tileManifestPath
        staged_game_bin = Artifact (Join-Path $root 'build\avsp_cd\GAME.BIN')
        staged_tile_archive = Artifact (Join-Path $root 'build\avsp_cd\SPR4\TILES.BIN')
    }
}
$manifestPath = Join-Path $output 'probe3-manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath `
    -Encoding ascii
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $output 'probe3-manifest.sha256'),
    "$manifestHash  probe3-manifest.json`r`n", [Text.Encoding]::ASCII)
Write-Host "Probe 3 package: $output"
Write-Host "Probe 3 manifest SHA-256: $manifestHash"
