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

# Step 4: the RUNTIME's input-assembly path (gated constant table_set +
# span-view selectors) must reproduce the S1 known contact set over the same
# captures. The new assertion is that the runtime path - not just the library -
# assembles identical inputs (check A, zero mismatches, non-vacuous) and the
# full predicate over those inputs still counts the exact S1 numbers (check B).
# Requires the private captures and program image; skips cleanly without them.
# When generated/avsp_anim_records.h is present the span-view selector check
# upgrades to the runtime's sparse record-span form, same guard as the walk test.
$rtDefine = ''
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'generated/avsp_anim_records.h')) {
    $rtDefine = '-DAVSP_GENERATED_RECORDS '
}
$rtCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 $rtDefine" + "avsp_actor.c avsp_anim_script.c avsp_collision.c tests/avsp_runtime_collision_test.c -o build/avsp_runtime_collision_test && ./build/avsp_runtime_collision_test"
& $wsl.Source sh '-lc' $rtCommand
if ($LASTEXITCODE -ne 0) {
    throw "Runtime input-assembly collision test failed with exit code $LASTEXITCODE."
}

# ROM animation-script walk against the game's own per-frame record pointer.
# Requires the private captures and program image; skips cleanly without them.
# The shipped-subset equivalence check (check C) needs the generated record
# spans; without them the walk test still runs checks A and B.
$recordsDefine = ''
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'generated/avsp_anim_records.h')) {
    $recordsDefine = '-DAVSP_GENERATED_RECORDS '
}
$walkCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 $recordsDefine" + "avsp_actor.c avsp_anim_script.c tests/avsp_anim_walk_test.c -o build/avsp_anim_walk_test && ./build/avsp_anim_walk_test"
& $wsl.Source sh '-lc' $walkCommand
if ($LASTEXITCODE -ne 0) {
    throw "Animation-walk test failed with exit code $LASTEXITCODE."
}

# The complete ROM-to-object emission pipeline (pose assembly -> selector ->
# groups -> origin -> both loop variants -> four-word entries), checked
# against live-captured oracle entries for both selectors, both facing
# variants and three palettes. The same algorithm passes the 6,010-instance
# corpus falsification with zero mismatches; see avsp_emit.h and
# tools/verify_avsp_object_corpus.py. Requires the private program image;
# skips cleanly without it.
$emitCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_emit.c tests/avsp_emit_test.c -o build/avsp_emit_test && ./build/avsp_emit_test"
& $wsl.Source sh '-lc' $emitCommand
if ($LASTEXITCODE -ne 0) {
    throw "Object-emission pipeline test failed with exit code $LASTEXITCODE."
}

# S2 Body E: the ROM tile archive reader and the MAME-transcribed per-entry
# tile expansion, checked against the generated cd/SPR4/TILES.BIN and the
# committed oracle entries. Skips cleanly when the archive has not been
# generated (it carries ROM-derived bytes and stays untracked; regenerate
# with tools/gen_avsp_gfx_tiles.py).
$tilesCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_tiles.c tests/avsp_tiles_test.c -o build/avsp_tiles_test && ./build/avsp_tiles_test"
& $wsl.Source sh '-lc' $tilesCommand
if ($LASTEXITCODE -ne 0) {
    throw "ROM tile archive test failed with exit code $LASTEXITCODE."
}

# Negative test: the tile generator must refuse a --scope round1 archive
# against the runtime's real cartridge carve, and must leave the on-disk
# street archive and its manifest untouched when it does. This also
# regenerates the street archive as its baseline step, so it doubles as
# the "regenerate after asset extraction" verification build.ps1 relies on.
& $PythonPath (Join-Path $PSScriptRoot 'tests\test_avsp_gfx_tiles_budget.py')
if ($LASTEXITCODE -ne 0) {
    throw "Tile archive budget test failed with exit code $LASTEXITCODE."
}

# table_set writer-trace analyzer: synthetic positive/negative fixtures (no
# private inputs needed) plus, when the pinned retained run is present, a
# full parse that asserts 7 logical stores / no orphans / G=2373. Skips the
# positive path cleanly in a checkout that lacks the untracked raw inputs.
& $PythonPath (Join-Path $PSScriptRoot 'tools\analyze_avsp_table_set_writer.py') '--self-test'
if ($LASTEXITCODE -ne 0) {
    throw "table_set writer-trace analyzer self-test failed with exit code $LASTEXITCODE."
}

# table_set source rule: transcribes three LIVE instruction-trace findings
# (each family's store is an immediate constant, not a table read) and
# falsifies them against the full-corpus attribution watchpoint log with a
# negative control. No file dependencies - always runs, no private inputs
# needed.
& $PythonPath (Join-Path $PSScriptRoot 'tools\gen_avsp_table_set_source.py')
if ($LASTEXITCODE -ne 0) {
    throw "table_set source-rule falsification failed with exit code $LASTEXITCODE."
}

# table_set source-rule decoder: maps spawn context (route/slot/timing - NOT
# any actor byte) to the proven per-type constant and falsifies it across the
# stride-1 target-type-12 corpus with a non-vacuous perturbation control.
# Reads only the tracked evidence manifest; always runs, no private inputs.
& $PythonPath (Join-Path $PSScriptRoot 'tools\decode_avsp_table_set.py')
if ($LASTEXITCODE -ne 0) {
    throw "table_set source-rule decoder falsification failed with exit code $LASTEXITCODE."
}

# Step-1 GATE: prove the runtime street-alien table_set constant (0x00130AC8)
# over the stride-1 street capture before any runtime wiring - every active
# type-12 frame whose record pointer sits in the walk/attack street spans must
# carry it, zero exceptions. No correlation, no spawn_type. Requires the
# private program image + street captures; skips cleanly without them (the
# committed manifest records the run where inputs were present).
& $PythonPath (Join-Path $PSScriptRoot 'tools\gate_avsp_table_set.py')
if ($LASTEXITCODE -ne 0) {
    throw "table_set street-alien gate failed with exit code $LASTEXITCODE."
}

# Frontend screen composition: derives, from the ROM-truth frontend capture
# (layers/objects, never pixels), what the title and character-select screens
# are actually drawn with. Skips cleanly when the private capture is absent;
# regenerate with capture_frontend_rom.ps1.
& $PythonPath (Join-Path $PSScriptRoot 'tools\analyze_frontend_rom_composition.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend composition analysis failed with exit code $LASTEXITCODE."
}
