[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$wsl = Get-Command 'wsl.exe' -ErrorAction SilentlyContinue
if (-not $wsl) {
    throw 'WSL with GCC is required for the strict host-side gameplay-model test.'
}

$linuxRoot = (& $wsl.Source wslpath '-a' $PSScriptRoot).Trim()
if ($LASTEXITCODE -ne 0 -or -not $linuxRoot) {
    throw 'Could not translate the project path for WSL.'
}

if ($linuxRoot.Contains("'")) {
    throw 'The WSL project path contains an unsupported apostrophe.'
}
$command = "cd '$linuxRoot' && mkdir -p build && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 capability_model.c tests/capability_model_test.c -o build/capability_model_test && ./build/capability_model_test"
& $wsl.Source sh '-lc' $command
if ($LASTEXITCODE -ne 0) {
    throw "Gameplay-model tests failed with exit code $LASTEXITCODE."
}
