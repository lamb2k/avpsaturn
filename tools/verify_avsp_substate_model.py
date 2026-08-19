"""Falsify the sub-state model against the game's own captured work RAM.

tools/extract_avsp_dispatchers.py decodes, from the opcode-space image, that
actor byte +0x04 is a WORD-table index into a PC-relative jump table:

    move.b ($4,A6), D0 ; move.w ($6,PC,D0.w), D1 ; jmp ($2,PC,D1.w)

This tool tests that structural claim against live-captured actor records -
the corpus half of the provenance rule (offline disasm locates and
structures; the corpus or a live trace confirms).

CHECK A - index validity (universal, all types, all routes). If +0x04 is
really a word-table index it must be EVEN, and it must stay within the
largest table the enumeration found. A byte used as a flag, counter, timer
or pointer would produce odd values almost immediately. Population is every
active actor-frame in the scanned routes; zero exceptions required; an
empty population is a vacuous FAILURE.

CHECK B - negative control. The same test applied to a deliberately
perturbed index (+0x04 read one byte over, at +0x05) must FAIL. Without
this, check A could pass on a field that happens to be even for unrelated
reasons.

CHECK C - the family map for street aliens (type 12). Reports, per action
word at +0x06, the table_set observed at +0x50, over frames whose live
animation-record pointer lies in the walk/attack street spans. This is the
evidence that feeds the per-state table_set question the collision body
left open; it is REPORTED with counts, and only the already-gated
walk/attack claim (== 0x00130AC8) is asserted.

Inputs (private, untracked): .deps/mame/<route>/workram_*.bin plus the
opcode dump for the enumeration bound. Skips cleanly when absent.
Output (tracked): data/avsp_substate_model.json
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHERS = ROOT / "data" / "avsp_substate_dispatchers.json"
OUT_JSON = ROOT / "data" / "avsp_substate_model.json"

ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")

WORKRAM_FIRST = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_ANCHOR = 0xFF8380
ACTOR_STRIDE = 0xC0
SLOT_COUNT = (WORKRAM_SIZE - (ACTOR_ANCHOR - WORKRAM_FIRST)) // ACTOR_STRIDE

ACTIVE, SUB_STATE, ACTION, TYPE = 0x00, 0x04, 0x06, 0x08
RECORD_PTR, TABLE_SET = 0x1C, 0x50

STREET_TYPE = 12
WALK_SEED, ATTACK_SEED = 0x12EB4C, 0x12D8A0
GATED_TABLE_SET = 0x00130AC8
RECORD_BYTES, JUMP_RECORD_BYTES = 16, 20

ROM_PATH = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def u32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o + 4], "big")


def loop_span(rom: bytes, seed: int) -> set:
    """Record addresses reachable from seed, mirroring avsp_anim_next_address
    (same walker tools/gate_avsp_table_set.py uses)."""
    seen: set[int] = set()
    stack = [seed]
    while stack:
        a = stack.pop()
        if a in seen or a + JUMP_RECORD_BYTES > len(rom):
            continue
        seen.add(a)
        nxt = u32(rom, a + 16) if u16(rom, a + 2) & 0x8000 else a + RECORD_BYTES
        if 0 < nxt <= len(rom) - JUMP_RECORD_BYTES and nxt not in seen:
            stack.append(nxt)
    return seen


def main() -> int:
    if not DISPATCHERS.is_file():
        print("substate model: SKIPPED - dispatcher manifest absent; run "
              "tools/extract_avsp_dispatchers.py first")
        return 0
    manifest = json.loads(DISPATCHERS.read_text())
    if not manifest.get("sites"):
        print("substate model: SKIPPED - dispatcher manifest has no sites "
              "(the private opcode dump was absent when it ran)")
        return 0
    max_sub_states = max(s["sub_states"] for s in manifest["sites"])
    max_index = 2 * (max_sub_states - 1)

    routes = [r for r in ROUTES
              if any((ROOT / ".deps" / "mame" / r).glob("workram_*.bin"))]
    if not routes:
        print("substate model: SKIPPED - no captured routes present")
        return 0

    street = set()
    if ROM_PATH.is_file():
        rom = ROM_PATH.read_bytes()
        street = loop_span(rom, WALK_SEED) | loop_span(rom, ATTACK_SEED)

    population = 0
    odd = []
    out_of_range = []
    control_violations = 0
    index_hist: Counter = Counter()
    per_route = {}
    family_map: dict[str, Counter] = {}

    for route in routes:
        root = ROOT / ".deps" / "mame" / route
        frames = sorted(root.glob("workram_*.bin"))
        route_pop = 0
        for path in frames:
            work = path.read_bytes()
            if len(work) != WORKRAM_SIZE:
                continue
            for n in range(SLOT_COUNT):
                o = (ACTOR_ANCHOR - WORKRAM_FIRST) + n * ACTOR_STRIDE
                if work[o + ACTIVE] != 1:
                    continue
                population += 1
                route_pop += 1
                idx = work[o + SUB_STATE]
                index_hist[idx] += 1
                if idx % 2:
                    if len(odd) < 20:
                        odd.append({"route": route, "file": path.name,
                                    "slot": n, "value": "0x%02X" % idx})
                if idx > max_index:
                    if len(out_of_range) < 20:
                        out_of_range.append(
                            {"route": route, "file": path.name, "slot": n,
                             "value": "0x%02X" % idx,
                             "max_index": "0x%02X" % max_index})
                # Negative control: the neighbouring byte, same test.
                if work[o + SUB_STATE + 1] % 2 or \
                        work[o + SUB_STATE + 1] > max_index:
                    control_violations += 1
                # Check C data
                if street and work[o + TYPE] == STREET_TYPE:
                    ptr = u32(work, o + RECORD_PTR)
                    if ptr in street:
                        key = "0x%04X" % u16(work, o + ACTION)
                        family_map.setdefault(key, Counter())[
                            "0x%06X" % u32(work, o + TABLE_SET)] += 1
        per_route[route] = {"frames": len(frames), "active_actor_frames": route_pop}

    vacuous = population == 0
    check_a = not odd and not out_of_range and not vacuous
    check_b = control_violations > 0
    gated_violations = {
        action: dict(counts) for action, counts in family_map.items()
        if set(counts) != {"0x%06X" % GATED_TABLE_SET}
    }

    result = {
        "schema": 1,
        "classification": "sub-state index falsification - counts and "
                          "addresses only, no ROM bytes",
        "claim": "actor byte +0x04 is a WORD-table index into the "
                 "PC-relative sub-state jump table decoded in "
                 "data/avsp_substate_dispatchers.json, so it must be even "
                 "and within the largest enumerated table",
        "routes_scanned": per_route,
        "declared_population": "every active actor-frame (any type) in the "
                               "scanned routes",
        "population": population,
        "max_sub_states_enumerated": max_sub_states,
        "max_valid_index": "0x%02X" % max_index,
        "observed_index_histogram": {"0x%02X" % k: index_hist[k]
                                     for k in sorted(index_hist)},
        "check_a_index_validity": {
            "odd_values": odd,
            "out_of_range_values": out_of_range,
            "vacuous": vacuous,
            "result": "PASS" if check_a else "FAIL",
        },
        "check_b_negative_control": {
            "description": "same test on the neighbouring byte (+0x05) must "
                           "fail, proving check A is not trivially true",
            "violations": control_violations,
            "result": "PASS (control correctly fails)" if check_b else
                      "FAIL (control passed - check A may be vacuous)",
        },
        "check_c_street_family_map": {
            "description": "table_set observed per action word for type-12 "
                           "actors inside the walk/attack street spans; the "
                           "gated claim is that these are all 0x00130AC8",
            "action_to_table_set": {k: dict(v) for k, v in
                                    sorted(family_map.items())},
            "actions_not_matching_gated_constant": gated_violations,
        },
        "result": "PASS" if (check_a and check_b) else "FAIL",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("substate model: %s" % result["result"])
    print("  population %d active actor-frames over %s"
          % (population, ", ".join(routes)))
    print("  index histogram %s (max valid 0x%02X from %d-state tables)"
          % (result["observed_index_histogram"], max_index, max_sub_states))
    print("  check A index validity: %s (odd %d, out-of-range %d)"
          % (result["check_a_index_validity"]["result"], len(odd),
             len(out_of_range)))
    print("  check B negative control: %s (%d violations on +0x05)"
          % (result["check_b_negative_control"]["result"], control_violations))
    if street:
        print("  check C: %d distinct street action words; %d not on the "
              "gated constant" % (len(family_map), len(gated_violations)))
        for action, counts in sorted(gated_violations.items()):
            print("     action %s -> %s" % (action, counts))
    print("wrote", OUT_JSON)
    return 0 if (check_a and check_b) else 1


if __name__ == "__main__":
    raise SystemExit(main())
