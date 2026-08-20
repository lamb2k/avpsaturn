#!/usr/bin/env python3
"""Chapter 1: pin within-priority-code object ordering from the source.

MAME 0.289 cps2_render_sprites walks the object list from the LAST entry
down to entry 0, so an earlier object-RAM entry is drawn over a later
one: within a single priority code, the earlier slot wins. This tool
proves that against the captured framebuffer rather than assuming it.

For each sampled street frame it builds the full register-driven
composite (tile layers in the programmed draw order, objects inserted at
the slot the OBJ_PRI nibbles dictate) and looks for witness pixels where

- exactly two priority-4 objects are opaque, in different colours, and
  no third priority-4 object covers the pixel;
- the composite agrees with MAME's captured framebuffer, so the model is
  validated at that pixel rather than merely selected there.

The composite colour at such a pixel identifies the winner. Every
witness carries an EXECUTED control: the two entries are reversed in the
object word list and the whole composite is rebuilt, which must move the
pixel to the other object's colour. Pixels where the validated composite
gives the LATER slot are counted as counterexamples and must be zero.

Output: data/rp4_object_order_witnesses.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract_avspu_stage1 as avsp                       # noqa: E402
from census_full_route import RouteState                  # noqa: E402
from verify_street_composite import Frame, in_of          # noqa: E402
from pin_object_layer_priority import (                   # noqa: E402
    OBJECT_CODE, compose_from_registers, read_registers)

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
OUTPUT = ROOT / "data" / "rp4_object_order_witnesses.json"

NEEDED_FRAMES = 3
NEEDED_PAIR_TYPES = 2
FRAME_STEP = 271
MAX_FRAMES = 12


def entries_of(words: list[int]) -> list[dict]:
    """Priority-OBJECT_CODE entries, in object-RAM slot order."""
    out = []
    for offset in range(0, len(words) - 3, 4):
        x, y, code, attribute = words[offset:offset + 4]
        if y >= 0x8000 or attribute >= 0xFF00:
            break
        if ((x >> 13) & 7) != OBJECT_CODE:
            continue
        wide = (((attribute >> 8) & 0xF) + 1) * 16 if attribute & 0xFF00 \
            else 16
        high = (((attribute >> 12) & 0xF) + 1) * 16 if attribute & 0xFF00 \
            else 16
        out.append({"slot": offset // 4, "x": x, "y": y, "code": code,
                    "attr": attribute, "sx": (x & 0x3FF) - 64,
                    "sy": (y & 0x3FF) - 16, "w": wide, "h": high})
    return out


def single(entry) -> list[int]:
    return [entry["x"], entry["y"], entry["code"], entry["attr"],
            0, 0x8000, 0, 0]


def swap_entries(words: list[int], a_slot: int, b_slot: int) -> list[int]:
    out = list(words)
    a, b = a_slot * 4, b_slot * 4
    out[a:a + 4], out[b:b + 4] = out[b:b + 4], out[a:a + 4]
    return out


def shape_label(entry) -> str:
    """Structural label: block size and palette bank, never appearance."""
    return (f"{entry['w']}x{entry['h']}-pal{entry['attr'] & 0x1F:02d}")


def overlaps(a, b) -> bool:
    return (a["sx"] < b["sx"] + b["w"] and b["sx"] < a["sx"] + a["w"] and
            a["sy"] < b["sy"] + b["h"] and b["sy"] < a["sy"] + a["h"])


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    street = next(s for s in manifest["scenes"]
                  if s["label"] == "round1-street-gameplay")
    first, last = street["first_frame"], street["last_frame"]

    state = RouteState(CAPTURE)
    gfx = avsp.load_gfx_region()
    witnesses = []
    pair_types = set()
    frames_with = set()
    frames_examined = 0
    counterexamples = 0

    for rec in state.frames():
        f = rec["frame"]
        if f > last or frames_examined >= MAX_FRAMES:
            break
        if f < first or (f - first) % FRAME_STEP:
            continue
        frames_examined += 1
        frame = Frame(state, rec)
        regs = read_registers(state, frame)
        entries = entries_of(frame.words)
        if len(entries) < 2:
            continue

        composite = compose_from_registers(gfx, frame, regs).load()
        truth = Image.open(
            CAPTURE / f"reference_{f:05d}.png").convert("RGBA").load()
        masks = {}
        for entry in entries:
            image, _ = avsp.decode_objects(gfx, single(entry),
                                           frame.palette)
            masks[entry["slot"]] = image.load()

        hit = None
        for i, a in enumerate(entries):
            for b in entries[i + 1:]:
                if not overlaps(a, b):
                    continue
                pa, pb = masks[a["slot"]], masks[b["slot"]]
                earlier, later = (a, b) if a["slot"] < b["slot"] else (b, a)
                pe = masks[earlier["slot"]]
                pl = masks[later["slot"]]
                for y in range(max(a["sy"], b["sy"], 0),
                               min(a["sy"] + a["h"], b["sy"] + b["h"], 224)):
                    for x in range(max(a["sx"], b["sx"], 0),
                                   min(a["sx"] + a["w"], b["sx"] + b["w"],
                                       384)):
                        if not (pa[x, y][3] and pb[x, y][3]):
                            continue
                        if pa[x, y][:3] == pb[x, y][:3]:
                            continue
                        if any(masks[e["slot"]][x, y][3]
                               for e in entries
                               if e["slot"] not in
                               (a["slot"], b["slot"])):
                            continue        # a third object covers it
                        fitted_x = (x * 351 - 175 + 382) // 383
                        if truth[in_of(fitted_x), y][:3] != \
                                composite[x, y][:3]:
                            continue        # composite unvalidated here
                        if composite[x, y][:3] == pl[x, y][:3]:
                            counterexamples += 1
                            continue
                        if composite[x, y][:3] != pe[x, y][:3]:
                            continue        # a tile layer owns the pixel
                        hit = (x, y, earlier, later)
                        break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                break
        if not hit:
            continue

        x, y, earlier, later = hit
        swapped_words = swap_entries(frame.words, earlier["slot"],
                                     later["slot"])
        swapped_frame = Frame.__new__(Frame)
        swapped_frame.__dict__ = dict(frame.__dict__)
        swapped_frame.words = swapped_words
        swapped = compose_from_registers(gfx, swapped_frame, regs).load()
        pair_type = "/".join(sorted((shape_label(earlier),
                                     shape_label(later))))
        witnesses.append({
            "frame": f,
            "source_xy": [x, y],
            "fitted_x": (x * 351 - 175 + 382) // 383,
            "pair_type": pair_type,
            "earlier": {"slot": earlier["slot"],
                        "code": f"0x{earlier['code']:04x}",
                        "attr": f"0x{earlier['attr']:04x}",
                        "source_xy": [earlier["sx"], earlier["sy"]]},
            "later": {"slot": later["slot"],
                      "code": f"0x{later['code']:04x}",
                      "attr": f"0x{later['attr']:04x}",
                      "source_xy": [later["sx"], later["sy"]]},
            "winner": "earlier object-RAM slot",
            "composite_matches_capture": True,
            "earlier_rgb": list(masks[earlier["slot"]][x, y][:3]),
            "later_rgb": list(masks[later["slot"]][x, y][:3]),
            "reversed_entries_control_detected":
                swapped[x, y][:3] == masks[later["slot"]][x, y][:3],
        })
        pair_types.add(pair_type)
        frames_with.add(f)
    state.close()

    ok = (len(frames_with) >= NEEDED_FRAMES and
          len(pair_types) >= NEEDED_PAIR_TYPES and
          counterexamples == 0 and
          bool(witnesses) and
          all(w["reversed_entries_control_detected"] for w in witnesses))
    report = {
        "schema": "rp4-object-order-witnesses-v0",
        "rule": "within one source object priority code the EARLIER "
                "object-RAM entry wins, because MAME 0.289 "
                "cps2_render_sprites draws the list last-to-first",
        "object_priority_code": OBJECT_CODE,
        "pair_type_basis": "structural: object block size and palette "
                           "bank, never rendered appearance",
        "frames_examined": frames_examined,
        "witness_count": len(witnesses),
        "distinct_frames": sorted(frames_with),
        "pair_types": sorted(pair_types),
        "counterexamples": counterexamples,
        "witnesses": witnesses,
        "requirements_met": ok,
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
    print(f"object order: {len(witnesses)} witnesses over "
          f"{len(frames_with)} frames, pair types {len(pair_types)}, "
          f"counterexamples {counterexamples}, "
          f"{'OK' if ok else 'INSUFFICIENT'}")
    if not ok:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
