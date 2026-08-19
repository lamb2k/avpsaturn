"""Enumerate every per-actor sub-state dispatcher in the decrypted program.

THE MECHANISM (decoded offline 2026-08-19 from the validated opcode-space
dump, corroborated by the live table_set traces and the stride-1 corpus):
each actor action routine begins with this exact 68000 idiom -

    102e 0004   move.b ($4,A6), D0     ; index = actor byte +0x04
    323b 0006   move.w ($6,PC,D0.w), D1
    4efb 1002   jmp    ($2,PC,D1.w)

The PC-relative word table starts at dispatcher_pc + 12; entry i's handler
is table_base + table[i]. The table is self-describing: table[0] is the
displacement to the sub-state-0 handler, which sits immediately after the
table, so table[0]/2 is the number of sub-states. Sub-state-0 handlers are
the per-state initializers (they start with `addq.b #2,($4,A6)` so they run
once per state entry - the mechanism behind the three live-proven table_set
stores at 0x060570/0x0495FC/0x0003F0F0, whose dispatchers are 0x060532/
0x0495CC/0x0003F0C4).

The opcode-space dump (decrypted_opcodes_2m.bin) is valid at code addresses
- all three live-confirmed store instructions appear byte-exact in it. The
DATA-space dump (decrypted_program_2m.bin) is NOT; do not scan that one for
code. Offline scan LOCATES and STRUCTURES; per the provenance rule, any
value that enters the runtime still needs live confirmation or corpus
falsification (tools/verify_avsp_substate_model.py is the corpus half).

Output: data/avsp_substate_dispatchers.json - addresses, counts and targets
only; no ROM bytes.

Contract for test.ps1: skips cleanly (exit 0) when the private opcode dump
is absent; when present, the self-test (three known sites decode to the
live-confirmed initializer entries; a fabricated site is rejected) must
pass or the exit is nonzero.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
OUT_JSON = ROOT / "data" / "avsp_substate_dispatchers.json"

IDIOM = bytes.fromhex("102e0004" "323b0006" "4efb1002")

# Live-proven anchors: dispatcher pc -> (state0 handler, table_set family).
# The three initializer entries were confirmed by instruction trace
# (data/avsp_table_set_source.json); the dispatcher decode must land state 0
# exactly on them.
KNOWN = {
    0x060532: {"state0": 0x060546, "family": "normal (0x130AC8)"},
    0x0495CC: {"state0": 0x0495E0, "family": "replace (0x13E97A)"},
    0x03F0C4: {"state0": 0x03F0D8, "family": "type_promotion (0x12CE5C)"},
}

MAX_STATES = 0x40          # sanity bound; the known tables have 4


def u16(data: bytes, off: int) -> int:
    return (data[off] << 8) | data[off + 1]


def decode_site(data: bytes, pc: int) -> dict | None:
    """Decode one idiom hit into its sub-state table, or None if the site
    fails structural sanity (a data byte-pattern collision, not a
    dispatcher)."""
    base = pc + 12
    if base + 2 > len(data):
        return None
    first = u16(data, base)
    if first == 0 or first % 2 or first // 2 > MAX_STATES:
        return None
    count = first // 2
    if base + 2 * count > len(data):
        return None
    targets = []
    for i in range(count):
        disp = u16(data, base + 2 * i)
        # 68000 index displacement is signed 16-bit; a dispatcher's handlers
        # follow its table, so entries are positive and beyond the table.
        if disp >= 0x8000:
            return None
        target = base + disp
        if disp < first or target + 2 > len(data):
            return None
        targets.append(target)
    return {
        "pc": "0x%06X" % pc,
        "table_base": "0x%06X" % base,
        "sub_states": count,
        "targets": ["0x%06X" % t for t in targets],
    }


def scan(data: bytes) -> tuple[list[dict], int]:
    sites = []
    rejected = 0
    off = 0
    while True:
        off = data.find(IDIOM, off)
        if off < 0:
            break
        if off % 2 == 0:               # 68000 instructions are word-aligned
            site = decode_site(data, off)
            if site is None:
                rejected += 1
            else:
                sites.append(site)
        off += 2
    return sites, rejected


def self_test(sites: list[dict]) -> list[str]:
    failures = []
    by_pc = {int(s["pc"], 16): s for s in sites}
    for pc, expect in KNOWN.items():
        site = by_pc.get(pc)
        if site is None:
            failures.append("known dispatcher 0x%06X not found" % pc)
            continue
        state0 = int(site["targets"][0], 16)
        if state0 != expect["state0"]:
            failures.append(
                "0x%06X state-0 target 0x%06X != live-confirmed 0x%06X (%s)"
                % (pc, state0, expect["state0"], expect["family"]))
    # Negative control: a fabricated pc must not appear, and a real site's
    # decode must break if the table pointer is deliberately shifted.
    if 0x000100 in by_pc:
        failures.append("negative control: fabricated pc accepted")
    return failures


def main() -> int:
    if not OPCODES.is_file():
        print("dispatchers: SKIPPED - opcode dump absent (%s); committed "
              "manifest records the run with inputs present"
              % OPCODES.relative_to(ROOT).as_posix())
        return 0

    data = OPCODES.read_bytes()
    sites, rejected = scan(data)
    failures = self_test(sites)

    # Control: shifting a known site's decode by 2 must NOT reproduce the
    # live-confirmed state-0 entry (proves the table math is load-bearing).
    control = decode_site(data, 0x060532 + 2)
    control_broken = (control is None or
                      int(control["targets"][0], 16) != KNOWN[0x060532]["state0"])
    if not control_broken:
        failures.append("perturbation control not broken")

    manifest = {
        "schema": 1,
        "classification": "sub-state dispatcher enumeration - code "
                          "addresses/counts/targets only, no ROM bytes",
        "mechanism": "move.b ($4,A6),D0; move.w ($6,PC,D0.w),D1; "
                     "jmp ($2,PC,D1.w) - actor byte +0x04 indexes a "
                     "PC-relative word table at dispatcher_pc+12; table[0]/2 "
                     "is the sub-state count; sub-state-0 handlers are the "
                     "per-state initializers (they addq.b #2 the index)",
        "source_image": {
            "path": OPCODES.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "note": "OPCODE-space decrypted dump - valid at code addresses "
                    "(all three live-confirmed table_set stores byte-exact); "
                    "the DATA-space dump is not valid for code",
        },
        "site_count": len(sites),
        "pattern_hits_rejected_by_sanity": rejected,
        "known_anchors": {
            "0x%06X" % pc: {"state0": "0x%06X" % v["state0"],
                            "family": v["family"]}
            for pc, v in KNOWN.items()},
        "self_test_failures": failures,
        "perturbation_control_broken": control_broken,
        "result": "PASS" if not failures else "FAIL",
        "sites": sites,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    counts: dict[int, int] = {}
    for s in sites:
        counts[s["sub_states"]] = counts.get(s["sub_states"], 0) + 1
    print("dispatchers: %s - %d sites (%d pattern hits rejected), "
          "sub-state histogram %s"
          % (manifest["result"], len(sites), rejected,
             {k: counts[k] for k in sorted(counts)}))
    for f in failures:
        print("  FAILURE:", f)
    print("wrote", OUT_JSON)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
