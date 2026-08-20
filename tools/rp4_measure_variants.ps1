<#
.SYNOPSIS
Build and capture the four RP4 submission-order variants, one rule for all.

.DESCRIPTION
The RP4 question is whether the street loop's order survives into the
final VDP1 command sequence. Answering it needs four builds that differ
only in declared switches, each captured at the same fixture frame by the
same predicate:

  sorted_reverse     the old slDispSprite path, reverse loop  (control)
  sorted_forward     the old slDispSprite path, forward loop  (control)
  immediate_reverse  slPutSprite, reverse loop                (candidate)
  immediate_forward  slPutSprite, forward loop                (negative)

The two sorted builds must reproduce the committed inert result. If they
stop being inert, the instrument changed and no candidate result from the
same run can be trusted.

Every build is -Clean, and the compile-profile stamp now includes the RP4
switches, so no variant can inherit another's main.o.
#>
[CmdletBinding()]
param(
    [string]$EmulatorPath,
    [int]$Rel = 0,
    [double]$TimeoutSeconds = 300,
    [string]$OutputRoot = 'private-evidence\rp4-direct-order',
    [string[]]$Only,
    [switch]$Repeat
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$python = Join-Path $env:USERPROFILE `
    '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "bundled Python not found at $python"
}
if (-not $EmulatorPath) {
    $EmulatorPath = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.deps\emulators') `
        -Filter 'yabasanshiro.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $EmulatorPath -or -not (Test-Path -LiteralPath $EmulatorPath)) {
    throw 'yabasanshiro.exe not found; pass -EmulatorPath.'
}

# FrameLag is how many fixture frames the committed VDP1 command table
# trails the street draw loop for that submission path. The sorted path
# leaves the frame in SGL's sort list until slSynch, so its table is one
# frame behind; the immediate path has already written it. Declaring the
# lag is what makes the cross-path comparison like for like.
$variants = @(
    @{ Name = 'sorted_reverse';    Flags = @();                                            FrameLag = 1 }
    @{ Name = 'sorted_forward';    Flags = @('-Rp4ForwardOrder');                          FrameLag = 1 }
    @{ Name = 'immediate_reverse'; Flags = @('-Rp4ImmediateSprites');                      FrameLag = 0 }
    @{ Name = 'immediate_forward'; Flags = @('-Rp4ImmediateSprites', '-Rp4ForwardOrder');  FrameLag = 0 }
)
if ($Only) { $variants = $variants | Where-Object { $Only -contains $_.Name } }

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
New-Item -ItemType Directory -Force -Path 'build\rp4_launch' | Out-Null
$summary = @()

foreach ($variant in $variants) {
    $name = $variant.Name
    Write-Host "=== $name : building ===" -ForegroundColor Cyan
    $buildArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', '.\build.ps1',
                   '-Clean', '-StreetTest', '-SkipHostTests') + $variant.Flags
    & powershell @buildArgs | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "$name build failed with exit $LASTEXITCODE" }

    $elf = (Get-FileHash -Algorithm SHA256 'game.elf').Hash.ToLower()
    $iso = (Get-FileHash -Algorithm SHA256 'game.iso').Hash.ToLower()
    Write-Host "=== $name : elf $($elf.Substring(0,16)) iso $($iso.Substring(0,16)) ==="

    Write-Host "=== $name : capturing at fixture frame $Rel ===" -ForegroundColor Cyan
    & $python 'tools\street_launch.py' `
        --emulator $EmulatorPath `
        --expect-live `
        --timeout $TimeoutSeconds `
        --capture-label $name `
        --capture-rel $Rel `
        --capture-frame-lag $variant.FrameLag `
        --capture-output (Join-Path $OutputRoot "$name.json") `
        --report (Join-Path 'build\rp4_launch' "$name.launch.json") | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "$name capture failed with exit $LASTEXITCODE" }

    if ($Repeat) {
        # Same unchanged build, second cold boot. If this is not identical
        # the instrument is not deterministic and no variant difference
        # measured against it means anything.
        Write-Host "=== $name : determinism repeat ===" -ForegroundColor Cyan
        & $python 'tools\street_launch.py' `
            --emulator $EmulatorPath --expect-live --timeout $TimeoutSeconds `
            --capture-label "$name-repeat" --capture-rel $Rel `
            --capture-frame-lag $variant.FrameLag `
            --capture-output (Join-Path $OutputRoot "$name.repeat.json") `
            --report (Join-Path 'build\rp4_launch' "$name.repeat.launch.json") | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "$name repeat capture failed" }
    }

    $summary += [pscustomobject]@{
        Variant = $name
        Elf     = $elf
        Iso     = $iso
        Capture = (Get-FileHash -Algorithm SHA256 (Join-Path $OutputRoot "$name.json")).Hash.ToLower()
    }
}

Write-Host ''
$summary | Format-Table -AutoSize
$summary | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path 'build\rp4_launch' 'variant_builds.json') -Encoding utf8

$stale = Get-Process yabasanshiro*, mame -ErrorAction SilentlyContinue
if ($stale) { throw "emulator processes still running: $($stale.Id -join ', ')" }
Write-Host 'no emulator process remains' -ForegroundColor Green
