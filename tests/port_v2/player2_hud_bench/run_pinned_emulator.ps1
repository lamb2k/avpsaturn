[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(1, 2)]
    [int]$Run,
    [string]$EmulatorPath
)

$ErrorActionPreference = 'Stop'
$delegate = Join-Path $PSScriptRoot '..\hud_pcm_bench\run_pinned_emulator.ps1'
& $delegate -Run $Run -EmulatorPath $EmulatorPath
if ($LASTEXITCODE -ne 0) {
    throw "Player 2 HUD pinned-emulator run $Run failed."
}
