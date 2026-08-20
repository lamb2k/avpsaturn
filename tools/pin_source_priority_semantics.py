#!/usr/bin/env python3
"""Chapter 1: pin AvP source object-priority semantics per scene.

Retires the falsified actor/foreground class labels: the field
`(x >> 13) & 7` is recorded as `source_object_priority_code`, an
emitted-object property. This sweep produces the tracked semantic
evidence for what each code actually does:

- per scene (joined to the runtime_scene_id manifest): visible and
  offscreen object counts per priority code, position ranges, bounded
  code/attribute histograms, active bank usage;
- the CPS2 OBJ_PRI output register (offset +0x04 in the captured
  `output` region; MAME 0.289 cps2.cpp cps2_objram_latch reads
  m_output[CPS2_OBJ_PRI]) decoded per scene into per-layer priority
  nibbles via the layer-control order, with the implied
  object-code-vs-layer relationships from render_layers' primasks
  construction (mame0289 src/mame/capcom/cps2.cpp, render_layers);
- the CPS-B tile-pen priority-mask registers per scene (expected zero;
  when zero the pen-level front split is inert, and in the 0.289 CPS2
  render path front pens are not drawn at all).

No object RAM bytes or pixels are serialized.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from census_full_route import RouteState  # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
OUTPUT = ROOT / "data" / "source_priority_semantics.json"

# AvP CPS-B layout (tracked census uses the same offsets): layer control
# at +0x26, the four tile-pen priority masks at +0x28..+0x2E.
LAYER_CONTROL_OFFSET = 0x26
MASK_OFFSETS = (0x28, 0x2A, 0x2C, 0x2E)


def decode_layer_priorities(layer_control: int, pri_ctrl: int) -> dict:
    """MAME 0.289 cps2.cpp render_layers decode: draw positions from the
    layer-control order bits; each layer's priority nibble indexed by
    LAYER NUMBER in OBJ_PRI; sprite code i is hidden under layer L
    exactly when i <= pri(L) (primasks construction)."""
    order = [(layer_control >> shift) & 3 for shift in (6, 8, 10, 12)]
    pris = {layer: (pri_ctrl >> (4 * layer)) & 0xF for layer in (1, 2, 3)}
    relationships = {}
    for code in range(8):
        above = sorted(l for l, p in pris.items() if code > p)
        below = sorted(l for l, p in pris.items() if code <= p)
        relationships[str(code)] = {
            "draws_above_layers": above,
            "hidden_under_layers": below,
        }
    return {
        "layer_control": f"0x{layer_control:04x}",
        "draw_order_back_to_front": order,
        "layer_priority_nibbles": {str(k): v for k, v in pris.items()},
        "object_code_relationships": relationships,
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    scenes = manifest["scenes"]
    state = RouteState(CAPTURE)

    per_scene: dict[str, dict] = {}
    scene_iter = iter(scenes)
    scene = next(scene_iter)

    def new_bucket():
        return {
            "visible": Counter(), "offscreen": Counter(),
            "codes": {p: Counter() for p in range(8)},
            "attrs": {p: Counter() for p in range(8)},
            "x_min": {}, "x_max": {}, "y_min": {}, "y_max": {},
            "banks": Counter(), "pri_ctrl": Counter(),
            "layer_control": Counter(), "masks": Counter(),
            "cps_b_hashes": set(),
        }

    bucket = new_bucket()

    def flush(scene, bucket):
        entry = {
            "runtime_scene_id": scene["runtime_scene_id"],
            "label": scene["label"],
            "first_frame": scene["first_frame"],
            "last_frame": scene["last_frame"],
            "visible_by_code":
                {str(k): v for k, v in sorted(bucket["visible"].items())},
            "offscreen_by_code":
                {str(k): v for k, v in sorted(bucket["offscreen"].items())},
            "top_codes_by_priority": {
                str(p): [[f"0x{c:04x}", n]
                         for c, n in bucket["codes"][p].most_common(6)]
                for p in range(8) if bucket["codes"][p]},
            "top_attrs_by_priority": {
                str(p): [[f"0x{a:04x}", n]
                         for a, n in bucket["attrs"][p].most_common(6)]
                for p in range(8) if bucket["attrs"][p]},
            "position_ranges": {
                str(p): {"x": [bucket["x_min"][p], bucket["x_max"][p]],
                         "y": [bucket["y_min"][p], bucket["y_max"][p]]}
                for p in bucket["x_min"]},
            "active_banks": {str(k): v
                             for k, v in sorted(bucket["banks"].items())},
            "obj_pri_register_values":
                {f"0x{k:04x}": v
                 for k, v in sorted(bucket["pri_ctrl"].items())},
            "cps_b_priority_mask_values":
                {str(k): v for k, v in sorted(bucket["masks"].items())},
            "cps_b_state_hashes": sorted(bucket["cps_b_hashes"])[:4],
        }
        dominant_lc = bucket["layer_control"].most_common(1)[0][0]
        dominant_pri = bucket["pri_ctrl"].most_common(1)[0][0]
        entry["priority_decode"] = decode_layer_priorities(
            dominant_lc, dominant_pri)
        per_scene[str(scene["runtime_scene_id"])] = entry

    done = False
    for rec in state.frames():
        f = rec["frame"]
        while f > scene["last_frame"]:
            flush(scene, bucket)
            bucket = new_bucket()
            try:
                scene = next(scene_iter)
            except StopIteration:
                done = True
                break
        if done:
            break
        if f < scene["first_frame"]:
            continue
        active_name = "objram2" if rec["active_bank"] else "objram1"
        active = state.current[active_name]
        bucket["banks"][rec["active_bank"]] += 1
        out = state.current["output"]
        bucket["pri_ctrl"][int.from_bytes(out[4:6], "big")] += 1
        cps_b = state.current["cps_b"]
        bucket["layer_control"][int.from_bytes(
            cps_b[LAYER_CONTROL_OFFSET:LAYER_CONTROL_OFFSET + 2],
            "big")] += 1
        bucket["masks"][tuple(
            int.from_bytes(cps_b[o:o + 2], "big")
            for o in MASK_OFFSETS)] += 1
        bucket["cps_b_hashes"].add(rec["cps_b_hash"])
        for off in range(0, len(active) - 7, 8):
            x = int.from_bytes(active[off:off + 2], "big")
            y = int.from_bytes(active[off + 2:off + 4], "big")
            code = int.from_bytes(active[off + 4:off + 6], "big")
            attr = int.from_bytes(active[off + 6:off + 8], "big")
            if y >= 0x8000 or attr >= 0xFF00:
                break
            pri = (x >> 13) & 7
            sx = (x & 0x3FF) - 64
            sy = (y & 0x3FF) - 16
            w = (((attr >> 8) & 0xF) + 1) * 16 if attr & 0xFF00 else 16
            h = (((attr >> 12) & 0xF) + 1) * 16 if attr & 0xFF00 else 16
            visible = (sx + w > 0 and sx < 384 and
                       sy + h > 0 and sy < 224)
            bucket["visible" if visible else "offscreen"][pri] += 1
            bucket["codes"][pri][code] += 1
            bucket["attrs"][pri][attr] += 1
            if pri not in bucket["x_min"]:
                bucket["x_min"][pri] = bucket["x_max"][pri] = sx
                bucket["y_min"][pri] = bucket["y_max"][pri] = sy
            else:
                bucket["x_min"][pri] = min(bucket["x_min"][pri], sx)
                bucket["x_max"][pri] = max(bucket["x_max"][pri], sx)
                bucket["y_min"][pri] = min(bucket["y_min"][pri], sy)
                bucket["y_max"][pri] = max(bucket["y_max"][pri], sy)
    flush(scene, bucket)
    state.close()

    visible_totals = Counter()
    scenes_with_7 = []
    for sid, entry in per_scene.items():
        for code, count in entry["visible_by_code"].items():
            visible_totals[code] += count
        if entry["visible_by_code"].get("7"):
            scenes_with_7.append(
                {"runtime_scene_id": entry["runtime_scene_id"],
                 "label": entry["label"],
                 "frames": [entry["first_frame"], entry["last_frame"]],
                 "visible_priority_7":
                     entry["visible_by_code"]["7"]})

    report = {
        "schema": "source-priority-semantics-v0",
        "classification": "per-scene counts, histograms, register decodes "
                          "and hashes only; no object RAM or pixels",
        "terminology": "source_object_priority_code = (x >> 13) & 7 on "
                       "the emitted object; an object property, NOT a "
                       "semantic actor class",
        "renderer_reference": "MAME mame0289 src/mame/capcom/cps2.cpp "
                              "render_layers + cps2_render_sprites "
                              "(OBJ_PRI nibbles per layer, sprites drawn "
                              "last-to-first so earlier objram entries "
                              "are on top, code i hidden under layer L "
                              "iff i <= pri(L)); "
                              "src/mame/capcom/cps1_v.cpp "
                              "cps1_update_transmasks (tile-pen masks; "
                              "zero masks = inert)",
        "visible_totals_by_code":
            {k: v for k, v in sorted(visible_totals.items())},
        "priority_7_scenes": scenes_with_7,
        "per_scene": per_scene,
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
    print(f"source priority semantics: {len(per_scene)} scenes, visible "
          f"totals {dict(visible_totals)}, priority-7 scenes "
          f"{[s['label'] for s in scenes_with_7]}")


if __name__ == "__main__":
    main()
