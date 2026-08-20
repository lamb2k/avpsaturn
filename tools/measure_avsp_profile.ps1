# RP5 correction: stateless per-profile residency measurement.
#
# Builds one profile and writes ONE explicit measurement file. The
# residency ledger generator (gen_avsp_residency_budget.py) consumes
# exactly four of these files and never reads its own previous output,
# so the tracked ledger regenerates byte-identically from explicit
# inputs alone.
#
# Usage:
#   .\tools\measure_avsp_profile.ps1 -ProfileName street-test `
#       -BuildArguments @('-StreetTest') `
#       -OutputJson build\residency_profiles\street-test.json
param(
    [Parameter(Mandatory)][string]$ProfileName,
    [string[]]$BuildArguments = @(),
    [Parameter(Mandatory)][string]$OutputJson,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $projectRoot
try {
    # Hashtable splat: an array splat would pass '-StreetTest' style
    # strings positionally (observed binding to -JoEngineRoot).
    $splat = @{ SkipHostTests = $true }
    foreach ($argument in $BuildArguments) {
        $splat[$argument.TrimStart('-')] = $true
    }
    if ($PythonPath) { $splat['PythonPath'] = $PythonPath }
    & (Join-Path $projectRoot 'build.ps1') @splat
    if ($LASTEXITCODE -ne 0) {
        throw "Profile '$ProfileName' build failed with exit code $LASTEXITCODE."
    }

    $elf = Join-Path $projectRoot 'game.elf'
    if (-not (Test-Path -LiteralPath $elf)) {
        throw "Profile '$ProfileName' build produced no game.elf."
    }
    $nm = Join-Path $projectRoot '.deps\joengine\Compiler\WINDOWS\sh-elf\bin\nm.exe'
    $bendLine = & $nm --target=coff-sh $elf | Select-String ' __bend$' | Select-Object -Last 1
    if (-not $bendLine) {
        throw "Profile '$ProfileName': __bend not found in game.elf."
    }
    $bend = [Convert]::ToInt64(($bendLine.Line -split '\s+')[0], 16)
    $limit = 0x060C0000

    $stampPath = Join-Path $projectRoot 'build\last_compile_profile.txt'
    $stamp = if (Test-Path -LiteralPath $stampPath) {
        (Get-Content -LiteralPath $stampPath -Raw).Trim()
    } else { 'unknown' }

    # Carve constants straight from the tracked source.
    $mainSource = Get-Content -LiteralPath (Join-Path $projectRoot 'main.c') -Raw
    $carves = @{}
    foreach ($name in 'AVSP_CART_DRAM1_BYTES', 'AVSP_TILE_REGION_BYTES',
                      'AVSP_STRIPS_REGION_BYTES') {
        if ($mainSource -match "#define $name (0x[0-9A-Fa-f]+|\d+)") {
            $value = $Matches[1]
            if ($value -like '0x*') {
                $carves[$name] = [Convert]::ToInt64($value.Substring(2), 16)
            } else {
                $carves[$name] = [Convert]::ToInt64($value, 10)
            }
        }
    }

    $isoPath = Join-Path $projectRoot 'game.iso'
    $manifestPath = Join-Path $projectRoot 'build\hardware_release_manifest.txt'
    $record = [ordered]@{
        profile              = $ProfileName
        build_arguments      = @($BuildArguments)
        build_profile_stamp  = $stamp
        game_elf_sha256      = (Get-FileHash -LiteralPath $elf -Algorithm SHA256).Hash.ToLower()
        bend                 = ('0x{0:x8}' -f $bend)
        limit                = ('0x{0:x8}' -f $limit)
        headroom_bytes       = ($limit - $bend)
        carve_constants      = $carves
        iso_sha256           = if (Test-Path -LiteralPath $isoPath) {
                                   (Get-FileHash -LiteralPath $isoPath -Algorithm SHA256).Hash.ToLower()
                               } else { $null }
        hardware_manifest_sha256 = if (Test-Path -LiteralPath $manifestPath) {
                                   (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLower()
                               } else { $null }
        status               = 'MEASURED'
    }

    $outputPath = Join-Path $projectRoot $OutputJson
    $outputDir = Split-Path -Parent $outputPath
    if (-not (Test-Path -LiteralPath $outputDir)) {
        New-Item -ItemType Directory -Force $outputDir | Out-Null
    }
    $json = ($record | ConvertTo-Json -Depth 5) -replace "`r`n", "`n"
    [IO.File]::WriteAllText($outputPath, $json + "`n")
    Write-Host ("Measured {0}: __bend {1}, headroom {2} bytes -> {3}" -f `
        $ProfileName, $record.bend, $record.headroom_bytes, $OutputJson)
}
finally {
    Pop-Location
}
