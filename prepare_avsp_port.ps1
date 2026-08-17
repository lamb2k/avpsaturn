[CmdletBinding()]
param(
    [string]$PythonPath,
    [switch]$RefreshCapture
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$romRoot = Join-Path $projectRoot 'avspu'
if (-not (Test-Path -LiteralPath $romRoot)) {
    throw 'The local avspu ROM directory is missing from the project root.'
}

& (Join-Path $projectRoot 'setup_reference.ps1')

$mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
& $mame '-rompath' $projectRoot '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) {
    throw "The avspu ROM audit failed with exit code $LASTEXITCODE."
}

$captureRoot = Join-Path $projectRoot '.deps\mame\captures'
New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
$requiredCaptures = @('gfx_region.bin', 'gfxram.tsv', 'palette.tsv', 'objram1.tsv',
    'animation_samples.tsv', 'active_object_bank.txt', 'objram_active_2880.tsv',
    'palette_2880.tsv', 'stage1_sample_2880.png')
$captureMissing = $false
foreach ($captureName in $requiredCaptures) {
    if (-not (Test-Path -LiteralPath (Join-Path $captureRoot $captureName))) {
        $captureMissing = $true
        break
    }
}
if ($RefreshCapture -or $captureMissing) {
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' '-nothrottle' `
            '-skip_gameinfo' '-snapshot_directory' '.deps\mame\captures' `
            '-state_directory' '.deps\mame\captures' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_stage1.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Deterministic Stage 1 capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host 'Reusing the existing verified deterministic Stage 1 capture.'
}

$playerActionArguments = @{}
if ($RefreshCapture) {
    $playerActionArguments['Refresh'] = $true
}
if ($PythonPath) {
    $playerActionArguments['PythonPath'] = $PythonPath
}
& (Join-Path $projectRoot 'capture_player_actions.ps1') @playerActionArguments
if ($LASTEXITCODE -ne 0) {
    throw "Isolated player-action capture failed with exit code $LASTEXITCODE."
}

$playerDamageArguments = @{}
if ($RefreshCapture) {
    $playerDamageArguments['Refresh'] = $true
}
if ($PythonPath) {
    $playerDamageArguments['PythonPath'] = $PythonPath
}
& (Join-Path $projectRoot 'capture_player_damage.ps1') @playerDamageArguments
if ($LASTEXITCODE -ne 0) {
    throw "Natural player-damage capture failed with exit code $LASTEXITCODE."
}

$enemyActionArguments = @{}
if ($RefreshCapture) {
    $enemyActionArguments['Refresh'] = $true
}
if ($PythonPath) {
    $enemyActionArguments['PythonPath'] = $PythonPath
}
& (Join-Path $projectRoot 'capture_enemy_actions.ps1') @enemyActionArguments
if ($LASTEXITCODE -ne 0) {
    throw "Natural enemy-action capture failed with exit code $LASTEXITCODE."
}

& (Join-Path $projectRoot 'capture_enemy_contact.ps1') @enemyActionArguments
if ($LASTEXITCODE -ne 0) {
    throw "Natural enemy-contact capture failed with exit code $LASTEXITCODE."
}

$bossCaptures = @('boss_gfxram.tsv', 'boss_cps_a_regs.tsv',
    'boss_cps_b_regs.tsv', 'boss_palette.tsv', 'boss_objram1.tsv',
    'boss_objram2.tsv', 'boss_active_object_bank.txt')
$bossCaptureMissing = $false
foreach ($captureName in $bossCaptures) {
    if (-not (Test-Path -LiteralPath (Join-Path $captureRoot $captureName))) {
        $bossCaptureMissing = $true
        break
    }
}
if ($RefreshCapture -or $bossCaptureMissing) {
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' '-nothrottle' `
            '-skip_gameinfo' '-snapshot_directory' '.deps\mame\captures' `
            '-state_directory' '.deps\mame\captures' '-autoboot_delay' '0' `
            '-autoboot_script' '.\tools\mame_capture_stage1_boss.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Deterministic Stage 1 boss capture failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host 'Reusing the existing verified Stage 1 Chrysalis-room capture.'
}

$bossActionArguments = @{}
if ($RefreshCapture) {
    $bossActionArguments['Refresh'] = $true
}
if ($PythonPath) {
    $bossActionArguments['PythonPath'] = $PythonPath
}
& (Join-Path $projectRoot 'capture_boss_actions.ps1') @bossActionArguments
if ($LASTEXITCODE -ne 0) {
    throw "Dense Chrysalis-action capture failed with exit code $LASTEXITCODE."
}

& (Join-Path $projectRoot 'capture_stalker_actions.ps1') @bossActionArguments
if ($LASTEXITCODE -ne 0) {
    throw "Dense Stage 1 Stalker-action capture failed with exit code $LASTEXITCODE."
}

$audioCapture = Join-Path $captureRoot 'stage1_route_reference.wav'
$audioRawCapture = Join-Path $captureRoot 'stage1_route_reference_untrimmed.wav'
$audioNeedsTrim = $false
if ($RefreshCapture -or -not (Test-Path -LiteralPath $audioCapture)) {
    Push-Location $projectRoot
    try {
        & $mame 'avspu' '-rompath' '.' '-video' 'none' '-sound' 'none' `
            '-samplerate' '44100' '-wavwrite' '.deps\mame\captures\stage1_route_reference_untrimmed.wav' `
            '-nothrottle' '-skip_gameinfo' '-state_directory' '.deps\mame\captures' `
            '-autoboot_delay' '0' '-autoboot_script' '.\tools\mame_capture_stage1_audio.lua'
        if ($LASTEXITCODE -ne 0) {
            throw "Stage 1 QSound reference capture failed with exit code $LASTEXITCODE."
        }
        $audioNeedsTrim = $true
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host 'Reusing the existing verified Stage 1 QSound reference mix.'
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
            $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonPath = $bundledPython
            }
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 with Pillow is required. Pass its executable with -PythonPath.'
}

if ($audioNeedsTrim) {
    & $PythonPath (Join-Path $projectRoot 'tools\trim_stage1_audio.py') `
        $audioRawCapture $audioCapture
    if ($LASTEXITCODE -ne 0) {
        throw "Stage 1 QSound WAV trim failed with exit code $LASTEXITCODE."
    }
}
if (-not (Test-Path -LiteralPath $audioCapture) -or
    (Get-Item -LiteralPath $audioCapture).Length -le 44) {
    throw 'The Stage 1 QSound reference WAV is missing or empty.'
}

$routeArguments = @((Join-Path $projectRoot 'tools\generate_stage1_route.py'))
$completeRouteMetadata = Join-Path $projectRoot `
    '.deps\mame\full_stage1_complete\route_samples.tsv'
if (Test-Path -LiteralPath $completeRouteMetadata) {
    $routeArguments += '--verify-captures'
}
& $PythonPath @routeArguments
if ($LASTEXITCODE -ne 0) {
    throw "Stage 1 route-ledger generation failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $projectRoot 'tools\extract_avspu_stage1.py')
if ($LASTEXITCODE -ne 0) {
    throw "CPS2 extraction and Saturn conversion failed with exit code $LASTEXITCODE."
}

Write-Host 'Prepared verified local AvP Stage 1 assets for the Saturn-native build.'
