[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Archive,
    [string]$PythonPath = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$verify = Join-Path $PSScriptRoot 'verify_yabasanshiro_1_20_37_scanout.py'
$manifest = Get-Content -LiteralPath (Join-Path $root 'data\yabasanshiro_1_20_37_scanout_manifest.json') -Raw | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $PythonPath)) { throw "Bundled Python missing: $PythonPath" }
& $PythonPath $verify --source $Source --archive $Archive
if ($LASTEXITCODE -ne 0) { throw 'Refusing official patch: source/archive/preimage verification failed.' }

$lode = Join-Path $Source 'yabause\src\runner\lodepng'
New-Item -ItemType Directory -Force -Path $lode | Out-Null
foreach ($file in $manifest.toolchain.lodepng.files.psobject.Properties) {
    $out = Join-Path $lode $file.Name
    if (-not (Test-Path -LiteralPath $out)) {
        Invoke-WebRequest -Uri "$($manifest.toolchain.lodepng.base_url)/$($file.Name)" -OutFile $out
    }
    $hash = (Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $file.Value) { throw "lodepng hash mismatch: $($file.Name)" }
}

$patch = Join-Path $root $manifest.official_patch.path
& git apply --check --unsafe-paths "--directory=$Source" $patch
if ($LASTEXITCODE -ne 0) { throw 'Official patch does not apply.' }
& git apply --unsafe-paths "--directory=$Source" $patch
if ($LASTEXITCODE -ne 0) { throw 'Official patch application failed.' }
Write-Output 'Applied official 1.20.37 REFERENCE_INSTRUMENT_ONLY diagnostic patch. It is not wired into acceptance evidence.'
