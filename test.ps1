[CmdletBinding()]
param(
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
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
            $bundledPython = Join-Path $env:USERPROFILE `
                '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonPath = $bundledPython
            }
        }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw 'Python 3 is required to validate the committed Stage 1 route ledger.'
}

& $PythonPath (Join-Path $PSScriptRoot 'tools\generate_stage1_route.py')
if ($LASTEXITCODE -ne 0) {
    throw "Stage 1 route-ledger validation failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $PSScriptRoot 'tools\generate_boss_anim_script.py')
if ($LASTEXITCODE -ne 0) {
    throw "Boss animation script generation failed with exit code $LASTEXITCODE."
}

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

$animCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_anim_script.c tests/avsp_anim_script_test.c -o build/avsp_anim_script_test && ./build/avsp_anim_script_test"
& $wsl.Source sh '-lc' $animCommand
if ($LASTEXITCODE -ne 0) {
    throw "Animation-script interpreter test failed with exit code $LASTEXITCODE."
}

# Actor record + the C port of the game's collision predicate. Requires the
# private captures and program image; the test skips cleanly without them.
$actorCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_actor.c avsp_collision.c tests/avsp_actor_test.c -o build/avsp_actor_test && ./build/avsp_actor_test"
& $wsl.Source sh '-lc' $actorCommand
if ($LASTEXITCODE -ne 0) {
    throw "Actor-spine / collision-port test failed with exit code $LASTEXITCODE."
}
