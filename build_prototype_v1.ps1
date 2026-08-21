[CmdletBinding()]
param(
    [string]$JoEngineRoot,
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (-not $JoEngineRoot) {
    $JoEngineRoot = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest\.deps\joengine'
}
if (-not (Test-Path -LiteralPath $JoEngineRoot)) {
    throw "Pinned Jo Engine dependency is missing: $JoEngineRoot"
}
if (-not $PythonPath) {
    $candidate = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($candidate) { $PythonPath = $candidate.Source }
}
if (-not $PythonPath) { throw 'Python 3 is required.' }

$resolvedEngine = (Resolve-Path -LiteralPath $JoEngineRoot).Path
$utilities = Join-Path $resolvedEngine 'Compiler\WINDOWS\Other Utilities'
$make = Join-Path $utilities 'make.exe'
$mkisofs = Join-Path $utilities 'mkisofs.exe'
$projectUri = [Uri]($projectRoot.TrimEnd('\') + '\')
$engineUri = [Uri]($resolvedEngine.TrimEnd('\') + '\')
$relativeEngine = [Uri]::UnescapeDataString(
    $projectUri.MakeRelativeUri($engineUri).ToString()).TrimEnd('/')
if ($relativeEngine -match '\s') {
    throw "Relative Jo Engine path contains spaces: $relativeEngine"
}

$outputRoot = Join-Path $projectRoot 'build\prototype_v1'
$contentRoot = Join-Path $outputRoot 'cd'
$loaderRoot = Join-Path $outputRoot 'loader'
New-Item -ItemType Directory -Force -Path (Join-Path $contentRoot 'BG') | Out-Null
New-Item -ItemType Directory -Force -Path $loaderRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'build\loader') | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'cd\BG\CORRIDOR.TGA') `
    -Destination (Join-Path $contentRoot 'BG\CORRIDOR.TGA') -Force
foreach ($name in @('ABS.TXT', 'BIB.TXT', 'CPY.TXT')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot "cd\$name") `
        -Destination (Join-Path $contentRoot $name) -Force
}

$previousPath = $env:PATH
try {
    $env:PATH = "$utilities;$(Join-Path $resolvedEngine 'Compiler\WINDOWS\bin');$previousPath"
    Push-Location $projectRoot
    try {
        foreach ($path in @(
            'src\prototype_v1\runtime.o', 'src\prototype_v1\core.o',
            'game.elf', 'game.raw', 'game.map', 'loader\loader.o',
            'loader\trampoline.o', 'build\loader\loader.elf',
            'build\loader\loader.raw', 'build\loader\loader.map'
        )) {
            if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
        }
        $makeArgs = @('-f', 'makefile', "JO_ENGINE_ROOT=$relativeEngine",
                      'AVSP_PROTOTYPE_V1=1', 'JO_DEBUG=1', 'game.raw')
        & $make @makeArgs
        if ($LASTEXITCODE -ne 0) { throw 'Prototype Saturn compilation failed.' }
        $loaderArgs = @('-f', 'makefile', "JO_ENGINE_ROOT=$relativeEngine",
                        'AVSP_PROTOTYPE_V1=1', 'JO_DEBUG=1',
                        'build/loader/loader.raw')
        & $make @loaderArgs
        if ($LASTEXITCODE -ne 0) { throw 'Prototype loader compilation failed.' }

        $game = Get-Item game.raw
        if ($game.Length -gt 1MB) { throw 'GAME.BIN exceeds staging area.' }
        $loader = Get-Item build\loader\loader.raw
        if ($loader.Length -gt 400KB) { throw 'Loader exceeds pinned Yaba envelope.' }
        Copy-Item -LiteralPath $loader.FullName `
            -Destination (Join-Path $contentRoot '0.bin') -Force
        Copy-Item -LiteralPath $game.FullName `
            -Destination (Join-Path $contentRoot 'GAME.BIN') -Force

        $loaderIp = Join-Path $loaderRoot 'IP.BIN'
        & $PythonPath tools\build_loader_ip.py `
            (Join-Path $resolvedEngine 'Compiler\COMMON\IP.BIN') $loaderIp
        if ($LASTEXITCODE -ne 0) { throw 'Prototype loader IP build failed.' }
        $iso = Join-Path $outputRoot 'prototype_v1.iso'
        & $mkisofs -quiet -sysid 'SEGA SATURN' -volid 'AVP_PROTO_V1' `
            -volset 'AVP_PROTO_V1' -sectype 2352 -publisher 'PRIVATE PROTOTYPE' `
            -preparer 'PRIVATE PROTOTYPE' -appid 'AVP_PLAYABLE_SKELETON' `
            -abstract '.\cd\ABS.TXT' -copyright '.\cd\CPY.TXT' `
            -biblio '.\cd\BIB.TXT' -generic-boot $loaderIp `
            -full-iso9660-filenames -o $iso $contentRoot
        if ($LASTEXITCODE -ne 0) { throw 'Prototype ISO creation failed.' }
        & $PythonPath tools\verify_iso_file.py $iso '/GAME.BIN' `
            '--equals' (Join-Path $contentRoot 'GAME.BIN')
        if ($LASTEXITCODE -ne 0) { throw 'Prototype ISO GAME.BIN verification failed.' }
        & $PythonPath tools\verify_iso_file.py $iso '/BG/CORRIDOR.TGA' `
            '--equals' (Join-Path $contentRoot 'BG\CORRIDOR.TGA')
        if ($LASTEXITCODE -ne 0) { throw 'Prototype ISO stage verification failed.' }
        $cue = Join-Path $outputRoot 'prototype_v1.cue'
        [IO.File]::WriteAllLines($cue, @(
            'FILE "prototype_v1.iso" BINARY',
            '  TRACK 01 MODE1/2048',
            '    INDEX 01 00:00:00'
        ))
        $manifest = Join-Path $outputRoot 'manifest.txt'
        [IO.File]::WriteAllLines($manifest, @(
            'classification=PROTOTYPE_ONLY',
            'profile=debug-prototype-v1',
            "controller_base=bbf6ccd5bf4103a71a695483877f28267b13bc27",
            "game_bytes=$($game.Length)",
            "iso_sha256=$((Get-FileHash $iso -Algorithm SHA256).Hash.ToLowerInvariant())",
            "cue_sha256=$((Get-FileHash $cue -Algorithm SHA256).Hash.ToLowerInvariant())"
        ))
        Write-Host "Built $cue"
    }
    finally { Pop-Location }
}
finally { $env:PATH = $previousPath }
