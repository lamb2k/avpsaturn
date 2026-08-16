[CmdletBinding()]
param(
    [string]$SourceRepo = 'https://github.com/johannes-fetz/joengine.git'
)

$ErrorActionPreference = 'Stop'
$pinnedCommit = '556d081146211b6a1cfa6591d70f9487d406758b'
$dependencyRoot = Join-Path $PSScriptRoot '.deps'
$engineRoot = Join-Path $dependencyRoot 'joengine'
$patchPath = Join-Path $PSScriptRoot 'engine-patches\joengine-4bpp-sprites.patch'

if (-not (Test-Path -LiteralPath $patchPath)) {
    throw "Required engine patch not found: $patchPath"
}

if (-not (Test-Path -LiteralPath $dependencyRoot)) {
    New-Item -ItemType Directory -Path $dependencyRoot | Out-Null
}

if (-not (Test-Path -LiteralPath (Join-Path $engineRoot '.git'))) {
    if (Test-Path -LiteralPath $engineRoot) {
        throw "'$engineRoot' exists but is not a Git checkout. Move it aside and rerun setup."
    }
    & git clone --no-checkout $SourceRepo $engineRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Could not clone Jo Engine from '$SourceRepo'."
    }
    & git -C $engineRoot checkout --detach $pinnedCommit
    if ($LASTEXITCODE -ne 0) {
        throw "Could not check out pinned Jo Engine commit $pinnedCommit."
    }
}

$actualCommit = (& git -C $engineRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $pinnedCommit) {
    throw "Jo Engine dependency is at '$actualCommit'; expected '$pinnedCommit'."
}

$savedErrorPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& git -C $engineRoot apply --reverse --check $patchPath 2>$null
$patchAlreadyApplied = $LASTEXITCODE -eq 0
$ErrorActionPreference = $savedErrorPreference
if ($patchAlreadyApplied) {
    Write-Host "Jo Engine dependency is already patched."
}
else {
    & git -C $engineRoot apply --check $patchPath
    if ($LASTEXITCODE -ne 0) {
        throw "The 4bpp patch does not apply cleanly to pinned Jo Engine."
    }
    & git -C $engineRoot apply $patchPath
    if ($LASTEXITCODE -ne 0) {
        throw "Could not apply the 4bpp Jo Engine patch."
    }
    Write-Host "Applied the private 4bpp sprite patch."
}

Write-Host "Jo Engine $pinnedCommit is ready at $engineRoot"
