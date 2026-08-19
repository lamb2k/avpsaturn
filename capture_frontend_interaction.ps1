[CmdletBinding()]
param(
    [switch]$Refresh,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
$captureRoot = Join-Path $projectRoot '.deps\mame\frontend_interaction'
$routes = @('topology', 'button1', 'button2', 'button3', 'alternate_confirm')

if (-not (Test-Path -LiteralPath $mame)) {
    & (Join-Path $projectRoot 'setup_reference.ps1')
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'avspu'))) {
    throw 'The local avspu ROM directory is missing from the project root.'
}

& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

foreach ($route in $routes) {
    $routeRoot = Join-Path $captureRoot $route
    $required = Join-Path $routeRoot 'samples.tsv'
    if ($Refresh -or -not (Test-Path -LiteralPath $required)) {
        if (Test-Path -LiteralPath $routeRoot) {
            $resolvedRoute = (Resolve-Path -LiteralPath $routeRoot).Path
            $resolvedRoot = if (Test-Path -LiteralPath $captureRoot) {
                (Resolve-Path -LiteralPath $captureRoot).Path
            } else { $captureRoot }
            if (-not $resolvedRoute.StartsWith(
                    $resolvedRoot + [IO.Path]::DirectorySeparatorChar,
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw "Refusing to clear frontend route outside $resolvedRoot."
            }
            Remove-Item -LiteralPath $resolvedRoute -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path $routeRoot | Out-Null
        Push-Location $projectRoot
        try {
            $env:AVSP_FRONTEND_INTERACTION_ROUTE = $route
            & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
                '-nothrottle' '-skip_gameinfo' '-snapshot_directory' '.deps\mame' `
                '-autoboot_delay' '0' '-autoboot_script' `
                '.\tools\mame_capture_frontend_interaction.lua'
            if ($LASTEXITCODE -ne 0) {
                throw "Frontend interaction route '$route' failed with exit code $LASTEXITCODE."
            }
        }
        finally {
            Remove-Item Env:AVSP_FRONTEND_INTERACTION_ROUTE -ErrorAction SilentlyContinue
            Pop-Location
        }
    }
    else {
        Write-Host "Reusing frontend interaction route '$route'."
    }
}

if (-not $PythonPath) {
    $bundledPython = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) {
        $PythonPath = $bundledPython
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Bundled Python 3 is required to analyze the frontend interaction.'
}

& $PythonPath (Join-Path $projectRoot 'tools\analyze_frontend_interaction.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend interaction analysis failed with exit code $LASTEXITCODE."
}
