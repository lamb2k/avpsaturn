"""Mine the game's own action -> animation-record seeding table.

S2 Body D bridged pose seeding with TWO hardcoded script addresses (walk
0x12EB4C, attack 0x12D8A0) chosen by the capability model's action enum.
That is the last hand-authored input on the ROM animation path and it
covers one actor type and two actions. This tool replaces it with a table
the game itself demonstrates.

Method (the standing corpus method, offline):

  * every paired work-RAM capture frame of every route is read;
  * for each live actor slot, the pair (type at +0x08, action word at
    +0x06) is keyed to the live animation-record pointer at +0x1C;
  * a record pointer counts only on a TRUE EXTERNAL RE-POINT: the
    actor's action word changed on that frame AND the new pointer is
    neither the previous frame's pointer nor its own script successor
    (+16, or the jump target when flags bit 15 is set - the interpreter
    rule, read from the ROM). Without the re-point condition the table
    is poisoned: an action word returning to 0x0000 ("no new action")
    leaves the pointer walking mid-script, which first-pass mining
    recorded as 65 distinct "seeds" for one key at 7% agreement;
  * the winning seed per (type, action) is the most frequently observed
    one, and its share of that key's observations is recorded so a
    caller can see how clean the evidence is.

Outputs:

  * generated/avsp_action_seeds.h - the C table (git-ignored: the record
    addresses are program-image offsets)
  * data/avsp_action_seeds.json  - tracked manifest: counts, per-key
    observation totals and agreement shares, route breakdown. Addresses
    ARE included: they are ROM offsets, not ROM bytes, and the existing
    avsp_anim_records.json already publishes the same class of value.

Every seed is MEASURED: it is a pointer the game wrote itself on the
frame it changed that actor's action.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")
WORKRAM_BASE = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_ANCHOR = 0xFF8380
ACTOR_STRIDE = 0xC0
PROGRAM_FIRST = 0x100000
PROGRAM_LAST = 0x200000
OUT_H = ROOT / "generated" / "avsp_action_seeds.h"
OUT_JSON = ROOT / "data" / "avsp_action_seeds.json"


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def u32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o + 4], "big")


ROM_PATH = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
ROM_BASE = 0x000000
_ROM = None


def rom() -> bytes:
    global _ROM
    if _ROM is None:
        _ROM = ROM_PATH.read_bytes()
    return _ROM


def script_successor(pointer: int) -> int:
    """The interpreter's next record address (avsp_anim_next_address)."""
    data = rom()
    off = pointer - ROM_BASE
    if off < 0 or off + 20 > len(data):
        return -1
    flags = u16(data, off + 2)
    if flags & 0x8000:
        return u32(data, off + 16)
    return pointer + 16


def slot_offsets(work: bytes):
    n = 0
    while True:
        off = (ACTOR_ANCHOR - WORKRAM_BASE) + n * ACTOR_STRIDE
        if off + ACTOR_STRIDE > len(work):
            return
        yield n, off
        n += 1


def mine(route_root: Path, seeds, totals, routes_seen, route_name):
    """Walk one route's frames in order, keyed on true external re-points."""
    previous = {}
    frames = sorted(route_root.glob("workram_*.bin"))
    for path in frames:
        work = path.read_bytes()
        if len(work) != WORKRAM_SIZE:
            continue
        for slot, off in slot_offsets(work):
            rec = work[off:off + ACTOR_STRIDE]
            if rec[0x00] != 1:            # not live
                previous.pop(slot, None)
                continue
            actor_type = rec[0x08]
            action = u16(rec, 0x06)
            record = u32(rec, 0x1C)
            if not (PROGRAM_FIRST <= record < PROGRAM_LAST):
                continue
            prev = previous.get(slot)
            previous[slot] = (actor_type, action, record)
            if prev is None:
                continue
            prev_type, prev_action, prev_record = prev
            if (prev_type, prev_action) == (actor_type, action):
                continue                    # no action change
            # True external re-point only: the game wrote a fresh record,
            # not the script's own hold/advance/jump continuation.
            if record == prev_record:
                continue
            if record == script_successor(prev_record):
                continue
            key = (actor_type, action)
            seeds[key][record] += 1
            totals[key] += 1
            routes_seen[key].add(route_name)
    return len(frames)


def main() -> int:
    seeds = defaultdict(Counter)
    totals = Counter()
    routes_seen = defaultdict(set)
    per_route = {}
    for route in ROUTES:
        root = ROOT / ".deps" / "mame" / route
        if not root.is_dir():
            print("skip missing route:", route)
            continue
        n = mine(root, seeds, totals, routes_seen, route)
        per_route[route] = {"frames": n}
        print("%s: %d frames, %d distinct (type,action) keys so far"
              % (route, n, len(seeds)))

    if not seeds:
        print("no captures found - nothing to generate")
        return 1

    rows = []
    for (actor_type, action), counter in sorted(seeds.items()):
        record, hits = counter.most_common(1)[0]
        total = totals[(actor_type, action)]
        rows.append({
            "type": actor_type,
            "action": action,
            "record": record,
            "observations": total,
            "agreement": round(hits / total, 4),
            "distinct_records": len(counter),
            "routes": sorted(routes_seen[(actor_type, action)]),
        })

    clean = [r for r in rows if r["agreement"] == 1.0]
    print("keys: %d, unanimous: %d, total observations: %d"
          % (len(rows), len(clean), sum(r["observations"] for r in rows)))

    # Only ship rows the evidence does not contradict: agreement 1.0 means
    # every observed re-point for that key landed on the same record. A
    # split key (e.g. type 12 / action 0x1600 at 47%) means the game picks
    # among VARIANTS the actor record does not yet expose to this table -
    # shipping the majority winner there would be a guess wearing a
    # MEASURED label, so those rows are omitted, not guessed.
    shipped = [r for r in rows if r["agreement"] == 1.0]
    print("shipping %d unanimous rows of %d mined (%d withheld as split)"
         % (len(shipped), len(rows), len(rows) - len(shipped)))

    OUT_H.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "/* Generated by tools/gen_avsp_action_seeds.py. Do not edit, do not\n"
        " * commit: these are addresses inside the private program image.\n"
        " * Each row is a record pointer the GAME wrote on every observed\n"
        " * true external re-point for that (actor_type, action) key - \n"
        " * MEASURED, never hand-chosen. Only unanimous keys ship; split\n"
        " * keys (the game choosing among variants this table can't see)\n"
        " * are withheld rather than guessed - see data/avsp_action_seeds.json\n"
        " * for the full mined set including withheld rows. */\n"
        "#ifndef AVSP_ACTION_SEEDS_H\n#define AVSP_ACTION_SEEDS_H\n\n"
        "typedef struct {\n"
        "    unsigned char actor_type;\n"
        "    unsigned short action;\n"
        "    unsigned long record;\n"
        "} AvspActionSeed;\n\n"
        "static const AvspActionSeed avsp_action_seeds[%d] = {\n" % len(shipped)
    ]
    for r in shipped:
        lines.append("    { %d, 0x%04X, 0x%06XUL },\n"
                     % (r["type"], r["action"], r["record"]))
    lines.append("};\n\n#define AVSP_ACTION_SEED_COUNT %d\n\n#endif\n"
                 % len(shipped))
    OUT_H.write_text("".join(lines))

    manifest = {
        "schema": 1,
        "classification": "action->record seed manifest - ROM offsets, no ROM bytes",
        "method": "seed recorded only on a true external re-point: the "
                  "actor's action word changed AND the new record pointer "
                  "is neither the previous pointer nor its own script "
                  "successor. Only agreement==1.0 keys are compiled into "
                  "avsp_action_seeds.h; split keys are listed here for "
                  "visibility but withheld from the shipped table.",
        "keys": len(rows),
        "shipped_keys": len(shipped),
        "unanimous_keys": len(clean),
        "observations": sum(r["observations"] for r in rows),
        "routes": per_route,
        "seeds": [{"type": r["type"],
                   "action": "0x%04X" % r["action"],
                   "record": "0x%06X" % r["record"],
                   "observations": r["observations"],
                   "agreement": r["agreement"],
                   "distinct_records": r["distinct_records"],
                   "routes": r["routes"]} for r in rows],
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote %s and %s" % (OUT_H, OUT_JSON))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
