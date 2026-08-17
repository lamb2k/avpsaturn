[CmdletBinding()]
param(
    [string]$JoEngineRoot,
    [string]$PythonPath,
    [switch]$Clean,
    [switch]$Release,
    [switch]$SkipHostTests
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (-not $JoEngineRoot) {
    $JoEngineRoot = Join-Path $projectRoot '.deps\joengine'
}
if (-not (Test-Path -LiteralPath $JoEngineRoot)) {
    throw "Jo Engine dependency is missing. Run .\setup_engine.ps1 first."
}
$resolvedEngine = (Resolve-Path -LiteralPath $JoEngineRoot).Path
$compiler = Join-Path $resolvedEngine 'Compiler\WINDOWS\bin\sh-elf-gcc.exe'
$objcopy = Join-Path $resolvedEngine 'Compiler\WINDOWS\bin\sh-elf-objcopy.exe'
$utilities = Join-Path $resolvedEngine 'Compiler\WINDOWS\Other Utilities'
$make = Join-Path $utilities 'make.exe'
$mkisofs = Join-Path $utilities 'mkisofs.exe'
$cueMaker = Join-Path $utilities 'JoEngineCueMaker.exe'

foreach ($requiredTool in @($compiler, $objcopy, $make, $mkisofs, $cueMaker)) {
    if (-not (Test-Path -LiteralPath $requiredTool)) {
        throw "Required Saturn build tool not found: $requiredTool"
    }
}

if (-not $PythonPath) {
    $pythonCommand = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $PythonPath = $pythonCommand.Source
    }
    else {
        $pythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
        if ($pythonCommand -and $pythonCommand.Source -notlike '*WindowsApps*') {
            $PythonPath = $pythonCommand.Source
        }
        else {
            $bundledPython = Join-Path $env:LOCALAPPDATA 'codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonPath = $bundledPython
            }
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 with Pillow is required. Pass its executable with -PythonPath.'
}

$projectUri = [Uri]($projectRoot.TrimEnd('\') + '\')
$engineUri = [Uri]($resolvedEngine.TrimEnd('\') + '\')
$relativeEngine = [Uri]::UnescapeDataString($projectUri.MakeRelativeUri($engineUri).ToString()).TrimEnd('/')
if ($relativeEngine -match '\s') {
    throw "The relative Jo Engine path '$relativeEngine' contains spaces, which its makefiles do not support."
}

$previousPath = $env:PATH
try {
    $env:PATH = "$utilities;$(Join-Path $resolvedEngine 'Compiler\WINDOWS\bin');$previousPath"
    Push-Location $projectRoot
    try {
        if (-not $SkipHostTests) {
            & '.\test.ps1'
            if ($LASTEXITCODE -ne 0) {
                throw "Host tests failed with exit code $LASTEXITCODE."
            }
        }

        & '.\prepare_avsp_port.ps1' -PythonPath $PythonPath
        if ($LASTEXITCODE -ne 0) {
            throw "AvP Stage 1 asset preparation failed with exit code $LASTEXITCODE."
        }

        $contentRoot = Join-Path $projectRoot 'build\avsp_cd'
        foreach ($metadataName in @('ABS.TXT', 'BIB.TXT', 'CPY.TXT')) {
            Copy-Item -LiteralPath (Join-Path $projectRoot "cd\$metadataName") `
                -Destination (Join-Path $contentRoot $metadataName) -Force
        }

        if ($Clean) {
            # Jo Engine's bundled Cygwin rm.exe can fail to reserve its heap on
            # current 64-bit Windows. Remove only this project's known outputs.
            foreach ($generatedName in @(
                'main.o', 'capability_model.o', 'game.elf', 'game.raw',
                'game.iso', 'game.cue', 'game.map', 'cd\0.bin', 'build\avsp_cd\0.bin'
            )) {
                $generatedPath = Join-Path $projectRoot $generatedName
                if (Test-Path -LiteralPath $generatedPath) {
                    Remove-Item -LiteralPath $generatedPath -Force
                }
            }
            Get-ChildItem -LiteralPath (Join-Path $resolvedEngine 'jo_engine') -Filter '*.o' -File |
                Remove-Item -Force
            }

        $makeArguments = @('-f', 'makefile', "JO_ENGINE_ROOT=$relativeEngine")
        if ($Release) {
            $makeArguments += 'JO_DEBUG=0'
        }
        $makeArguments += 'game.raw'
        & $make @makeArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Saturn compilation failed with exit code $LASTEXITCODE."
        }

        & $objcopy '-O' 'binary' 'game.elf' (Join-Path $contentRoot '0.bin')
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the Saturn boot binary (exit code $LASTEXITCODE)."
        }

        $mkisofsArguments = @(
            '-quiet',
            '-sysid', 'SEGA SATURN',
            '-volid', 'AVP_CAP_TEST',
            '-volset', 'AVP_CAP_TEST',
            '-sectype', '2352',
            '-publisher', 'PRIVATE CAPABILITY TEST',
            '-preparer', 'PRIVATE CAPABILITY TEST',
            '-appid', 'AVP_SATURN_CAPABILITY',
            '-abstract', '.\cd\ABS.TXT',
            '-copyright', '.\cd\CPY.TXT',
            '-biblio', '.\cd\BIB.TXT',
            '-generic-boot', (Join-Path $resolvedEngine 'Compiler\COMMON\IP.BIN'),
            '-full-iso9660-filenames',
            '-o', 'game.iso', $contentRoot
        )
        & $mkisofs @mkisofsArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create game.iso (exit code $LASTEXITCODE)."
        }

        & $cueMaker
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create game.cue (exit code $LASTEXITCODE)."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:PATH = $previousPath
}

Write-Host "Built $projectRoot\game.cue and game.iso"
