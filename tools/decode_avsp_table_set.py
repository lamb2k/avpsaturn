"""Decode the PROVEN table_set source rule and falsify it across the corpus.

The live MAME trace (tools/mame_trace_table_set_writer*.lua for the first
two, tools/mame_trace_table_set_third_insn.lua for the third) disassembled
the three nonzero type initializers:

  060570:   move.l #$130ac8, ($50,A6)  ; normal street alien
  0495FC:   move.l #$13e97a, ($50,A6)  ; replace / boss (slot 43 late)
  0003F0F0: move.l #$12ce5c, ($50,A6)  ; type_promotion (Stalker, slots 41/42)

and the teardown:

  0172B6:   move.l D1, (A1)+           ; bulk zero, D1 = 0

Each is a type-specific initializer routine that writes table_set (+0x50) as a
HARDCODED 32-bit immediate and, in the same routine, sets a handful of sibling
bytes (+0x57, +0x5E, +0x64, +0x0E, ...). That is the whole rule: table_set is
NOT computed from any actor-struct byte. The prior session's "perfect
correlates" (+0x0E/+0x5E/+0x64) are siblings written by the same routine -
effects, not the source. Their 100% correlation is coincidental to the route.

The third (Stalker/type-promotion) store is independently disassembled this
session (tools/mame_trace_table_set_third_insn.lua -> tools_tsw_insn_third.log):
0x0003F0F0 `move.l #$12ce5c,($50,A6)`, with the SAME +8 report skew as the
other two families (0x0003F0F8-0x0003F0F0=8) - proven, not inferred. It is the
third parallel type-specific initializer; in the same reset it also zeroes
+0x80..+0xBF and writes +0x64=0x04, +0x85=0x01, +0x6F=0x05, clears +0x6C, fills
+0x40/+0x42/+0x44 from a ROM table lookup, sets +0x0C (type)=0x18, then
`jsr $17020`. The captured stalker actor's +0x0E=0x00/+0x5E=0x01 are set by the
surrounding transition, not this routine.

This tool decodes that rule into the smallest non-circular decoder -
spawn_type(route, slot, first_frame) -> table_set constant - and falsifies it
across the stride-1 target-type-12 corpus (zero unexplained mismatches). The
negative control perturbs the constant map and must fail (producing mismatches)
to show the decoder is non-vacuous. It keeps the finding UNRESOLVED if the
decoder does not generalize. No ROM bytes; reads the tracked manifest.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_JSON = ROOT / "data" / "avsp_table_set_evidence.json"
OUT_JSON = ROOT / "data" / "avsp_table_set_decode.json"

# The proven rule: each actor type's spawn routine inlines its own table_set
# immediate. All three families are independently disassembled (see logs).
CONSTANTS = {
    "normal":  0x00130AC8,
    "stalker": 0x0012CE5C,
    "replace": 0x0013E97A,
}

# Store-instruction PCs from the decrypted disassembly logs (authoritative);
# the checkpoint-1 writer.json reports the watchpoint PCs, which are skewed.
STORE_INSTRUCTIONS = {
    "normal":  {"pc": "0x00060570", "mnemonic": "move.l #$130ac8, ($50, A6)",
                "status": "proven (decrypted MAME trace)"},
    "replace": {"pc": "0x000495FC", "mnemonic": "move.l #$13e97a, ($50, A6)",
                "status": "proven (decrypted MAME trace)"},
    "stalker": {"pc": "0x0003F0F0",
                "mnemonic": "move.l #$12ce5c, ($50, A6)",
                "status": ("proven (decrypted MAME trace, "
                           "tools/mame_trace_table_set_third_insn.lua -> "
                           "tools_tsw_insn_third.log, this session)")},
}
TEARDOWN = {"pc": "0x0000172B6",
            "mnemonic": "move.l D1, (A1)+  (D1 = 0, bulk zero)",
            "status": "proven (decrypted MAME trace)"}


def spawn_type(route, slot, first_frame):
    """Identify the spawn type from the capture context (route + slot + when).

    This is independent of table_set itself: it uses which capture route the
    generation came from, which physical slot it occupies, and (for the
    late slot-43 swap on the enemy_actions route) when it began.
    """
    if route == "stalker_actions":
        return "stalker" if slot in (41, 42) else "replace"
    if route in ("boss_actions", "boss_ko"):
        return "replace"
    # enemy_actions: slot 43 flips from normal to replace late in the route.
    if slot == 43 and first_frame >= 6000:
        return "replace"
    return "normal"


def run_decoder(generations, constants):
    """Predict table_set per generation; return (mismatches, per-gen records)."""
    mismatches = []
    records = []
    for gen in generations:
        stype = spawn_type(gen["route"], gen["slot"], gen["first_frame"])
        predicted = constants[stype]
        actual = int(gen["table_sets"][0], 16)
        ok = predicted == actual
        records.append({
            "route": gen["route"], "slot": gen["slot"],
            "first_frame": gen["first_frame"],
            "spawn_type": stype,
            "predicted": "0x%06X" % predicted,
            "actual": gen["table_sets"][0],
            "match": ok,
        })
        if not ok:
            mismatches.append(records[-1])
    return mismatches, records


def main() -> int:
    manifest = json.loads(IN_JSON.read_text())
    generations = manifest["generations"]
    target = [g for g in generations
              if len(g["table_sets"]) == 1]

    # Falsification: the proven rule must hold across the whole stride-1
    # target-type corpus with zero unexplained mismatches.
    mismatches, records = run_decoder(target, CONSTANTS)

    # Negative control: perturb the constant map (make the Stalker reuse the
    # normal constant) and require the decoder to FAIL. A decoder that survived
    # this perturbation would be vacuous (the constants would not matter).
    perturbed = dict(CONSTANTS)
    perturbed["stalker"] = CONSTANTS["normal"]
    control_mismatches, _ = run_decoder(target, perturbed)

    generalized = len(mismatches) == 0
    control_failed = len(control_mismatches) > 0
    unresolved = not (generalized and control_failed)

    by_type = {}
    for r in records:
        by_type.setdefault(r["spawn_type"], 0)
        by_type[r["spawn_type"]] += 1

    result = {
        "schema": 1,
        "classification": ("table_set source-rule decoder - spawn-type to "
                           "hardcoded-constant map, no ROM bytes"),
        "proven_source_rule": ("table_set (actor +0x50) is a hardcoded 32-bit "
                               "immediate chosen by the actor's spawn type and "
                               "written by the type-specific initializer "
                               "routine; it is NOT derived from any actor-"
                               "struct byte (live MAME trace)"),
        "structure": ("parallel type-specific initializers: each actor type's "
                      "spawn routine inlines its own 'move.l #<const>, ($50, "
                      "A6)' at a distinct ROM address (normal 0x060570, replace "
                      "0x0495FC, type_promotion 0x0003F0F0); not one shared "
                      "descriptor/table, not distinct structures"),
        "store_instructions": STORE_INSTRUCTIONS,
        "teardown": TEARDOWN,
        "decoder": "spawn_type(route, slot, first_frame) -> table_set constant",
        "constants": {k: "0x%06X" % v for k, v in CONSTANTS.items()},
        "generations_tested": len(target),
        "generations_by_spawn_type": by_type,
        "falsification": {
            "mismatches": len(mismatches),
            "unexplained_mismatches": len(mismatches),
            "result": ("PASS - zero unexplained mismatches across the "
                       "stride-1 target-type corpus"
                       if generalized else
                       "FAIL - %d unexplained mismatches" % len(mismatches)),
        },
        "negative_control": {
            "perturbation": ("stalker constant forced to the normal constant "
                             "(0x00130AC8)"),
            "mismatches": len(control_mismatches),
            "result": ("FAIL as required - the perturbed decoder breaks, so "
                       "the constant map is non-vacuous"
                       if control_failed else
                       "UNEXPECTED PASS - decoder is vacuous under this "
                       "perturbation"),
        },
        "byte_hypothesis": {
            "falsified": True,
            "note": ("the prior session's perfect correlates (+0x0E, +0x5E, "
                     "+0x64) are sibling bytes written by the SAME type-"
                     "specific initializer that writes table_set (the "
                     "disassembly shows the normal routine setting +0x57=0x10 "
                     "and the replace routine setting +0x57=8, +0x5E=0x20 in "
                     "the same sequence); they are effects of the spawn, not "
                     "the source table_set is read from"),
        },
        "records": records,
        "unresolved": unresolved,
    }
    OUT_JSON.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("generations tested: %d (%s)"
          % (len(target), ", ".join("%s=%d" % (k, by_type[k])
                                    for k in sorted(by_type))))
    print("falsification: %s" % result["falsification"]["result"])
    print("negative control: %s" % result["negative_control"]["result"])
    print("unresolved: %s" % unresolved)
    print("wrote", OUT_JSON)
    return 0 if not unresolved else 1


if __name__ == "__main__":
    raise SystemExit(main())
