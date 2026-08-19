"""Record the table_set (actor +0x50) correlation evidence, honestly.

Item 2 (connect decoded collision) needs a table_set value per ROM-driven
actor. This instrument answers a narrow question: WHICH actor fields are
perfectly correlated with table_set in the captured corpus? It does NOT
answer which field the game actually reads - that requires the writer
trace (a live MAME watchpoint on the spawn initializer), and no field may
enter the runtime on correlation alone. An earlier revision of this file
promoted one candidate (+0x02) to "the explanation"; that was wrong - six
bytes tie at 100% agreement in this corpus and correlation cannot pick
between them.

Method:

  * every captured frame of every route is scanned (stride 1 - the
    earlier stride-3 revision is the same class of shortcut that lost 18
    tiles from the tile archive);
  * each physical actor slot is segmented into GENERATIONS: a generation
    begins on inactive->active, ends on active->inactive, and a new one
    begins if the type byte changes without an observed inactive frame
    (a same-slot respawn the sampling missed);
  * candidate bytes are evaluated per-generation against that
    generation's table_set; a candidate is "perfect" only when every
    generation with a given candidate value has the same table_set AND
    the mapping is consistent across all routes;
  * a NEGATIVE CONTROL runs the same test on a perturbed copy of each
    candidate (value XOR slot index) - a passing control would mean the
    test is vacuous (e.g. one generation per key), not that the field is
    predictive.

Outputs data/avsp_table_set_evidence.json - tracked manifest with every
generation record (route, slot, generation index, first/last frame,
candidate values, table_set) and every perfect candidate's explicit
value->table_set mapping. No ROM bytes.
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
# Every byte offset except the answer itself (+0x50..+0x53) and the
# generation-identity fields used for segmentation.
CANDIDATE_OFFSETS = [o for o in range(ACTOR_STRIDE)
                     if o not in (0x00, 0x50, 0x51, 0x52, 0x53)]


def u32(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def collect_generations():
    """Segment every slot of every route into actor generations."""
    generations = []
    for route in ROUTES:
        root = ROOT / ".deps" / "mame" / route
        if not root.is_dir():
            continue
        open_gens = {}       # slot -> generation dict being built
        frames = sorted(root.glob("workram_*.bin"))
        for path in frames:
            try:
                frame_no = int(path.stem.split("_")[-1])
            except ValueError:
                frame_no = -1
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
                active = rec[0x00] == 1
                gen = open_gens.get(slot)
                if not active:
                    if gen is not None:
                        generations.append(gen)
                        del open_gens[slot]
                    continue
                actor_type = rec[0x08]
                table_set = u32(rec, 0x50)
                if gen is not None and gen["type"] != actor_type:
                    # identity changed with no observed inactive frame:
                    # close the generation and start a new one
                    generations.append(gen)
                    gen = None
                if gen is None:
                    gen = {
                        "route": route, "slot": slot,
                        "type": actor_type,
                        "first_frame": frame_no, "last_frame": frame_no,
                        "table_sets": set(),
                        "candidates": {o: set() for o in CANDIDATE_OFFSETS},
                    }
                    open_gens[slot] = gen
                gen["last_frame"] = frame_no
                gen["table_sets"].add(table_set)
                for o in CANDIDATE_OFFSETS:
                    gen["candidates"][o].add(rec[o])
        generations.extend(open_gens.values())
    return generations


def evaluate(generations, value_of):
    """Perfect-mapping test: candidate value -> table_set, per offset.

    value_of(gen, offset) supplies the candidate value for a generation
    (or None to skip it); swapping this in is how the negative control
    perturbs the data without duplicating the test itself.
    """
    perfect = {}
    for o in CANDIDATE_OFFSETS:
        mapping = defaultdict(set)
        usable = 0
        for gen in generations:
            if gen["type"] != TARGET_TYPE:
                continue
            if len(gen["table_sets"]) != 1:
                continue          # ambiguous generation; never evidence
            value = value_of(gen, o)
            if value is None:
                continue
            mapping[value].add(next(iter(gen["table_sets"])))
            usable += 1
        if not mapping or usable == 0:
            continue
        if all(len(targets) == 1 for targets in mapping.values()):
            perfect[o] = {
                "mapping": {str(v): "0x%06X" % next(iter(t))
                            for v, t in sorted(mapping.items())},
                "distinct_values": len(mapping),
                "generations_used": usable,
            }
    return perfect


def stable_value(gen, offset):
    values = gen["candidates"][offset]
    if len(values) != 1:
        return None               # varies within the generation: not a
    return next(iter(values))     # spawn-time identity field


def perturbed_value(gen, offset):
    value = stable_value(gen, offset)
    if value is None:
        return None
    return value ^ (gen["slot"] & 0xFF)


def main() -> int:
    generations = collect_generations()
    target_gens = [g for g in generations if g["type"] == TARGET_TYPE]
    unambiguous = [g for g in target_gens if len(g["table_sets"]) == 1]
    print("generations: %d total, %d of type %d, %d with a single "
          "table_set" % (len(generations), len(target_gens), TARGET_TYPE,
                        len(unambiguous)))

    perfect = evaluate(generations, stable_value)
    control = evaluate(generations, perturbed_value)
    # The control perturbs each value by the slot index; offsets whose
    # mapping SURVIVES that perturbation are being carried by something
    # other than the value itself (e.g. degenerate group sizes), so the
    # test cannot distinguish them - flag those.
    vacuous = sorted(set(perfect) & set(control))
    informative = sorted(set(perfect) - set(control))
    print("perfect candidates: %d, of which %d survive the negative "
          "control's perturbation (test vacuous for those): %s"
          % (len(perfect), len(vacuous),
             ", ".join("0x%02X" % o for o in vacuous) or "none"))
    print("informative perfect candidates: %s"
          % (", ".join("0x%02X" % o for o in informative) or "none"))

    generation_records = []
    for gen in target_gens:
        generation_records.append({
            "route": gen["route"], "slot": gen["slot"],
            "first_frame": gen["first_frame"],
            "last_frame": gen["last_frame"],
            "table_sets": sorted("0x%06X" % t for t in gen["table_sets"]),
            "candidates": {"0x%02X" % o: sorted(gen["candidates"][o])
                           for o in informative},
        })

    manifest = {
        "schema": 2,
        "classification": "table_set correlation evidence - actor field "
                          "offsets and observation counts, no ROM bytes",
        "question": "which actor fields are PERFECTLY CORRELATED with "
                   "table_set in this corpus? (correlation only - the "
                   "field the game actually reads requires the writer "
                   "trace, and nothing may be wired on this evidence "
                   "alone)",
        "method": "stride-1 over every captured frame; per-slot "
                 "generation segmentation (inactive->active begins, "
                 "active->inactive ends, type change without an "
                 "observed inactive frame splits); perfect-mapping test "
                 "per candidate byte over unambiguous generations; "
                 "negative control perturbs each candidate by slot "
                 "index - candidates surviving the control are flagged "
                 "vacuous, not predictive",
        "finding": "multiple candidate bytes are perfectly correlated "
                  "with table_set in this corpus; correlation cannot "
                  "choose between them. The game's real source must "
                  "come from a live writer trace on the spawn "
                  "initializer (watch writes to +0x50 and the candidate "
                  "bytes on one street-alien slot over the cold-boot "
                  "route, log PC and source reads).",
        "target_type": TARGET_TYPE,
        "generations_total": len(generations),
        "generations_target_type": len(target_gens),
        "generations_unambiguous": len(unambiguous),
        "perfect_candidates": {"0x%02X" % o: perfect[o]
                               for o in sorted(perfect)},
        "vacuous_under_negative_control": ["0x%02X" % o for o in vacuous],
        "informative_candidates": ["0x%02X" % o for o in informative],
        "generations": generation_records,
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
