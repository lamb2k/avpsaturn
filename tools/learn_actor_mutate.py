#!/usr/bin/env python
"""Sensitivity check for the actor gate: each deliberate wrong constant must make its unit FAIL.
usage: learn_actor_mutate.py [UNIT] [CASES]   Restores the source after each mutation. Mutated runs use --no-record,
so they never reach gate_runs.tsv. A gate run while this runs in the same worktree would see mutated source."""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "source_recon/avsrc_actor.c"
M = [
    ("RAM16W(m, p->top_addr, top + 2);", "RAM16W(m, p->top_addr, top + 4);", "pool_alloc_5"),
    ("0x4c, 0x46, 0x70", "0x4c, 0x70", "pool_release_2"),
    ("(u32)RAM8(m, slot + ACT_CLASS) * 4u", "(u32)RAM8(m, slot + ACT_CLASS) * 8u", "pool_traverse_5"),
    ("--RAM8(m, slot + ACT_FLASH_LEFT) == 0", "--RAM8(m, slot + ACT_FLASH_LEFT) == 1", "pool_traverse_2"),
    ("0x90c0", "0x90c1", "pools_reset"),
    ("if (camera > RAM16(m, G_CAMERA_X)) return;", "if (camera >= RAM16(m, G_CAMERA_X)) return;", "spawn_table_step"),
    ("#define SPAWN_FACING    0x0cu", "#define SPAWN_FACING    0x0du", "spawn_table_step"),
    ("return gate <= difficulty;", "return gate < difficulty;", "spawn_table_step"),
    ("(0x100u - gate) & 0xffu) > difficulty", "(0x100u - gate) & 0xffu) >= difficulty", "spawn_table_step"),
    ("damage = reduced(damage, 2);", "damage = reduced(damage, 1);", "damage_apply"),
    ("RAM16(m, defender + ACT_HEALTH) < 6", "RAM16(m, defender + ACT_HEALTH) < 5", "damage_apply"),
    ("? 1u : 0u", "? 2u : 0u", "damage_apply"),
    ("|| h < 6) h = 0", "|| h < 7) h = 0", "player_energy_drain"),
    ("if (h == 0) h = 5;", "if (h == 0) h = 4;", "pickup_heal"),
    ("(u8)(face ^ 1u)", "(u8)face", "hit_commit_single"),
    ("if (RAM8(m, attacker + ACT_HITSTOP) == 0) RAM8", "RAM8", "hit_commit_player"),
    ("if (RAM8(m, defender + ACT_TAG) == 0) avsrc_actor_call(m, 0x1d73au, 0);", "", "hit_commit_single"),
    ("!(RAM8(m, attacker + ACT_ROW65) & 0x80u)", "1", "hit_commit_row65"),
    ("ACT_TIMER2A, 0x30)", "ACT_TIMER2A, 0x31)", "emitter_tick"),
    ("0x1004", "0x1005", "emitter_tick"),
]
CASES = sys.argv[2] if len(sys.argv) > 2 else "200"
orig = SRC.read_bytes()
survived = 0
try:
    for old, new, unit in M:
        if len(sys.argv) > 1 and unit != sys.argv[1]:
            continue
        text = orig.decode()
        if text.count(old) != 1:
            print("NOT APPLICABLE", old, text.count(old))
            survived += 1
            continue
        SRC.write_bytes(text.replace(old, new).encode())
        r = subprocess.run([sys.executable, str(REPO / "tools/learn_unit.py"), unit, CASES, "--no-record"], capture_output=True, text=True)
        killed = r.returncode != 0 and "FAIL" in r.stdout
        print("killed" if killed else "SURVIVED", unit, "|", old[:50])
        survived += not killed
finally:
    SRC.write_bytes(orig)
print("survived", survived)
sys.exit(1 if survived else 0)
