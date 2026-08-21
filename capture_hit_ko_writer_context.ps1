[CmdletBinding()]
param(
    [string]$MamePath = '.deps\mame\mame0289\mame.exe',
    [string]$RomPath = 'C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest'
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$mame = Join-Path $projectRoot $MamePath
$contextRoot = Join-Path $projectRoot '.deps\mame\vertical_slice\hit_ko_writer_context_watchpoint_4'
$nvramBaseline = Join-Path $projectRoot '.deps\mame\full_route_nvram_baseline\eeprom'
$cfgRoot = Join-Path $projectRoot '.deps\mame\hit_ko_writer_context_cfg'
$nvramRoot = Join-Path $projectRoot '.deps\mame\hit_ko_writer_context_nvram'

if (-not (Test-Path -LiteralPath $mame)) { throw "MAME is missing: $mame" }
if (-not (Test-Path -LiteralPath $RomPath)) { throw "ROM root is missing: $RomPath" }
if (-not (Test-Path -LiteralPath $nvramBaseline)) { throw "NVRAM baseline is missing: $nvramBaseline" }
if (Test-Path -LiteralPath $contextRoot) { throw "Refusing to replace private context: $contextRoot" }

New-Item -ItemType Directory -Force -Path $contextRoot, $cfgRoot,
    (Join-Path $nvramRoot 'avspu') | Out-Null
Copy-Item -LiteralPath $nvramBaseline -Destination (Join-Path $nvramRoot 'avspu\eeprom')

& $mame '-rompath' $RomPath '-verifyroms' 'avspu'
if ($LASTEXITCODE -ne 0) { throw "avspu verification failed: $LASTEXITCODE" }

$priorRoot, $priorFirst, $priorLast = $env:AVSP_HIT_KO_CONTEXT_ROOT,
    $env:AVSP_HIT_KO_FIRST, $env:AVSP_HIT_KO_LAST
try {
    $env:AVSP_HIT_KO_CONTEXT_ROOT = (Resolve-Path -LiteralPath $contextRoot).Path.Replace('\', '/')
    $env:AVSP_HIT_KO_FIRST = '4080'
    $env:AVSP_HIT_KO_LAST = '5469'
    Push-Location $contextRoot
    try {
        & $mame 'avspu' '-rompath' $RomPath '-video' 'none' '-sound' 'none' '-nothrottle' `
            '-skip_gameinfo' '-debug' '-autoboot_delay' '0' '-cfg_directory' $cfgRoot `
            '-nvram_directory' $nvramRoot '-autoboot_script' (Join-Path $projectRoot 'tools\mame_capture_hit_ko_writer_context.lua') '-log'
        if ($LASTEXITCODE -ne 0) { throw "MAME write-context capture failed: $LASTEXITCODE" }
        $errorLog = Join-Path $contextRoot 'error.log'
        if ((Test-Path -LiteralPath $errorLog) -and
            (Select-String -LiteralPath $errorLog -Pattern '\[LUA ERROR\]' -Quiet)) {
            throw "MAME write-context capture logged a Lua callback error: $errorLog"
        }
    }
    finally { Pop-Location }
}
finally {
    $env:AVSP_HIT_KO_CONTEXT_ROOT = $priorRoot
    $env:AVSP_HIT_KO_FIRST = $priorFirst
    $env:AVSP_HIT_KO_LAST = $priorLast
}

Write-Output "Private target-actor context captured: $contextRoot"
