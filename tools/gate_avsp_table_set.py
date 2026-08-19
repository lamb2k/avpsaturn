"""Step 1 GATE - prove the runtime table_set constant before any wiring.

This is the offline gate that must pass, in the same turn, before any
runtime `table_set` is wired to the decoded street-alien collision. It
proves, over the stride-1 street capture, that the constant is safe:

  For every stride-1 street-route frame in which a type-12 actor's live
  animation-record pointer (actor +0x1C) lies inside the walk loop (seed
  0x12EB4C) or attack loop (seed 0x12D8A0) record spans, that actor's
  table_set (actor +0x50) equals 0x00130AC8. Zero exceptions.

Design constraints (binding for this task):

  * The population is declared before counting and every exclusion is named.
  * This tool does NOT import spawn_type() from the stride-1 decoder -
    that is a capture-context classifier, not game logic. It walks the
    ROM's own animation control flow from the two street seeds and tests
    the raw per-frame work-RAM actor records directly.
  * A gate that sees zero eligible frames proves nothing, so eligible == 0
    is a FAILURE (vacuous), not a skip.

Inputs (private, untracked):
  .deps/mame/actorprobe/decrypted_program_2m.bin   the 2 MB program image
  .deps/mame/enemy_actions/workram_*.bin           the stride-1 street route
  .deps/mame/{stalker_actions,boss_actions,boss_ko}/workram_*.bin  (context)

Output (tracked):
  data/avsp_table_set_gate.json  declared population, named exclusions,
                                 per-route result, span sizes, ROM hash.

Contract for test.ps1: if the program image or the street captures are
absent the gate skips cleanly (exit 0) - the same contract as the private-
input C tests - and the committed manifest records the run where inputs were
present. If the inputs are present, ANY exception in the gate population
exits nonzero so the wiring is not allowed to proceed.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
GATE_ROUTE = "enemy_actions"                     # the street route
CONTEXT_ROUTES = ("stalker_actions", "boss_actions", "boss_ko")
OUT_JSON = ROOT / "data" / "avsp_table_set_gate.json"

WORKRAM_FIRST = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_ANCHOR = 0xFF8380
ACTOR_STRIDE = 0xC0
TARGET_TYPE = 12
EXPECTED_TABLE_SET = 0x00130AC8

# The two live-verified street-alien loops the runtime's ADAPTED action
# bridge (rom_actor_tick) drives: the walk and the attack.
WALK_SEED = 0x12EB4C
ATTACK_SEED = 0x12D8A0

RECORD_BYTES = 16
JUMP_RECORD_BYTES = 20
ACTIVE_BYTE = 0x00
TYPE_BYTE = 0x08
RECORD_PTR = 0x1C
TABLE_SET = 0x50


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def u32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o + 4], "big")


def loop_span(rom: bytes, seed: int) -> set:
    """Record addresses reachable from `seed` following the script's own
    control flow (16-byte advance; 20-byte jump to the u32 at +16 when flags
    bit 15 is set). Mirrors avsp_anim_next_address exactly - the same walker
    the runtime uses to advance these loops. A loop closes when a record is
    revisited, so the reachable set IS the loop's record span."""
    seen = set()
    stack = [seed]
    while stack:
        a = stack.pop()
        if a in seen or a + JUMP_RECORD_BYTES > len(rom):
            continue
        seen.add(a)
        if u16(rom, a + 2) & 0x8000:
            nxt = u32(rom, a + 16)
        else:
            nxt = a + RECORD_BYTES
        if 0 < nxt <= len(rom) - JUMP_RECORD_BYTES and nxt not in seen:
            stack.append(nxt)
    return seen


def frame_path_number(path: Path) -> int:
    try:
        return int(path.stem.split("_")[-1])
    except ValueError:
        return -1


def scan_route(rom: bytes, route: str, street: set) -> dict:
    """One route, stride-1. Returns the declared population, the named
    exclusions, the eligible table_set distribution, and any exceptions."""
    root = ROOT / ".deps" / "mame" / route
    frames = sorted(root.glob("workram_*.bin")) if root.is_dir() else []
    slot_count = (WORKRAM_SIZE - (ACTOR_ANCHOR - WORKRAM_FIRST)) // ACTOR_STRIDE

    frames_scanned = 0
    excluded_inactive = 0
    excluded_non_target = 0
    excluded_out_of_span = 0
    excluded_ptr_unreadable = 0
    eligible = 0
    table_set_dist = Counter()
    exceptions = []

    for path in frames:
        work = path.read_bytes()
        if len(work) != WORKRAM_SIZE:
            continue
        frames_scanned += 1
        fn = frame_path_number(path)
        for n in range(slot_count):
            o = (ACTOR_ANCHOR - WORKRAM_FIRST) + n * ACTOR_STRIDE
            if work[o + ACTIVE_BYTE] != 1:
                excluded_inactive += 1
                continue
            if work[o + TYPE_BYTE] != TARGET_TYPE:
                excluded_non_target += 1
                continue
            ptr = u32(work, o + RECORD_PTR)
            if not (0 < ptr <= len(rom) - JUMP_RECORD_BYTES):
                excluded_ptr_unreadable += 1
                continue
            if ptr not in street:
                excluded_out_of_span += 1
                continue
            eligible += 1
            t = u32(work, o + TABLE_SET)
            table_set_dist["0x%06X" % t] += 1
            if t != EXPECTED_TABLE_SET:
                exceptions.append({
                    "route": route, "frame": fn, "slot": n,
                    "record_ptr": "0x%06X" % ptr,
                    "table_set": "0x%06X" % t,
                })
    return {
        "route": route,
        "frames_scanned": frames_scanned,
        "declared_population": (
            "active type-12 actor-frames whose +0x1C record pointer lies in "
            "the walk/attack street spans"),
        "eligible": eligible,
        "table_set_distribution": dict(table_set_dist),
        "exceptions": exceptions,
        "exclusions": {
            "inactive_actors": excluded_inactive,
            "non_type_12_actors": excluded_non_target,
            "type_12_record_ptr_outside_street_spans": excluded_out_of_span,
            "type_12_record_ptr_unreadable": excluded_ptr_unreadable,
        },
    }


def main() -> int:
    if not ROM_PATH.is_file():
        print("gate: SKIPPED - program image absent (%s); "
              "committed manifest records the run with inputs present"
              % ROM_PATH.relative_to(ROOT).as_posix())
        return 0
    street_root = ROOT / ".deps" / "mame" / GATE_ROUTE
    if not any(street_root.glob("workram_*.bin")):
        print("gate: SKIPPED - street captures absent (%s); "
              "committed manifest records the run with inputs present"
              % GATE_ROUTE)
        return 0

    rom = ROM_PATH.read_bytes()
    walk_span = loop_span(rom, WALK_SEED)
    attack_span = loop_span(rom, ATTACK_SEED)
    street = walk_span | attack_span

    gate = scan_route(rom, GATE_ROUTE, street)
    context = [scan_route(rom, r, street) for r in CONTEXT_ROUTES]

    gate_exceptions = len(gate["exceptions"])
    context_exceptions = sum(len(c["exceptions"]) for c in context)
    vacuous = gate["eligible"] == 0

    passed = (gate_exceptions == 0) and (not vacuous)

    result = {
        "schema": 1,
        "classification": "step-1 offline gate - proves the runtime street-"
                          "alien table_set constant, no correlation, no "
                          "spawn_type",
        "gate": (
            "for every stride-1 street-route frame in which a type-12 actor's "
            "live record pointer (+0x1C) lies inside the walk (0x12EB4C) or "
            "attack (0x12D8A0) record spans, its table_set (+0x50) equals "
            "0x00130AC8; zero exceptions; vacuous (eligible==0) is a failure"),
        "expected_table_set": "0x%06X" % EXPECTED_TABLE_SET,
        "walk_seed": "0x%06X" % WALK_SEED,
        "attack_seed": "0x%06X" % ATTACK_SEED,
        "walk_span_records": len(walk_span),
        "attack_span_records": len(attack_span),
        "street_span_records": len(street),
        "program_image": {
            "path": ROM_PATH.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(rom).hexdigest(),
            "bytes": len(rom),
        },
        "gate_route": GATE_ROUTE,
        "gate_population": gate["declared_population"],
        "gate_frames_scanned": gate["frames_scanned"],
        "gate_eligible": gate["eligible"],
        "gate_table_set_distribution": gate["table_set_distribution"],
        "gate_exclusions": gate["exclusions"],
        "gate_exceptions": gate["exceptions"],
        "context_routes": [
            {
                "route": c["route"],
                "frames_scanned": c["frames_scanned"],
                "eligible": c["eligible"],
                "table_set_distribution": c["table_set_distribution"],
                "exceptions": c["exceptions"],
            }
            for c in context
        ],
        "context_exceptions": context_exceptions,
        "vacuous": vacuous,
        "result": (
            "PASS - %d/%d street-span type-12 frames carry 0x%06X, zero "
            "exceptions" % (gate["eligible"] - gate_exceptions,
                            gate["eligible"], EXPECTED_TABLE_SET)
            if passed else
            ("FAIL (vacuous) - no street-span type-12 frame observed"
             if vacuous else
             "FAIL - %d street-span exception(s)" % gate_exceptions)),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("gate: %s" % result["result"])
    print("  walk span=%d attack span=%d street union=%d records"
          % (len(walk_span), len(attack_span), len(street)))
    print("  gate route=%s frames=%d eligible=%d distribution=%s"
          % (GATE_ROUTE, gate["frames_scanned"], gate["eligible"],
             gate["table_set_distribution"]))
    print("  exclusions: %s" % gate["exclusions"])
    for c in context:
        print("  context %s: eligible=%d exceptions=%d"
              % (c["route"], c["eligible"], len(c["exceptions"])))
    print("wrote", OUT_JSON)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
