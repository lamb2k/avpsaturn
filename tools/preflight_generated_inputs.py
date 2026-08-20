#!/usr/bin/env python3
"""Clean-checkout preflight for private generated inputs.

The build compiles against ignored ROM-derived headers under generated/.
On a clean checkout those files do not exist, and before this preflight
the build failed midway with a bare missing-include error
(generated/avsp_emit_windows.h, then generated/avsp_boss_rom.h, ...).

This tool derives the REQUIRED header set from the tracked sources'
`#include "generated/..."` lines (so new includes cannot silently dodge
the mapping), and maps every required header to its producer:

- `command` producers are deterministic Python generators this preflight
  can run itself when the header is missing and the private inputs
  exist;
- `stage` producers are build-script stages (prepare_avsp_port.ps1,
  prepare_*audio*.ps1, gen_avsp_frontend.py, ...) that build.ps1 runs
  before this preflight; a header still missing here names its stage.

Modes:
  --check-mapping  capture-free: every required header is mapped and the
                   loader sources exist (used by test.ps1);
  default          ensure: run command producers for missing headers when
                   their inputs exist; fail with the exact missing
                   generator or input otherwise (used by build.ps1
                   after the prepare stages, before make).

No ROM-derived bytes are read or written by the mapping itself.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRACKED_SOURCE_GLOBS = ("*.c", "*.h", "tests/*.c")

LOADER_SOURCES = (
    "loader/loader.c",
    "loader/trampoline.s",
    "loader/loader.linker",
    "tools/build_loader_ip.py",
)

PY = [sys.executable]

# Producer map. `inputs` are the private files/directories whose absence
# is the bounded failure message; command producers are re-runnable and
# deterministic.
PRODUCERS: dict[str, dict] = {
    "avsp_emit_windows.h": {
        "command": PY + ["tools/gen_avsp_emit_windows.py"],
        "inputs": [".deps/mame/actorprobe/decrypted_program_2m.bin"],
    },
    "avsp_boss_rom.h": {
        # Reads generated/avsp_boss_animation.h, so its stage-produced
        # dependency must exist first; the preflight runs after the
        # prepare stages in build.ps1, which guarantees that ordering.
        "command": PY + ["tools/gen_boss_rom_data.py"],
        "inputs": [".deps/mame/actorprobe", "data/boss_play_sequence.json",
                   "generated/avsp_boss_animation.h"],
    },
    "avsp_boss_animation.h": {
        "stage": "prepare_avsp_port.ps1 extract_avspu_stage1.py step",
        "inputs": ["avspu"],
    },
    "avsp_collision.h": {
        "command": PY + ["tools/decode_avsp_collision.py",
                         "--rom",
                         ".deps/mame/actorprobe/decrypted_program_2m.bin",
                         "--census-workram",
                         ".deps/mame/collision_probe/workram.bin",
                         "--census-workram",
                         ".deps/mame/collision_probe_boss/workram.bin"],
        "inputs": [".deps/mame/actorprobe/decrypted_program_2m.bin",
                   ".deps/mame/collision_probe/workram.bin",
                   ".deps/mame/collision_probe_boss/workram.bin"],
    },
    "avsp_anim_records.h": {
        "stage": "build.ps1 gen_avsp_anim_records.py step",
        "inputs": [".deps/mame"],
    },
    "avsp_frontend.h": {
        "stage": "build.ps1 gen_avsp_frontend.py step",
        "inputs": [".deps/mame/frontend_rom"],
    },
    "avsp_table_set_classes.h": {
        "stage": "build.ps1 gen_avsp_table_set_classes.py step",
        "inputs": [".deps/mame"],
    },
    "avsp_stage1_route.h": {
        "stage": "prepare_avsp_port.ps1 generate_stage1_route.py step",
        "inputs": ["data/stage1_route.json", ".deps/mame"],
    },
}

# Headers produced by extract_avspu_stage1.py inside prepare_avsp_port.ps1.
for name in ("avsp_palette.h", "avsp_hud.h", "avsp_enemy_animation.h",
             "avsp_player_action_animation.h", "avsp_sequence_palette.h",
             "avsp_stalker_animation.h"):
    PRODUCERS[name] = {
        "stage": "prepare_avsp_port.ps1 extract_avspu_stage1.py step",
        "inputs": ["avspu"],
    }

# PCM descriptor headers produced by the prepare_*audio*.ps1 stages that
# build.ps1 runs before this preflight.
for name in ("avsp_audio.h", "avsp_boss_clear_audio.h",
             "avsp_boss_intro_audio.h", "avsp_breach_audio.h",
             "avsp_contact_audio.h", "avsp_door_dialogue_audio.h",
             "avsp_ko_contact_audio.h", "avsp_interior_transition_audio.h",
             "avsp_melee_audio.h", "avsp_round_title_a_audio.h",
             "avsp_round_title_b_audio.h", "avsp_withdraw_audio.h"):
    PRODUCERS[name] = {
        "stage": "build.ps1 prepare_*audio*.ps1 stages",
        "inputs": [".deps/mame"],
    }


def required_headers() -> set[str]:
    pattern = re.compile(r'#include\s+"generated/([A-Za-z0-9_.]+)"')
    found: set[str] = set()
    for glob in TRACKED_SOURCE_GLOBS:
        for source in ROOT.glob(glob):
            for match in pattern.finditer(
                    source.read_text(errors="replace")):
                found.add(match.group(1))
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-mapping", action="store_true",
                        help="capture-free mapping/loader coverage check")
    args = parser.parse_args()

    errors: list[str] = []
    for source in LOADER_SOURCES:
        if not (ROOT / source).exists():
            errors.append(f"missing staged-loader source: {source}")

    required = required_headers()
    unmapped = sorted(required - set(PRODUCERS))
    for name in unmapped:
        errors.append(f"generated/{name} is included by tracked sources "
                      f"but has no producer mapping in {Path(__file__).name}")

    if args.check_mapping:
        if errors:
            for error in errors:
                print("FAIL:", error)
            raise SystemExit(1)
        print(f"preflight mapping OK: {len(required)} generated headers "
              f"mapped, loader sources present")
        return

    for name in sorted(required & set(PRODUCERS)):
        header = ROOT / "generated" / name
        if header.exists():
            continue
        producer = PRODUCERS[name]
        missing = [i for i in producer["inputs"]
                   if not (ROOT / i).exists()]
        if missing:
            errors.append(
                f"generated/{name} is missing and its private inputs are "
                f"absent: {', '.join(missing)} "
                f"(producer: {producer.get('stage') or ' '.join(producer['command'][1:])})")
            continue
        if "command" not in producer:
            errors.append(
                f"generated/{name} is missing after its build stage "
                f"({producer['stage']}); run that stage or investigate "
                f"why it did not produce the header")
            continue
        print(f"preflight: generating generated/{name} via "
              f"{' '.join(producer['command'][1:])}")
        result = subprocess.run(producer["command"], cwd=ROOT)
        if result.returncode != 0 or not header.exists():
            errors.append(f"generated/{name}: producer exited "
                          f"{result.returncode} or produced nothing")

    if errors:
        for error in errors:
            print("FAIL:", error)
        raise SystemExit(1)
    print(f"preflight OK: {len(required)} generated headers present or "
          f"producible, loader sources present")


if __name__ == "__main__":
    main()
