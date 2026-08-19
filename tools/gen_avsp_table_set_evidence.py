"""Record the table_set (actor +0x50) investigation as tracked evidence.

Item 2 (connect decoded collision) needs a table_set value per ROM-driven
actor. diag_table_set_by_type.py found it is NOT a per-TYPE constant for
street aliens (type 12): 3 distinct values, 65.6% dominant - hardcoding
the dominant value would be a guess wearing a MEASURED label, the exact
trap the action-seed table was built to avoid (see
data/avsp_action_seeds.json).

diag_table_set_variance.py then found the real explanation: actor byte
+0x02 predicts table_set with 100% unanimity across 7,794 observations
and has exactly 3 distinct values, matching table_set's own cardinality
exactly. Per-slot tracking additionally shows table_set is FIXED for a
given spawn's whole observed lifetime (only 1 of 13 tracked slot-
instances ever showed two values, consistent with a despawn/respawn of a
different variant into the same physical slot, not a live per-frame
change) - so this is a spawn-time selector, not something that needs
re-reading every frame.

This resolves *why* table_set varies, but does NOT yet make it wireable:
+0x02 is not a field this runtime currently tracks for its ROM-driven
actors (CapActor.variant is a model-invented spawn-table field with no
proven correspondence to the ROM's own byte +0x02 - using it directly
would be exactly the guess this investigation exists to avoid). Closing
the gap needs either (a) reading +0x02 from a live actor record the
runtime doesn't yet carry, or (b) proving CapActor.variant's spawn-order
correlates with +0x02's real values for the captured route specifically.
Neither is done here.

Outputs data/avsp_table_set_evidence.json - a tracked manifest recording
the finding (byte offsets, values, evidence counts). No ROM bytes.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "avsp_table_set_evidence.json"
ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")
WORKRAM_BASE = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_ANCHOR = 0xFF8380
ACTOR_STRIDE = 0xC0
TARGET_TYPE = 12
PREDICTOR_OFFSETS = (0x02, 0x0E)  # both reached 100% unanimity


def u32(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def main() -> int:
    by_type = defaultdict(Counter)
    per_slot_values = defaultdict(set)
    predictors = {off: defaultdict(Counter) for off in PREDICTOR_OFFSETS}

    for route in ROUTES:
        root = ROOT / ".deps" / "mame" / route
        if not root.is_dir():
            continue
        for path in sorted(root.glob("workram_*.bin"))[::3]:
            work = path.read_bytes()
            if len(work) != WORKRAM_SIZE:
                continue
            n = 0
            while True:
                off = (ACTOR_ANCHOR - WORKRAM_BASE) + n * ACTOR_STRIDE
                if off + ACTOR_STRIDE > len(work):
                    break
                rec = work[off:off + ACTOR_STRIDE]
                slot = n
                n += 1
                if rec[0x00] != 1:
                    continue
                actor_type = rec[0x08]
                table_set = u32(rec, 0x50)
                by_type[actor_type][table_set] += 1
                if actor_type == TARGET_TYPE:
                    per_slot_values[(route, slot)].add(table_set)
                    for poff in PREDICTOR_OFFSETS:
                        predictors[poff][rec[poff]][table_set] += 1

    type_summary = []
    for actor_type in sorted(by_type):
        counter = by_type[actor_type]
        total = sum(counter.values())
        top, hits = counter.most_common(1)[0]
        type_summary.append({
            "type": actor_type, "observations": total,
            "distinct_table_set": len(counter),
            "dominant_table_set": "0x%06X" % top,
            "dominant_share": round(hits / total, 4),
        })

    changing = [k for k, v in per_slot_values.items() if len(v) > 1]

    predictor_summary = []
    for poff in PREDICTOR_OFFSETS:
        buckets = predictors[poff]
        total = agreed = 0
        for byte_value, counter in buckets.items():
            n = sum(counter.values())
            total += n
            agreed += counter.most_common(1)[0][1]
        predictor_summary.append({
            "byte_offset": "0x%02X" % poff,
            "distinct_byte_values": len(buckets),
            "unanimity": round(agreed / total, 4) if total else None,
            "observations": total,
        })

    manifest = {
        "schema": 1,
        "classification": "table_set investigation evidence - actor field "
                          "offsets and observation counts, no ROM bytes",
        "question": "is actor +0x50 (table_set) usable for collision "
                   "wiring without inventing a value?",
        "finding": "NOT a per-TYPE constant (type 12 street aliens: 3 "
                  "distinct values, 65.6% dominant - hardcoding the "
                  "dominant value would be a guess). IS fully explained "
                  "by actor byte +0x02 (100% unanimity, matches "
                  "table_set's own cardinality exactly) and closely by "
                  "+0x0E (also 100% unanimity, already independently "
                  "identified as the palette byte in milestone-1). Fixed "
                  "per spawn-instance lifetime, not a live per-frame "
                  "value (12 of 13 tracked slot-instances never changed).",
        "still_blocking": "the runtime does not currently track actor "
                         "byte +0x02 for its ROM-driven actors, and "
                         "CapActor.variant (the model's spawn-table "
                         "field) has no proven correspondence to it - "
                         "using it directly would reintroduce the exact "
                         "guess this investigation avoided for the "
                         "action-seed table.",
        "type_summary": type_summary,
        "target_type": TARGET_TYPE,
        "slot_instances_tracked": len(per_slot_values),
        "slot_instances_with_multiple_values": len(changing),
        "predictors": predictor_summary,
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote", OUT_JSON)
    print(json.dumps(manifest["finding"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
