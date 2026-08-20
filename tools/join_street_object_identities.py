#!/usr/bin/env python3
"""Chapter 1: join street objects to semantic actor identities.

An earlier version of this tool joined objects to actors by nearest
raw X. That heuristic is FALSIFIED and is not used here: sweeping every
grid and window, a shuffled-frame control never fell more than about
fifteen points below the true rate (96x64 window: 98.0% true against
87.8% control), because object parts scatter far from their anchor and
entities overlap. Proximity carries almost no identity information.

The rule used instead is EXACT RE-EMISSION. Each live actor record's
object words are decoded from ROM through the repo's emitter model, and
the record joins the object list at the unique 8-byte-aligned offset
where that word run appears VERBATIM in the next frame's active bank.
The run is the entity's own emission, so a match is an identity, not a
resemblance.

Two measured facts make this exact:

- the capture's `workram` region is based at 0xFF0000, not 0xFF8000
  (tools/mame_capture_full_route.lua reads 0xff0000..0xffffff), so the
  0xFF8000-based view every emitter tool expects is workram[0x8000:];
- objects at frame N+1 come from the actor state at frame N, and each
  entity's objects occupy one contiguous run of object-RAM slots.

Actor records sit on a 0x40 allocation grid from 0xFF8380, not the 0xC0
record stride: observed emitters include records at grid+0x80.

The negative control re-runs the whole join with the entities of a
distant frame against each frame's objects. It must collapse.

Output: data/rp4_object_identity_join.json (counts, rates, exclusion
reasons and slot samples; no object RAM bytes).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from census_full_route import RouteState              # noqa: E402
from decode_avsp_object_stream import Rom             # noqa: E402
from verify_avsp_object_corpus import (               # noqa: E402
    decode_actor_entries, read_anchors)

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
OUTPUT = ROOT / "data" / "rp4_object_identity_join.json"
ROM_PATH = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"

WORKRAM_CAPTURE_BASE = 0xFF0000
WORKRAM_VIEW_BASE = 0xFF8000
VIEW_OFFSET = WORKRAM_VIEW_BASE - WORKRAM_CAPTURE_BASE
ACTOR_ANCHOR = 0xFF8380
ALLOCATION_GRID = 0x40
# Observed emitters reach 0xFFCD80, so the scan must cover at least
# (0xFFCD80 - 0xFF8380) / 0x40 = 296 allocation slots.
ACTOR_SLOTS = 384
POSE_REGION_WIDE = (0x000000, 0x200000)   # the whole program image
ACTOR_STATES = tuple(range(0x01, 0xFF))
FRAME_STEP = 3
# The control lag MUST be a multiple of FRAME_STEP, or the stale frame
# is never one this run sampled and the control silently tests nothing.
CONTROL_LAG = 312
CONFIDENT_PARTS = 2

CLASS_NAMES = {0x00: "player-band", 0x04: "player-auxiliary-band",
               0x1F: "street-alien-band", 0x06: "auxiliary-band",
               0x80: "presentation-band"}


def class_name(class_id: int) -> str:
    return CLASS_NAMES.get(class_id, f"class-0x{class_id:02x}")


def object_words(active: bytes) -> list[int]:
    """The live object stream as words, up to the terminator."""
    words = []
    for offset in range(0, len(active) - 7, 8):
        entry = [int.from_bytes(active[offset + i:offset + i + 2], "big")
                 for i in (0, 2, 4, 6)]
        if entry[1] >= 0x8000 or entry[3] >= 0xFF00:
            break
        words.extend(entry)
    return words


def visible_entry_count(words: list[int]) -> int:
    count = 0
    for offset in range(0, len(words) - 3, 4):
        x, y, _, attribute = words[offset:offset + 4]
        wide = (((attribute >> 8) & 0xF) + 1) * 16 if attribute & 0xFF00 \
            else 16
        high = (((attribute >> 12) & 0xF) + 1) * 16 if attribute & 0xFF00 \
            else 16
        sx, sy = (x & 0x3FF) - 64, (y & 0x3FF) - 16
        if sx + wide > 0 and sx < 384 and sy + high > 0 and sy < 224:
            count += 1
    return count


def find_run_offset(haystack: list[int], needle: list[int]) -> int | None:
    """The 8-byte-aligned (four-word) offset of a verbatim run."""
    size = len(needle)
    if not size or size > len(haystack):
        return None
    first = needle[0]
    for start in range(0, len(haystack) - size + 1, 4):
        if haystack[start] != first:
            continue
        if haystack[start:start + size] == needle:
            return start
    return None


def decode_entities(rom: Rom, workram: bytes) -> list[dict]:
    """Every live actor record's decoded emission run."""
    view = workram[VIEW_OFFSET:]
    anchor_x, anchor_y = read_anchors(view)
    entities = []
    for index in range(ACTOR_SLOTS):
        address = ACTOR_ANCHOR + index * ALLOCATION_GRID
        slot_off = address - WORKRAM_VIEW_BASE
        if slot_off + 0xC0 > len(view):
            break
        record = view[slot_off:slot_off + 0xC0]
        if record[0] not in ACTOR_STATES or record[2] == 0xFF:
            continue
        try:
            flat, meta = decode_actor_entries(
                rom, view, slot_off, anchor_x, anchor_y,
                states=ACTOR_STATES, pose_region=POSE_REGION_WIDE)
        except IndexError:
            # The widened pose window admits pointers that walk past the
            # program image; that is an undecodable record, not a match.
            flat, meta = None, "decode-past-image-end"
        entities.append({
            "address": address,
            "class_id": record[2],
            "type": record[8],
            "words": flat,
            "exclusion": None if flat else meta,
        })
    return entities


def join_frame(entities: list[dict], words: list[int]) -> dict:
    """Join one frame's decoded entities against one object stream."""
    exact = mismatch = absent = 0
    joined_objects = 0
    by_class = Counter()
    confident = Counter()
    samples = []
    for entity in entities:
        if not entity["words"]:
            continue
        offset = find_run_offset(words, entity["words"])
        parts = len(entity["words"]) // 4
        if offset is None:
            absent += 1
            continue
        exact += 1
        joined_objects += parts
        name = class_name(entity["class_id"])
        by_class[name] += parts
        confident["confident" if parts >= CONFIDENT_PARTS
                  else "single-part-flagged"] += 1
        if len(samples) < 8:
            samples.append({
                "actor_address": f"0x{entity['address']:06x}",
                "class": name,
                "type": entity["type"],
                "object_slot": offset // 4,
                "parts": parts,
            })
    return {"exact": exact, "mismatch": mismatch, "absent": absent,
            "joined_objects": joined_objects, "by_class": by_class,
            "confidence": confident, "samples": samples}


def main() -> None:
    if not ROM_PATH.exists():
        raise SystemExit(
            f"private program image missing: {ROM_PATH}")
    rom = Rom(ROM_PATH.read_bytes())
    manifest = json.loads(MANIFEST.read_text())
    street = next(s for s in manifest["scenes"]
                  if s["label"] == "round1-street-gameplay")
    first, last = street["first_frame"], street["last_frame"]

    state = RouteState(CAPTURE)
    history: dict[int, list[dict]] = {}
    previous: tuple[int, bytes] | None = None

    totals = Counter()
    by_class = Counter()
    confidence = Counter()
    exclusions = Counter()
    control = Counter()
    samples: list[dict] = []
    frames_used = 0
    total_objects = 0
    total_visible = 0

    for rec in state.frames():
        f = rec["frame"]
        if f > last:
            break
        if f < first - 1:
            continue
        workram = bytes(state.current["workram"])
        if previous is None or (f - first) % FRAME_STEP:
            previous = (f, workram)
            continue

        entities = decode_entities(rom, previous[1])
        history[previous[0]] = entities
        previous = (f, workram)
        for entity in entities:
            if entity["exclusion"]:
                exclusions[entity["exclusion"].split("-0x")[0]] += 1

        words = object_words(
            state.current["objram2" if rec["active_bank"] else "objram1"])
        frames_used += 1
        total_objects += len(words) // 4
        total_visible += visible_entry_count(words)

        result = join_frame(entities, words)
        totals["exact"] += result["exact"]
        totals["absent"] += result["absent"]
        totals["eligible"] += result["exact"] + result["absent"]
        totals["joined_objects"] += result["joined_objects"]
        by_class.update(result["by_class"])
        confidence.update(result["confidence"])
        if not samples:
            samples = result["samples"]

        stale = history.get(f - 1 - CONTROL_LAG)
        if stale:
            stale_result = join_frame(stale, words)
            control["exact"] += stale_result["exact"]
            control["eligible"] += (stale_result["exact"] +
                                    stale_result["absent"])
            control["joined_objects"] += stale_result["joined_objects"]
    state.close()

    rate = (totals["exact"] / totals["eligible"]
            if totals["eligible"] else 0.0)
    control_rate = (control["exact"] / control["eligible"]
                    if control["eligible"] else 0.0)
    object_rate = (totals["joined_objects"] / total_objects
                   if total_objects else 0.0)
    collapsed = control_rate * 5 < rate

    report = {
        "schema": "rp4-object-identity-join-v1",
        "rule": "an actor record joins the object list at the "
                "8-byte-aligned offset where its ROM-decoded emission "
                "run appears verbatim in the NEXT frame's active bank",
        "falsified_predecessor":
            "nearest-raw-X proximity, whose shuffled-frame control "
            "stayed within about fifteen points of the true rate",
        "workram_base_note":
            "the capture's workram region is based at 0xFF0000; the "
            "0xFF8000-based emitter view is workram[0x8000:]",
        "street_frames": [first, last],
        "frames_used": frames_used,
        "objects_total": total_objects,
        "objects_visible": total_visible,
        "entities_eligible": totals["eligible"],
        "entities_matched_exactly": totals["exact"],
        "entities_absent_from_list": totals["absent"],
        "entity_match_rate": round(rate, 4),
        "objects_joined": totals["joined_objects"],
        "object_join_rate": round(object_rate, 4),
        "joined_objects_by_class": dict(sorted(by_class.items())),
        "match_confidence": dict(sorted(confidence.items())),
        "decode_exclusions": dict(sorted(exclusions.items())),
        "negative_control": {
            "method": f"entities from frame F-{CONTROL_LAG} joined "
                      f"against frame F objects",
            "eligible": control["eligible"],
            "matched": control["exact"],
            "rate": round(control_rate, 4),
            "collapsed": collapsed,
        },
        "class_slot_examples": samples,
        "inputs_sha256": {
            "route_census": hashlib.sha256(
                (ROOT / "data" / "round1_route_census.json")
                .read_bytes()).hexdigest(),
            "scene_manifest": hashlib.sha256(
                MANIFEST.read_bytes()).hexdigest(),
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"identity join: {totals['exact']}/{totals['eligible']} "
          f"entities matched exactly ({rate:.2%}), "
          f"{totals['joined_objects']}/{total_objects} objects joined "
          f"({object_rate:.2%}); control {control_rate:.2%} "
          f"{'COLLAPSED' if collapsed else 'DID NOT COLLAPSE'}")
    if not collapsed or rate < 0.5:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
