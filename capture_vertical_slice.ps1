[CmdletBinding()]
param(
    [string]$PythonPath = 'C:\Users\lambd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [switch]$KeepRaw
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$rawRoot = Join-Path $projectRoot '.deps\mame\vertical_slice'
$baseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline'
$liveNvram = Join-Path $projectRoot 'nvram\avspu'
$config = Join-Path $projectRoot 'cfg\avspu.cfg'

if (-not (Test-Path -LiteralPath $mame)) { throw "MAME is missing: $mame" }
if (-not (Test-Path -LiteralPath $baseline)) { throw "NVRAM baseline is missing: $baseline" }
if (-not (Test-Path -LiteralPath $PythonPath)) { throw "Python is missing: $PythonPath" }

& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }

function Assert-PrivateChild([string]$Path, [string]$Parent) {
    $resolvedParent = (Resolve-Path -LiteralPath $Parent).Path
    if (Test-Path -LiteralPath $Path) {
        $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
        if (-not $resolvedPath.StartsWith($resolvedParent + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove non-private path: $resolvedPath"
        }
    }
}

if (Test-Path -LiteralPath $rawRoot) {
    if (-not $KeepRaw) {
        Assert-PrivateChild $rawRoot (Join-Path $projectRoot '.deps\mame')
        Remove-Item -LiteralPath $rawRoot -Recurse -Force
    }
    else { throw "Raw vertical-slice root exists and -KeepRaw was supplied: $rawRoot" }
}
New-Item -ItemType Directory -Force -Path $rawRoot | Out-Null

$inputManifest = [ordered]@{
    schema = 1
    mame = [ordered]@{ version = (& $mame -version).Trim(); sha256 = (Get-FileHash -LiteralPath $mame -Algorithm SHA256).Hash.ToLowerInvariant() }
    config_sha256 = if (Test-Path -LiteralPath $config) { (Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash.ToLowerInvariant() } else { 'absent' }
    nvram_baseline_sha256 = (Get-FileHash -LiteralPath (Join-Path $baseline 'eeprom') -Algorithm SHA256).Hash.ToLowerInvariant()
    runs = @()
    roms = @()
}
Get-ChildItem -LiteralPath (Join-Path $projectRoot 'avspu') -File | Sort-Object Name | ForEach-Object {
    $inputManifest.roms += [ordered]@{ name = $_.Name; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
}

function Invoke-VerticalSliceRun([string]$Name, [int]$PerturbFrame) {
    $runRoot = Join-Path $rawRoot $Name
    New-Item -ItemType Directory -Force -Path $runRoot, (Join-Path $runRoot 'frames'),
        (Join-Path $runRoot 'objram'), (Join-Path $runRoot 'cps_a'), (Join-Path $runRoot 'cps_b'),
        (Join-Path $runRoot 'palette') | Out-Null
    if (Test-Path -LiteralPath $liveNvram) { Remove-Item -LiteralPath $liveNvram -Recurse -Force }
    Copy-Item -LiteralPath $baseline -Destination $liveNvram -Recurse
    $env:AVSP_VSLICE_CAPTURE_ROOT = (Resolve-Path -LiteralPath $runRoot).Path.Replace('\', '/')
    $env:AVSP_VSLICE_FIRST = '4080'
    $env:AVSP_VSLICE_LAST = '5469'
    $env:AVSP_VSLICE_PERTURB_FRAME = [string]$PerturbFrame
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' '-nothrottle' '-skip_gameinfo' '-debug' '-autoboot_delay' '0' '-autoboot_script' '.\tools\mame_capture_vertical_slice.lua'
        if ($LASTEXITCODE -ne 0) { throw "MAME $Name capture failed: $LASTEXITCODE" }
    }
    finally { Pop-Location }
    $inputManifest.runs += [ordered]@{ name = $Name; perturb_frame = $PerturbFrame; samples_sha256 = (Get-FileHash -LiteralPath (Join-Path $runRoot 'samples.tsv') -Algorithm SHA256).Hash.ToLowerInvariant() }
}

Invoke-VerticalSliceRun 'cold_run_1' 0
Invoke-VerticalSliceRun 'cold_run_2' 0
Invoke-VerticalSliceRun 'one_frame_perturbation' 4510
$inputManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $rawRoot 'input_manifest.json') -Encoding utf8

& $PythonPath (Join-Path $projectRoot 'tools\verify_avsp_vertical_slice_oracle.py') '--generate'
if ($LASTEXITCODE -ne 0) { throw "Oracle verifier failed: $LASTEXITCODE" }
