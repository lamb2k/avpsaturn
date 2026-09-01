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

& $PythonPath (Join-Path $PSScriptRoot 'tools\gen_avsp_table_set_classes.py')
if ($LASTEXITCODE -ne 0) {
    throw "Class-to-table-set lookup generation failed with exit code $LASTEXITCODE."
}

$animRom = Join-Path $PSScriptRoot '.deps\mame\actorprobe\decrypted_program_2m.bin'
$animCaptureA = Join-Path $PSScriptRoot '.deps\mame\collision_probe\workram.bin'
$animCaptureB = Join-Path $PSScriptRoot '.deps\mame\collision_probe_boss\workram.bin'
$animAnchorRoot = Join-Path $PSScriptRoot '.deps\mame\enemy_actions'
if ((Test-Path -LiteralPath $animRom) -and
    (Test-Path -LiteralPath $animCaptureA) -and
    (Test-Path -LiteralPath $animCaptureB) -and
    (Test-Path -LiteralPath (Join-Path $animAnchorRoot 'workram_05191.bin')) -and
    (Test-Path -LiteralPath (Join-Path $animAnchorRoot 'workram_05469.bin'))) {
    # Match the accepted complete-cadence REPAIR-09 range used by the Target
    # build. The former split rewrote the protected manifest to a narrower,
    # non-runtime identity whenever Fast ran.
    & $PythonPath (Join-Path $PSScriptRoot 'tools\gen_avsp_anim_records.py') `
        '--rom' $animRom '--capture' $animCaptureA '--capture' $animCaptureB `
        '--capture-dir-range' "$animAnchorRoot`:5191`:5469" `
        '--verify-deterministic'
    if ($LASTEXITCODE -ne 0) {
        throw "Animation-record extraction failed with exit code $LASTEXITCODE."
    }
}
else {
    Write-Host 'Animation-record extraction skipped: private inputs are incomplete.'
}

$wsl = Get-Command 'wsl.exe' -ErrorAction SilentlyContinue
if (-not $wsl) {
    throw 'WSL with GCC is required for the strict host-side gameplay-model test.'
}

$wslCompatibleRoot = $PSScriptRoot.Replace('\', '/')
$linuxRoot = (& $wsl.Source wslpath '-a' $wslCompatibleRoot).Trim()
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

# Bounded CRAM palette writes. Jo allocates colour RAM in 256-entry blocks but
# returns jo_palette::data one entry above the block base and documents a
# 255-colour maximum, because Saturn pixel/pen value zero is transparent and
# pixel p reads data[p - 1]. The test copies a full 255-colour surface, both
# extreme 4bpp sub-banks, and a source-indexed payload with canaries on the two
# hardware block boundaries, proves the canaries are live, and requires seven
# out-of-contract requests to be refused rather than clamped. No private inputs.
$cramCommand = "cd '$linuxRoot' && mkdir -p build && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_cram.c tests/avsp_cram_test.c -o build/avsp_cram_test && ./build/avsp_cram_test"
& $wsl.Source sh '-lc' $cramCommand
if ($LASTEXITCODE -ne 0) {
    throw "Bounded CRAM palette-write test failed with exit code $LASTEXITCODE."
}

# AvspSceneDef v0 contract (RP1): envelope/version/scene-ID validation, the
# unknown-scene policy, and the explicit route-controller state machine, with
# eleven negative controls (truncation, magic, version, ID zero, unknown
# opcode, short record, trailing payload, unknown lookup, dangling route
# edge, disagreeing transition). No private inputs.
$sceneCommand = "cd '$linuxRoot' && mkdir -p build && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_scene.c avsp_route.c tests/avsp_scene_test.c -o build/avsp_scene_test && ./build/avsp_scene_test"
& $wsl.Source sh '-lc' $sceneCommand
if ($LASTEXITCODE -ne 0) {
    throw "AvspSceneDef v0 contract test failed with exit code $LASTEXITCODE."
}

$sceneRuntimeCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_scene.c avsp_route.c avsp_scene_runtime.c tests/avsp_scene_runtime_test.c -o build/avsp_scene_runtime_test && ./build/avsp_scene_runtime_test"
& $wsl.Source sh '-lc' $sceneRuntimeCommand
if ($LASTEXITCODE -ne 0) {
    throw "AvspSceneRuntime player test failed with exit code $LASTEXITCODE."
}

$discGuardCommand = "cd '$linuxRoot' && gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 avsp_disc_guard.c tests/avsp_disc_guard_test.c -o build/avsp_disc_guard_test && ./build/avsp_disc_guard_test"
& $wsl.Source sh '-lc' $discGuardCommand
if ($LASTEXITCODE -ne 0) {
    throw "Disc-read guard test failed with exit code $LASTEXITCODE."
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

# S4 runtime input-assembly path (checked class table_set +
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

# S4 HIT/KO anchor replay. GAP_EXTERNAL_REPOINT is a measured, accepted result:
# it keeps those actions on the ADAPTED fallback and identifies the class 0x1F
# animation-pointer writer as an S5 translation dependency. The tool fails only
# for malformed evidence or missing shipped record coverage; private inputs skip.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_avsp_anchor_anim_replay.py')
if ($LASTEXITCODE -ne 0) {
    throw "HIT/KO animation-record replay check failed with exit code $LASTEXITCODE."
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
    throw "table_set street-alien check failed with exit code $LASTEXITCODE."
}

# Frontend screen composition: derives, from the ROM-truth frontend capture
# (layers/objects, never pixels), what the title and character-select screens
# are actually drawn with. Skips cleanly when the private capture is absent;
# regenerate with capture_frontend_rom.ps1.
& $PythonPath (Join-Path $PSScriptRoot 'tools\analyze_frontend_rom_composition.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend composition analysis failed with exit code $LASTEXITCODE."
}

# Cadence-1 character-select semantics: four cursor positions, source boundary
# behavior, all three confirm buttons, no observed cancel, selected-character
# work-RAM fields/writers, and a perturbed-input negative control.  Raw object
# RAM/work RAM/screenshots remain private and the analyzer skips cleanly when
# they are absent.
& $PythonPath (Join-Path $PSScriptRoot 'tools\analyze_frontend_interaction.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend interaction analysis failed with exit code $LASTEXITCODE."
}

# ROM-derived Saturn frontend converter: exact title/select composition from
# tilemaps + object lists, endpoint-aligned 384-to-352 fitting, palette/RLE
# round trips, live cursor cels, per-lifetime budgets and byte stability. Private
# captures and ROMs remain ignored; a checkout without them skips cleanly.
& $PythonPath (Join-Path $PSScriptRoot 'tools\gen_avsp_frontend.py') `
    '--verify-deterministic'
if ($LASTEXITCODE -ne 0) {
    throw "ROM-derived frontend generation failed with exit code $LASTEXITCODE."
}

# Live frontend palette-to-CRAM alignment under Jo's one-based contract, from
# the untracked -FrontendShotTest hold capture. Requires every live surface
# index in 1..255, an exact match at hardware entry 256*id + index, no write to
# either 256-entry block boundary, and failure of both the rejected zero-based
# payload and a one-bank perturbation. Skips cleanly with no live capture.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_frontend_cram.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend CRAM readback verification failed with exit code $LASTEXITCODE."
}

# Live frontend VDP1 object proof from the same hold capture: every held
# frame is compared against the ROM-derived converter manifest and the
# MAME-measured interaction evidence, reporting geometry, colour, order and
# timing as independent results, with four negative controls. Declared gaps
# (the VDP2 confirmation shutter and the Round 1 title) are printed, not
# normalised.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_frontend_objects.py')
if ($LASTEXITCODE -ne 0) {
    throw "Frontend VDP1 object verification failed with exit code $LASTEXITCODE."
}

# Complete-interval confirmation-shutter proof: every cadence-1 source frame
# from the last marker activity to the Round 1 text appearance must be
# explained by cap_confirm_shutter_band() - rows inside the band identical to
# the pre-shutter baseline, rows outside pure black - with four negative
# controls (start shift, band shift, two wrong rates). Skips cleanly without
# the private capture.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_confirm_shutter.py')
if ($LASTEXITCODE -ne 0) {
    throw "Confirmation shutter verification failed with exit code $LASTEXITCODE."
}

# RP2 route census structural contract: the tracked census must tile the
# complete captured route with unique provisional (bit-15) scene IDs and no
# gaps, and the recorded negative controls must have passed. Offline check
# against the tracked JSON only; the private capture is not required.
if (Test-Path (Join-Path $PSScriptRoot 'data\round1_route_census.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\verify_route_census.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Route census verification failed with exit code $LASTEXITCODE."
    }
}

# RP4 fixture/production separation: the captured street strips and object
# schedule are a validation fixture; this gate fails if main.c references
# them outside AVSP_STREET_TEST, if the tracked manifest loses its
# fixture_role classification, or if a non-StreetTest build left the fixture
# staged in the ISO content root.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_fixture_separation.py')
if ($LASTEXITCODE -ne 0) {
    throw "Fixture separation gate failed with exit code $LASTEXITCODE."
}

# RP4 street plane proof: full offline reconstruction of the representative
# interval (structural checks on all 201 frames, pixel comparison on the
# sampled set, eight negative controls). Requires the private full-route
# capture and the generated fixture; skipped when either is absent.
if ((Test-Path (Join-Path $PSScriptRoot '.deps\mame\full_route\region_index.tsv')) -and
        (Test-Path (Join-Path $PSScriptRoot 'build\rp4_fixture\STRIPS.BIN'))) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\verify_street_planes.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Street plane verification failed with exit code $LASTEXITCODE."
    }
}

# RP6 semantic scene manifest: must tile the census route exactly, carry
# recomputable content-addressed stable IDs, a consistent transition
# chain, and evidence-bound labels (unlabeled scenes need review flags).
# Offline check against tracked JSON only.
if (Test-Path (Join-Path $PSScriptRoot 'data\avsp_scene_manifest.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\verify_scene_manifest.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Scene manifest verification failed with exit code $LASTEXITCODE."
    }
}

# RP5 residency ledger: every recorded profile must sit under the work-RAM
# limit, carve arithmetic must recompute, bounded resources must show
# non-negative headroom, and each section needs a MEASURED/ADAPTED/GAP
# status. Offline check against tracked JSON only.
if (Test-Path (Join-Path $PSScriptRoot 'data\avsp_residency_budget.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\verify_residency_budget.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Residency budget verification failed with exit code $LASTEXITCODE."
    }
}

# SP10 row-scroll classification: per-scene verdicts must recompute from
# the recorded counts and match the census ranges. Offline, capture-free.
if (Test-Path (Join-Path $PSScriptRoot 'data\round1_rowscroll_classification.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\verify_rowscroll_classification.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Row-scroll classification verification failed with exit code $LASTEXITCODE."
    }
}

# Sub-state dispatcher enumeration: decodes, from the validated opcode-space
# image, every per-actor sub-state jump table (actor byte +0x04 indexes a
# PC-relative word table). Self-tests against the three live-confirmed
# table_set initializers and a perturbation control. Skips cleanly without
# the private opcode dump.
& $PythonPath (Join-Path $PSScriptRoot 'tools\extract_avsp_dispatchers.py')
if ($LASTEXITCODE -ne 0) {
    throw "Sub-state dispatcher extraction failed with exit code $LASTEXITCODE."
}

# Corpus falsification of that structural claim: over every active
# actor-frame in the captured routes, +0x04 must be an even, in-range word
# index, with a negative control on the neighbouring byte that must fail.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_avsp_substate_model.py')
if ($LASTEXITCODE -ne 0) {
    throw "Sub-state model falsification failed with exit code $LASTEXITCODE."
}

# Master actor dispatch: the per-class routine table the live-traced actor
# loop indexes with actor byte +0x02, and its corpus falsification. Resolves
# what calls into a sub-state dispatcher. Both skip cleanly without the
# private opcode dump / captures.
& $PythonPath (Join-Path $PSScriptRoot 'tools\extract_avsp_actor_classes.py')
if ($LASTEXITCODE -ne 0) {
    throw "Actor class-table extraction failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_avsp_actor_classes.py')
if ($LASTEXITCODE -ne 0) {
    throw "Actor class-dispatch falsification failed with exit code $LASTEXITCODE."
}

# Per-state table_set body (offline): bounded state-0 span decode of each
# street-class routine - from the dispatch target the handler span is
# decoded as far as the sequential decoder stays clean (the handlers
# embed inline data tables, where the clean decode stops and the tail is
# recorded), and the state-0 class-entry immediate store is the sole +0x50
# writer in the proven code region, cross-matched PC and value against
# the live-trace families. Plus byte-exact re-verification of each
# class's sub-state dispatch table and the second-level dispatch idiom.
# Skips cleanly without the private opcode dump and manifests.
& $PythonPath (Join-Path $PSScriptRoot 'tools\extract_avsp_table_set_states.py')
if ($LASTEXITCODE -ne 0) {
    throw "Per-state table_set extraction failed with exit code $LASTEXITCODE."
}

# Semantic anchor + corpus falsification of that claim: the captured
# enemy_action actor (RAM 0xffa000) must carry its class constant in
# every frame of its cited HIT and KO clips. Their animation-record sets
# define conservatively named anchor-record-signature populations; they do
# not promote action/sub-state correlations to semantic HIT/KO labels. The
# constant must stay unchanged for every active street frame in all four
# deterministic MAME routes, with exclusive lifecycle accounting and one
# corrupted-constant control for every populated class.
& $PythonPath (Join-Path $PSScriptRoot 'tools\verify_avsp_table_set_states.py')
if ($LASTEXITCODE -ne 0) {
    throw "Per-state table_set corpus falsification failed with exit code $LASTEXITCODE."
}

# Stage layer scroll rates: does any route scroll its CPS tilemap layers at
# different rates, i.e. need parallax that one flattened VDP2 bitmap cannot
# express? Register words and counts only. Skips cleanly without captures.
& $PythonPath (Join-Path $PSScriptRoot 'tools\analyze_avsp_stage_scroll.py')
if ($LASTEXITCODE -ne 0) {
    throw "Stage scroll analysis failed with exit code $LASTEXITCODE."
}

# Tile-archive palette coverage, plus the test that pins the known gap open so
# the archive scope cannot be widened without widening the palette.
& $PythonPath (Join-Path $PSScriptRoot 'tools\analyze_avsp_palette_coverage.py')
if ($LASTEXITCODE -ne 0) {
    throw "Palette coverage analysis failed with exit code $LASTEXITCODE."
}

& $PythonPath (Join-Path $PSScriptRoot 'tests\test_avsp_palette_coverage.py')
if ($LASTEXITCODE -ne 0) {
    throw "Palette coverage test failed with exit code $LASTEXITCODE."
}

# Saturn VDP1 command-table model: reachable-versus-stored traversal. No
# private inputs; fixtures are built in memory.
& $PythonPath (Join-Path $PSScriptRoot 'tests\test_avsp_vdp1_model.py')
if ($LASTEXITCODE -ne 0) {
    throw "VDP1 command-model test failed with exit code $LASTEXITCODE."
}

# Tranche 1 unified cold-boot semantic oracle and executable writer boundary.
# The self-tests always prove schema/classification rejection controls.  The
# private MAME runs are present only in the implementation worktree; when they
# are available, regenerate the public hash/count manifests and require their
# complete two-run/perturbation and PC/edge coverage gates to pass.
& $PythonPath (Join-Path $PSScriptRoot 'tests\test_avsp_vertical_slice_oracle.py')
if ($LASTEXITCODE -ne 0) {
    throw "Vertical-slice oracle schema/control test failed with exit code $LASTEXITCODE."
}
& $PythonPath (Join-Path $PSScriptRoot 'tests\test_avsp_translation_boundary.py')
if ($LASTEXITCODE -ne 0) {
    throw "Translation-boundary classification/control test failed with exit code $LASTEXITCODE."
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\oracle07_predator_warrior_action_graph_equipment.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_oracle07_player_action.py')
    if ($LASTEXITCODE -ne 0) {
        throw "ORACLE-07 player action/equipment test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\oracle08_round1_navigation_bounds.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_oracle08_navigation.py')
    if ($LASTEXITCODE -ne 0) {
        throw "ORACLE-08 navigation/bounds test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\oracle09_street_alien_state_facing_presentation.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_oracle09_alien_state.py')
    if ($LASTEXITCODE -ne 0) {
        throw "ORACLE-09 alien state/facing/presentation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec01_first_live_encounter_executable_contract.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec01_encounter_contract.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-01 executable encounter contract test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class00_type12_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class00_type12.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x00/type-12 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class00_type12.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x00/type-12 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class01_type12_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class01_type12.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x01/type-12 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class01_type12.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x01/type-12 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class06_type12_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class06_type12.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x06/type-12 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class06_type12.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x06/type-12 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class07_type20_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class07_type20.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x07/type-20 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class07_type20.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x07/type-20 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class10_type24_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class10_type24.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x10/type-24 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class10_type24.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x10/type-24 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class3d_type24_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class3d_type24.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x3d/type-24 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class3d_type24.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x3d/type-24 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class49_type24_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class49_type24.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x49/type-24 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class49_type24.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x49/type-24 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class4b_type24_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class4b_type24.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x4b/type-24 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class4b_type24.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x4b/type-24 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_class4e_type24_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_class4e_type24.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x4e/type-24 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_class4e_type24.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 class-0x4e/type-24 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_c200_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_c200_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x00c200 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_c200.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x00c200 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_8546_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_8546_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x008546 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_8546.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x008546 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_8bb2_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_8bb2_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x008bb2 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_8bb2.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x008bb2 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_90f2_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_90f2_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x0090f2 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_90f2.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x0090f2 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_8418_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_8418_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x008418 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_8418.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x008418 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_c886_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_c886_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x00c886 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_c886.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x00c886 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_route_83d4_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_route_83d4_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x0083d4 generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_route_83d4.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 route-0x0083d4 mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_presentation_audio_owner_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_presentation_audio_owner_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 presentation-audio owner generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_presentation_audio_owner.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 presentation-audio owner mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_projectile_audio_owner_program.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\build_spec02_projectile_audio_owner_program.py') '--check'
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 projectile-audio owner generation check failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_projectile_audio_owner.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 projectile-audio owner mutation test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\spec02_round1_executable_contract.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tests\test_spec02_round1_contract.py')
    if ($LASTEXITCODE -ne 0) {
        throw "SPEC-02 Round 1 executable contract test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'tests\port_v2\integration\source_closed_live_encounter\test_contract.py')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tests\port_v2\integration\source_closed_live_encounter\test_contract.py')
    if ($LASTEXITCODE -ne 0) {
        throw "REIMPLEMENT-12 source-closed encounter test failed with exit code $LASTEXITCODE."
    }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.deps\mame\vertical_slice\input_manifest.json')) {
    & $PythonPath (Join-Path $PSScriptRoot 'tools\verify_avsp_vertical_slice_oracle.py') '--generate'
    if ($LASTEXITCODE -ne 0) {
        throw "Vertical-slice oracle generation failed with exit code $LASTEXITCODE."
    }
    & $PythonPath (Join-Path $PSScriptRoot 'tools\map_avsp_translation_boundary.py') '--generate'
    if ($LASTEXITCODE -ne 0) {
        throw "Translation-boundary generation failed with exit code $LASTEXITCODE."
    }
}
