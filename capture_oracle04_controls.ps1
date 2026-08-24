[CmdletBinding()]
param(
    [string]$PythonPath = 'C:\Users\lambd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [string]$RomRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest'
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot '.deps\mame\oracle04_controls'
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$cfgDir = Join-Path $projectRoot 'cfg'

if (-not (Test-Path -LiteralPath $mame)) { throw "MAME is missing: $mame" }
if (-not (Test-Path -LiteralPath $baseline)) { throw "NVRAM baseline is missing: $baseline" }
if (-not (Test-Path -LiteralPath $PythonPath)) { throw "Python is missing: $PythonPath" }
if (-not (Test-Path -LiteralPath (Join-Path $RomRoot 'avspu'))) {
    throw "The private avspu ROM directory is missing beneath: $RomRoot"
}
if (Test-Path -LiteralPath $rawRoot) {
    throw "Preserving existing ORACLE-04 raw evidence; move it explicitly before recapture: $rawRoot"
}

& $mame '-rompath' $RomRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }

New-Item -ItemType Directory -Force -Path $rawRoot | Out-Null
$manifest = [ordered]@{
    schema = 1
    mame = [ordered]@{
        version = (& $mame -version).Trim()
        sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    runs = @()
    roms = @()
}
Get-ChildItem -LiteralPath (Join-Path $RomRoot 'avspu') -File | Sort-Object Name | ForEach-Object {
    $manifest.roms += [ordered]@{
        name = $_.Name
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

function Invoke-ControlRun([string]$Name, [int]$PerturbFrame) {
    $runRoot = Join-Path $rawRoot $Name
    New-Item -ItemType Directory -Force -Path $runRoot, (Join-Path $runRoot 'frames') | Out-Null
    if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    foreach ($stale in @((Join-Path $cfgDir 'avspu.cfg'), (Join-Path $cfgDir 'default.cfg'))) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }
    $env:AVSP_ORACLE04_ROOT = $runRoot.Replace('\', '/')
    $env:AVSP_ORACLE04_PERTURB_FRAME = [string]$PerturbFrame
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' $RomRoot '-video' 'none' '-sound' 'none' '-nothrottle' `
            '-skip_gameinfo' '-snapshot_directory' '.deps\mame' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_oracle04_controls.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $Name capture failed: $LASTEXITCODE" }
    }
    finally {
        Remove-Item Env:\AVSP_ORACLE04_ROOT -ErrorAction SilentlyContinue
        Remove-Item Env:\AVSP_ORACLE04_PERTURB_FRAME -ErrorAction SilentlyContinue
        Pop-Location
    }
    $manifest.runs += [ordered]@{
        name = $Name
        perturb_frame = $PerturbFrame
        samples_sha256 = (Get-FileHash -LiteralPath (Join-Path $runRoot 'samples.tsv') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

Invoke-ControlRun 'cold_run_1' 0
Invoke-ControlRun 'cold_run_2' 0
Invoke-ControlRun 'one_frame_perturbation' 2525
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8

& $PythonPath (Join-Path $projectRoot 'tools\analyze_oracle04_controls.py') '--generate'
if ($LASTEXITCODE -ne 0) { throw "ORACLE-04 analysis failed: $LASTEXITCODE" }
