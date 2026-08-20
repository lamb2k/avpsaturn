[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [string]$OutputRoot = 'C:\yb5',
    [string]$CMakeExe = '',
    [string]$VsDevCmd = 'C:\BuildTools\VS2022\Common7\Tools\VsDevCmd.bat'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $CMakeExe) {
    $CMakeExe = Join-Path $root '.deps\toolchain\cmake-3.30.5-windows-x86_64\bin\cmake.exe'
}
if (-not (Test-Path -LiteralPath $CMakeExe)) { throw "Portable CMake missing: $CMakeExe" }
if (-not (Test-Path -LiteralPath $VsDevCmd)) { throw "VS environment script missing: $VsDevCmd" }
if (-not (Test-Path -LiteralPath (Join-Path $Source 'yabause\src\runner\lodepng\lodepng.h'))) {
    throw 'Patch prerequisites are missing; run apply_yabasanshiro_scanout_patch.ps1 first.'
}

$build = Join-Path $OutputRoot 'src'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$configure = '"{0}" -S "{1}" -B "{2}" -G "NMake Makefiles" -DYAB_PORTS=runner -DYAB_WANT_OPENGL=ON -DYAB_WANT_SDL=ON -DYAB_WANT_OPENAL=ON -DCMAKE_BUILD_TYPE=Debug' -f $CMakeExe, (Join-Path $Source 'yabause'), $build
$buildCommand = '"{0}" --build "{1}" --target yabause-runner' -f $CMakeExe, $build
& cmd.exe /d /s /c "`"$VsDevCmd`" -arch=x64 -host_arch=x64 && $configure && $buildCommand"
if ($LASTEXITCODE -ne 0) { throw "Rejected diagnostic build failed: $LASTEXITCODE" }

$runner = Join-Path $build 'runner\yabasanshiro.exe'
if (-not (Test-Path -LiteralPath $runner)) { throw "Runner missing after build: $runner" }
$hash = (Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output "REPRODUCES_A_REJECTED_CUSTOM_DIAGNOSTIC_BUILD runner: $runner"
Write-Output "runner_sha256: $hash"
Write-Output 'This build is not guest-equivalent to the pinned release and cannot be used for RP4 acceptance.'
