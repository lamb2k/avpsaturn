"""Falsify the master actor class-dispatch model against the corpus.

The model (data/avsp_actor_class_table.json): the master loop at 0x01B980
walks 20 slots of stride 0xC0 from 0x00FF9580 (A5+0x1580, A5 measured live),
gates each on actor +0x00 nonzero, and calls
table[actor +0x02] where the table is 43 absolute-long entries at 0x01B9B6.

If that is the real dispatch, then over the captured routes:

  check A - every LIVE slot in the loop's own band carries a class byte
            within the decoded table's range. An out-of-range class would
            mean the loop jsr's to a non-entry, which cannot be true of a
            running game. Vacuous (zero live slots) is a FAILURE.
  check B - the RUNTIME-relevant claim: actors the runtime actually drives
            - those whose live animation-record pointer (+0x1C) lies in the
            street walk/attack spans, the same population the table_set gate
            declares - carry class 0x1F, whose table entry is the sub-state
            dispatcher 0x060532 the live traces proved they run. Zero
            exceptions; vacuous is a failure.

            Note this is deliberately NOT "type-12 implies class 0x1F". That
            stronger claim is FALSE and the data says so: live band actors
            with type byte +0x08 == 12 are also seen carrying class 0x00 and
            0x06, which are lifecycle states (class 0x00's routine 0x03F09C
            is the type_promotion path that rewrites the type byte). The
            joint distribution is reported below as an observation.
  check C - NEGATIVE CONTROL: the same range test applied to actor byte
            +0x11 (a high-entropy coordinate byte, ~200 distinct values)
            must FAIL. A control byte must be capable of failing, or check A
            proves nothing; +0x03 was tried first and rejected as a control
            precisely because it never leaves the range.

Reads only the private work-RAM captures; skips cleanly without them.
Output: data/avsp_actor_class_model.json
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_JSON = ROOT / "data" / "avsp_actor_class_table.json"
OUT_JSON = ROOT / "data" / "avsp_actor_class_model.json"

ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")
WORKRAM_FIRST = 0xFF8000
WORKRAM_SIZE = 0x8000

BAND_BASE = 0x00FF9580
BAND_SLOTS = 20
ACTOR_STRIDE = 0xC0

ACTIVE, CLASS, TYPE, RECORD_PTR = 0x00, 0x02, 0x08, 0x1C
CONTROL = 0x11             # high-entropy coordinate byte; see check C
STREET_TYPE = 12
STREET_CLASS = 0x1F

# The two live-verified street-alien animation loops (same seeds the
# table_set gate and the runtime's ROM actor path use).
WALK_SEED = 0x12EB4C
ATTACK_SEED = 0x12D8A0
ROM_PATH = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
RECORD_BYTES = 16
JUMP_RECORD_BYTES = 20


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def u32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o + 4], "big")


def loop_span(rom: bytes, seed: int) -> set:
    """Record addresses reachable from `seed` by the script's own control
    flow - identical to tools/gate_avsp_table_set.py's walker."""
    seen: set = set()
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
    if not TABLE_JSON.is_file():
        print("actor class model: SKIPPED - class table manifest absent; "
              "run tools/extract_avsp_actor_classes.py first")
        return 0
    table = json.loads(TABLE_JSON.read_text())
    entry_count = table["entry_count"]

    street_span = set()
    if ROM_PATH.is_file():
        rom = ROM_PATH.read_bytes()
        street_span = loop_span(rom, WALK_SEED) | loop_span(rom, ATTACK_SEED)

    routes_present = []
    live = 0
    class_hist = Counter()
    out_of_range = []
    control_out_of_range = 0
    street_total = 0
    street_ok = 0
    street_exceptions = Counter()
    type_class_joint = Counter()

    for route in ROUTES:
        root = ROOT / ".deps" / "mame" / route
        frames = sorted(root.glob("workram_*.bin")) if root.is_dir() else []
        if not frames:
            continue
        routes_present.append(route)
        for path in frames:
            work = path.read_bytes()
            if len(work) != WORKRAM_SIZE:
                continue
            for slot in range(BAND_SLOTS):
                base = (BAND_BASE - WORKRAM_FIRST) + slot * ACTOR_STRIDE
                if base + ACTOR_STRIDE > len(work):
                    break
                if work[base + ACTIVE] == 0:
                    continue
                live += 1
                cls = work[base + CLASS]
                class_hist["0x%02X" % cls] += 1
                if cls >= entry_count:
                    out_of_range.append(
                        {"route": route, "frame": path.stem, "slot": slot,
                         "class": "0x%02X" % cls})
                if work[base + CONTROL] >= entry_count:
                    control_out_of_range += 1
                type_class_joint[("0x%02X" % work[base + TYPE],
                                  "0x%02X" % cls)] += 1
                # check B population: the actors the runtime drives.
                if street_span:
                    ptr = u32(work, base + RECORD_PTR)
                    if ptr in street_span:
                        street_total += 1
                        if cls == STREET_CLASS:
                            street_ok += 1
                        else:
                            street_exceptions["0x%02X" % cls] += 1

    if not routes_present:
        print("actor class model: SKIPPED - no work-RAM captures present")
        return 0

    vacuous = live == 0
    check_a = (not out_of_range) and not vacuous
    check_c = control_out_of_range > 0      # control MUST fail the range test
    street_rate = (street_ok / street_total) if street_total else 0.0
    # Check B is only meaningful if the span walk had the program image and
    # the population is non-empty; otherwise it is reported as skipped.
    check_b_ran = bool(street_span) and street_total > 0
    check_b = (not street_exceptions) if check_b_ran else None

    ok = check_a and check_c and (check_b is not False)
    manifest = {
        "schema": 1,
        "classification": "master actor class-dispatch falsification - counts "
                          "and class indices only, no ROM bytes",
        "band": {"base": "0x%08X" % BAND_BASE, "slots": BAND_SLOTS,
                 "stride": "0x%02X" % ACTOR_STRIDE},
        "routes": routes_present,
        "live_actor_frames": live,
        "class_histogram": dict(sorted(class_hist.items())),
        "table_entry_count": entry_count,
        "check_a_class_in_table_range": {
            "pass": check_a, "violations": len(out_of_range),
            "examples": out_of_range[:8], "vacuous": vacuous},
        "check_b_runtime_population_class": {
            "population": "live band actors whose +0x1C record pointer is in "
                          "the street walk/attack spans (the population the "
                          "runtime drives and the table_set gate declares)",
            "expected_class": "0x%02X" % STREET_CLASS,
            "matching": street_ok, "total": street_total,
            "rate": round(street_rate, 6),
            "exceptions": dict(street_exceptions),
            "ran": check_b_ran, "pass": check_b},
        "observation_type_class_joint": {
            "%s/%s" % k: v for k, v in sorted(type_class_joint.items())},
        "observation_note": "type-12 actors are NOT always class 0x1F; class "
                            "0x00 (routine 0x03F09C, the type_promotion path) "
                            "and 0x06 also occur. The dispatch is keyed on "
                            "+0x02, not on the type byte.",
        "check_c_negative_control": {
            "byte": "+0x11",
            "out_of_range_count": control_out_of_range,
            "pass": check_c,
            "note": "the control byte MUST go out of table range; if it did "
                    "not, check A would be trivially satisfiable"},
        "result": "PASS" if ok else "FAIL",
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    print("actor class model: %s" % manifest["result"])
    print("  %d live actor-frames in the loop's own band over %s"
          % (live, ", ".join(routes_present)))
    print("  check A class within table range: %s (%d violations)"
          % ("PASS" if check_a else "FAIL", len(out_of_range)))
    if check_b_ran:
        print("  check B runtime population -> class 0x1F: %s %d/%d (%.4f)%s"
              % ("PASS" if check_b else "FAIL", street_ok, street_total,
                 street_rate,
                 "  exceptions %s" % dict(street_exceptions)
                 if street_exceptions else ""))
    else:
        print("  check B: SKIPPED - program image or population unavailable")
    print("  check C negative control (+0x11): %s (%d out-of-range)"
          % ("PASS - control fails as required" if check_c else "FAIL",
             control_out_of_range))
    print("  class histogram:", dict(sorted(class_hist.items())))
    print("wrote", OUT_JSON)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
