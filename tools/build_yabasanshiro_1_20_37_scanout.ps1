[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$OutputRoot,
    [string]$CMakeExe = '',
    [string]$VsDevCmd = 'C:\BuildTools\VS2022\Common7\Tools\VsDevCmd.bat'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $CMakeExe) { $CMakeExe = Join-Path $root '.deps\toolchain\cmake-3.30.5-windows-x86_64\bin\cmake.exe' }
if (-not (Test-Path -LiteralPath $CMakeExe)) { throw "Portable CMake missing: $CMakeExe" }
if (-not (Test-Path -LiteralPath $VsDevCmd)) { throw "VS environment script missing: $VsDevCmd" }
if (-not (Test-Path -LiteralPath (Join-Path $Source 'yabause\src\runner\lodepng\lodepng.h'))) {
    throw 'lodepng prerequisite missing: run apply_yabasanshiro_1_20_37_scanout.ps1 first.'
}
if (-not (Test-Path -LiteralPath $OutputRoot)) { New-Item -ItemType Directory -Path $OutputRoot | Out-Null }
$build = Join-Path $OutputRoot 'build'
$configure = '"{0}" -S "{1}" -B "{2}" -G "NMake Makefiles" -DYAB_PORTS=runner -DYAB_WANT_OPENGL=ON -DYAB_WANT_SDL=ON -DYAB_WANT_OPENAL=ON -DYAB_WANT_SH2_CACHE=ON -DCMAKE_BUILD_TYPE=Release' -f $CMakeExe, (Join-Path $Source 'yabause'), $build
$compile = '"{0}" --build "{1}" --target yabause-runner' -f $CMakeExe, $build
& cmd.exe /d /s /c "`"$VsDevCmd`" -arch=x64 -host_arch=x64 >nul && $configure && $compile"
if ($LASTEXITCODE -ne 0) { throw "Official runner build failed: $LASTEXITCODE" }
$runner = Join-Path $build 'src\runner\yabasanshiro.exe'
if (-not (Test-Path -LiteralPath $runner)) { throw "Runner missing: $runner" }
Write-Output "runner=$runner"
Write-Output "runner_sha256=$((Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash.ToLowerInvariant())"
Write-Output 'This REFERENCE_INSTRUMENT_ONLY output is not wired into RP4 or AvP acceptance evidence.'
