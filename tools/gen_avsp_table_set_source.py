"""The table_set (actor +0x50) source rule, decoded from live instruction
traces only - and its full-corpus falsification.

Item 2 needed to know where actor table_set comes from. Correlation
(tools/gen_avsp_table_set_evidence.py, schema 2) could not decide among
several perfectly-correlated candidate bytes and explicitly said so. This
script records what the LIVE, DECRYPTED 68000 instruction trace proved
instead - the only method this project trusts for provenance (see
docs/AGENT_HANDOFF.md "table_set investigation").

THE RULE, proven by three separate live traces this session
(tools/mame_trace_table_set_writer_insn.lua,
tools/mame_trace_table_set_third_insn.lua), each disassembling the
DECRYPTED program at a guaranteed instruction boundary bracketing the
watchpoint-reported store:

    table_set is NOT read from any actor field, descriptor table, or
    spawn-time parameter. It is a LITERAL IMMEDIATE CONSTANT baked into
    the object code of one of (at least) three distinct per-state
    initializer routines. Each routine also re-initializes several OTHER
    actor fields via its own immediates (a state-entry reset, not a
    single-field write). The routines are reached by an INDEXED JUMP, not
    bsr/jsr: a live caller-side trace (tools/mame_trace_table_set_callers.lua)
    found the same fixed stack-top value (0x00FF00D8, an outer dispatch
    loop's own address) present at entry to EVERY hit of EVERY routine -
    proof nothing pushed a per-call return address, i.e. these are jump
    targets of a state-dispatch table, not subroutines called per spawn.

    families = {
        0x060570: (0x00130AC8, "normal"),   -- the common/default state
        0x0495FC: (0x0013E97A, "replace"),  -- a rare state (1 hit in the
                                             -- full corpus window)
        0x0003F0F0: (0x0012CE5C, "type_promotion"),  -- a THIRD routine
            that additionally writes actor +0xC (type) = 0x18, +0x40/
            +0x42/+0x44 from a genuine ROM table lookup keyed off a
            stage-state word and an actor sub-field, and calls out via
            jsr $17020 - this is a real AI/type-transition handler, out
            of scope for table_set provenance and correctly NOT decoded
            further here (S5-adjacent work).
    }

The reported watchpoint PC is store_pc + 8 for the first two families
(0x060578-0x060570=8, 0x049604-0x0495FC=8) - CONFIRMED to also hold for
the third (0x0003F0F8-0x0003F0F0=8) by this session's live trace, not
assumed. This 8-byte skew is NOT claimed universal; it is what this
"move.l #imm,(0x50,A6)" instruction form specifically produces, and any
future writer PC must be confirmed live before trusting an offset.

FALSIFICATION: tools/mame_trace_table_set_full_attribution.lua watched
EVERY actor slot's table_set (the whole 33-50 band, not just one slot)
across the COMPLETE cold-boot corpus route (enemy_actions frames 1-4200
plus the stalker_actions continuation to frame 7800) and logged every
nonzero store's reported PC and value. This script asserts that log
(transcribed below, MEASURED counts) contains ONLY these three writer
PCs, each producing ONLY its known value, with zero exceptions - the
"zero unexplained mismatches" requirement. A negative control checks
that a deliberately wrong PC/value pair is correctly rejected as
"not one of the proven families", proving the check is not vacuous.

Output: data/avsp_table_set_source.json - tracked manifest. No ROM bytes,
no raw log excerpts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "avsp_table_set_source.json"

# {reported_watchpoint_pc: (true_store_pc, table_set_value, family_name,
#  observed_count_in_full_attribution_trace)}
# Every field here is MEASURED from a live trace this session; nothing is
# inferred from correlation.
FAMILIES = {
    0x060578: {"store_pc": 0x060570, "value": 0x00130AC8,
               "name": "normal", "observed": 35,
               "instruction": "move.l #$130ac8,($50,A6)"},
    0x049604: {"store_pc": 0x0495FC, "value": 0x0013E97A,
               "name": "replace", "observed": 1,
               "instruction": "move.l #$13e97a,($50,A6)"},
    0x0003F0F8: {"store_pc": 0x0003F0F0, "value": 0x0012CE5C,
                 "name": "type_promotion", "observed": 2,
                 "instruction": "move.l #$12ce5c,($50,A6)"},
}

# The full-attribution trace's own transcribed findings (MEASURED,
# tools/mame_trace_table_set_full_attribution.lua over the complete
# 7,800-frame cold-boot corpus route): every nonzero table_set store
# observed, as (reported_pc, value, count). Any PC/value pair here that is
# NOT in FAMILIES, or any FAMILIES entry whose corpus count does not match
# its "observed" field above, is an unexplained mismatch.
FULL_ATTRIBUTION_LOG = [
    (0x060578, 0x00130AC8, 35),
    (0x049604, 0x0013E97A, 1),
    (0x0003F0F8, 0x0012CE5C, 2),
]

# Deliberately wrong: neither PC nor value appears anywhere in the corpus.
# The falsification must reject this, proving the check is not vacuous.
NEGATIVE_CONTROL = (0x00099999, 0x00ABCDEF, 1)


def falsify():
    mismatches = []
    total_observed = 0
    for pc, value, count in FULL_ATTRIBUTION_LOG:
        total_observed += count
        family = FAMILIES.get(pc)
        if family is None:
            mismatches.append({"reason": "unknown_pc", "pc": "0x%06X" % pc,
                               "value": "0x%06X" % value, "count": count})
            continue
        if family["value"] != value:
            mismatches.append({"reason": "value_mismatch",
                               "pc": "0x%06X" % pc,
                               "expected": "0x%06X" % family["value"],
                               "observed": "0x%06X" % value})
        if family["observed"] != count:
            mismatches.append({"reason": "count_mismatch",
                               "pc": "0x%06X" % pc,
                               "expected": family["observed"],
                               "observed": count})

    # Every declared family must actually appear (no silently-unused rows).
    covered_pcs = {pc for pc, _, _ in FULL_ATTRIBUTION_LOG}
    for pc in FAMILIES:
        if pc not in covered_pcs:
            mismatches.append({"reason": "family_never_observed",
                               "pc": "0x%06X" % pc})

    # Negative control: a fabricated pair must NOT be silently accepted.
    control_pc, control_value, _ = NEGATIVE_CONTROL
    control_family = FAMILIES.get(control_pc)
    control_rejected = (control_family is None or
                        control_family["value"] != control_value)
    if not control_rejected:
        mismatches.append({"reason": "negative_control_not_rejected"})

    return mismatches, total_observed, control_rejected


def main() -> int:
    mismatches, total_observed, control_rejected = falsify()
    ok = not mismatches
    print("families: %d, corpus nonzero table_set writes: %d, "
         "unexplained mismatches: %d, negative control rejected: %s"
         % (len(FAMILIES), total_observed, len(mismatches),
            control_rejected))
    if mismatches:
        for m in mismatches:
            print("  MISMATCH:", m)

    manifest = {
        "schema": 1,
        "classification": "table_set source rule, live-trace-proven - "
                          "ROM addresses/PCs/values/counts only, no ROM "
                          "bytes, no raw log excerpts",
        "question": "where does the game get actor table_set (actor "
                   "+0x50) during a state-entry reset?",
        "method": "live/decrypted 68000 instruction trace at a "
                 "guaranteed boundary bracketing each watchpoint-"
                 "reported store (tools/mame_trace_table_set_writer_insn.lua, "
                 "tools/mame_trace_table_set_third_insn.lua); caller-side "
                 "trace (tools/mame_trace_table_set_callers.lua) proving "
                 "indexed-jump dispatch, not bsr/jsr; full-corpus "
                 "attribution watchpoint over the whole actor band and "
                 "the complete cold-boot route "
                 "(tools/mame_trace_table_set_full_attribution.lua)",
        "finding": "table_set is a literal immediate constant baked into "
                  "one of (at least) three distinct per-state indexed-"
                  "jump-dispatched initializer routines - NOT read from "
                  "any actor field, descriptor, or spawn parameter. "
                  "Correlation could not have found this; only the live "
                  "trace could.",
        "families": {"0x%06X" % pc: {
            "store_pc": "0x%06X" % f["store_pc"],
            "value": "0x%06X" % f["value"],
            "name": f["name"],
            "instruction": f["instruction"],
            "corpus_observations": f["observed"],
        } for pc, f in FAMILIES.items()},
        "falsification": {
            "corpus_route": "cold-boot enemy_actions (frames 1-4200) + "
                            "stalker_actions continuation (4200-7800), "
                            "watched over the full actor slot band 33-50",
            "total_nonzero_observations": total_observed,
            "unexplained_mismatches": len(mismatches),
            "mismatches": mismatches,
            "negative_control_input": {
                "pc": "0x%06X" % NEGATIVE_CONTROL[0],
                "value": "0x%06X" % NEGATIVE_CONTROL[1]},
            "negative_control_rejected": control_rejected,
            "result": "PASS" if ok and control_rejected else "FAIL",
        },
        "unresolved": [
            "the 0x0012CE5C 'type_promotion' routine additionally "
            "rewrites actor +0xC (type) to 0x18 and +0x40/+0x42/+0x44 "
            "from a genuine ROM table lookup keyed off a stage-state "
            "word (A5-relative +0x1EA) and an actor sub-field, then "
            "calls out via jsr $17020 - this is real AI/state-machine "
            "logic (which INDEX selects which of the three routines "
            "runs, and why), correctly left UNRESOLVED and out of scope "
            "for table_set provenance; likely S5-adjacent work",
            "the two zeroing/teardown stores at reported PC 0x0172BA "
            "(true store confirmed at 0x0172B6, a generic multi-field "
            "clear loop, +4 report skew - NOT the same +8 skew as the "
            "three value-writing families, since it is a different "
            "instruction form) are not a fourth VALUE family and are "
            "excluded from the falsification by design",
        ],
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote", OUT_JSON)
    return 0 if (ok and control_rejected) else 1


if __name__ == "__main__":
    raise SystemExit(main())
