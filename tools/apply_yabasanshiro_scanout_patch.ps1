[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [string]$PythonPath = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $root 'data\yabasanshiro_scanout_diagnostic_manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Bundled Python not found: $PythonPath"
}
& $PythonPath (Join-Path $PSScriptRoot 'verify_yabasanshiro_scanout_diagnostic.py') --source $Source
if ($LASTEXITCODE -ne 0) {
    throw "Refusing to apply rejected diagnostic patch (verification exit $LASTEXITCODE)."
}

$lodeDirectory = Join-Path $Source 'yabause\src\runner\lodepng'
New-Item -ItemType Directory -Force -Path $lodeDirectory | Out-Null
foreach ($entry in $manifest.toolchain.dependencies.lodepng.files.psobject.Properties) {
    $destination = Join-Path $lodeDirectory $entry.Name
    if (-not (Test-Path -LiteralPath $destination)) {
        $url = "$($manifest.toolchain.dependencies.lodepng.base_url)/$($entry.Name)"
        Invoke-WebRequest -Uri $url -OutFile $destination
    }
    $actual = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) {
        throw "lodepng hash mismatch for $($entry.Name): $actual"
    }
}

$patch = Join-Path $root $manifest.patch.path
& git -C $Source apply --check --ignore-space-change $patch
if ($LASTEXITCODE -ne 0) { throw 'git apply --check failed.' }
& git -C $Source apply --ignore-space-change $patch
if ($LASTEXITCODE -ne 0) { throw 'git apply failed.' }

Write-Output 'Applied REPRODUCES_A_REJECTED_CUSTOM_DIAGNOSTIC_BUILD patch only.'
