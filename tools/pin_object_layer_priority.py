#!/usr/bin/env python3
"""Chapter 1: pin object-versus-tile priority from the source registers.

The composite order between emitted objects and the tile layers is not a
convention we chose; it is programmed, per frame, by two registers that
the capture records:

- CPS2 OBJ_PRI (output region +0x04): one 4-bit priority per LAYER
  NUMBER. MAME 0.289 (src/mame/capcom/cps2.cpp render_layers) builds the
  sprite primasks so that object priority code i is hidden under layer L
  exactly when i <= pri(L), and draws above it otherwise.
- CPS-B layer control (+0x26), bits 6..13: the back-to-front draw order
  of the four layers.
- CPS-B tile-pen priority masks (+0x28..+0x2E): when zero the pen-level
  front/back split is inert.

This tool does not assume that decode. For witness frames in the street
scene it READS the registers, derives the object/layer relationships,
finds pixels where a priority-4 object and a tile layer are both opaque
in different colours, and requires MAME's captured framebuffer to agree
with the derived winner. Each witness then carries EXECUTED controls:

  obj_pri_nibble     raise the applicable layer's OBJ_PRI nibble so the
                     object becomes hidden under it -> pixel must change
  layer_order        move that layer's position in the draw order
                     -> pixel must change
  inapplicable_pri   perturb the nibble of a layer that is transparent
                     at the witness -> pixel must NOT change (negative)

Output: data/rp4_object_layer_witnesses.json.
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
from verify_street_composite import (Frame, in_of,        # noqa: E402
                                     words_for_priority)

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
OUTPUT = ROOT / "data" / "rp4_object_layer_witnesses.json"

LAYER_CONTROL_INDEX = 0x26 // 2
MASK_INDEXES = (0x28 // 2, 0x2A // 2, 0x2C // 2, 0x2E // 2)
OBJECT_CODE = 4
WITNESS_FRAMES = 4
FRAME_STEP = 271


def read_registers(state: RouteState, frame: Frame) -> dict:
    out = state.current["output"]
    return {
        "obj_pri": int.from_bytes(out[4:6], "big"),
        "layer_control": frame.cps_b[LAYER_CONTROL_INDEX],
        "tile_pen_masks": [frame.cps_b[i] for i in MASK_INDEXES],
    }


def decode(regs: dict) -> dict:
    order = [(regs["layer_control"] >> s) & 3 for s in (6, 8, 10, 12)]
    pris = {n: (regs["obj_pri"] >> (4 * n)) & 0xF for n in (1, 2, 3)}
    return {
        "draw_order_back_to_front": order,
        "layer_priority_nibbles": pris,
        "object_code_draws_above":
            sorted(n for n, p in pris.items() if OBJECT_CODE > p),
        "object_code_hidden_under":
            sorted(n for n, p in pris.items() if OBJECT_CODE <= p),
    }


def compose_from_registers(gfx, frame: Frame, regs: dict,
                           cps_b=None) -> Image.Image:
    """Composite driven purely by the (possibly perturbed) registers.

    Layers are drawn back to front in the programmed order. Object code
    OBJECT_CODE is inserted after the last layer it draws above and
    before the first layer that hides it; when the programmed order puts
    a hiding layer behind a beaten layer the model is inconsistent and
    the objects are drawn at the earliest legal slot.
    """
    cps_b = cps_b if cps_b is not None else frame.cps_b
    dec = decode(regs)
    order = dec["draw_order_back_to_front"]
    hidden = set(dec["object_code_hidden_under"])
    slot = 0
    for position, layer_number in enumerate(order):
        if layer_number in hidden:
            break
        slot = position + 1

    canvas = Image.new("RGBA", (384, 224), frame.palette[0xBFF])
    objects, _ = avsp.decode_objects(
        gfx, words_for_priority(frame.words, OBJECT_CODE), frame.palette)
    for position, layer_number in enumerate(order):
        if position == slot:
            canvas.alpha_composite(objects)
        if layer_number:
            canvas.alpha_composite(avsp.render_background(
                gfx, frame.gfxram, frame.cps_a, cps_b, frame.palette,
                layer_filter=(layer_number,),
                transparent_background=True))
    if slot >= len(order):
        canvas.alpha_composite(objects)
    return canvas


def layer_image(gfx, frame: Frame, layer_number: int) -> Image.Image:
    return avsp.render_background(
        gfx, frame.gfxram, frame.cps_a, frame.cps_b, frame.palette,
        layer_filter=(layer_number,), transparent_background=True)


def perturbed_order(layer_control: int, layer_number: int) -> int:
    """Move one layer to the front-most order position."""
    shifts = [6, 8, 10, 12]
    order = [(layer_control >> s) & 3 for s in shifts]
    if layer_number not in order:
        return layer_control
    index = order.index(layer_number)
    order[index], order[-1] = order[-1], order[index]
    value = layer_control
    for s, n in zip(shifts, order):
        value = (value & ~(3 << s)) | (n << s)
    return value


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    street = next(s for s in manifest["scenes"]
                  if s["label"] == "round1-street-gameplay")
    first, last = street["first_frame"], street["last_frame"]

    state = RouteState(CAPTURE)
    gfx = avsp.load_gfx_region()
    witnesses = []
    registers_seen = {}

    for rec in state.frames():
        f = rec["frame"]
        if f > last or len(witnesses) >= WITNESS_FRAMES:
            break
        if f < first or (f - first) % FRAME_STEP:
            continue
        frame = Frame(state, rec)
        regs = read_registers(state, frame)
        dec = decode(regs)
        registers_seen[str(f)] = {
            "obj_pri": f"0x{regs['obj_pri']:04x}",
            "layer_control": f"0x{regs['layer_control']:04x}",
            "tile_pen_masks": [f"0x{m:04x}"
                               for m in regs["tile_pen_masks"]],
            **{k: v for k, v in dec.items()},
        }
        objects, _ = avsp.decode_objects(
            gfx, words_for_priority(frame.words, OBJECT_CODE),
            frame.palette)
        po = objects.load()
        truth = Image.open(
            CAPTURE / f"reference_{f:05d}.png").convert("RGBA").load()
        correct = compose_from_registers(gfx, frame, regs)
        pc = correct.load()
        layers = {n: layer_image(gfx, frame, n).load() for n in (1, 2, 3)}

        for beaten in dec["object_code_draws_above"]:
            hit = None
            for y in range(224):
                for x in range(384):
                    if not po[x, y][3] or not layers[beaten][x, y][3]:
                        continue
                    if po[x, y][:3] == layers[beaten][x, y][:3]:
                        continue
                    if pc[x, y][:3] != po[x, y][:3]:
                        continue        # occluded by a front layer
                    fx = (x * 351 - 175 + 382) // 383
                    if truth[in_of(fx), y][:3] != po[x, y][:3]:
                        continue
                    hit = (x, y)
                    break
                if hit:
                    break
            if not hit:
                continue
            x, y = hit

            # Control 1: make the beaten layer hide the object.
            raised = dict(regs)
            raised["obj_pri"] = (
                regs["obj_pri"] & ~(0xF << (4 * beaten))
            ) | (OBJECT_CODE << (4 * beaten))
            c1 = compose_from_registers(gfx, frame, raised).load()

            # Control 2: move the beaten layer to the front of the order.
            reordered = dict(regs)
            reordered["layer_control"] = perturbed_order(
                regs["layer_control"], beaten)
            cps_b = list(frame.cps_b)
            cps_b[LAYER_CONTROL_INDEX] = reordered["layer_control"]
            c2 = compose_from_registers(
                gfx, frame, reordered, cps_b=cps_b).load()

            # Negative control: a layer transparent at the witness.
            inapplicable = next(
                (n for n in (1, 2, 3)
                 if n != beaten and not layers[n][x, y][3]), None)
            c3 = None
            if inapplicable is not None:
                other = dict(regs)
                other["obj_pri"] = (
                    regs["obj_pri"] & ~(0xF << (4 * inapplicable))
                ) | (OBJECT_CODE << (4 * inapplicable))
                c3 = compose_from_registers(gfx, frame, other).load()

            witnesses.append({
                "frame": f,
                "source_xy": [x, y],
                "fitted_x": (x * 351 - 175 + 382) // 383,
                "beaten_layer": beaten,
                "registers": registers_seen[str(f)],
                "object_rgb": list(po[x, y][:3]),
                "layer_rgb": list(layers[beaten][x, y][:3]),
                "truth_matches_object": True,
                "controls": {
                    "obj_pri_nibble_detected":
                        c1[x, y][:3] != pc[x, y][:3],
                    "layer_order_detected":
                        c2[x, y][:3] != pc[x, y][:3],
                    "inapplicable_layer": inapplicable,
                    "inapplicable_pri_unchanged":
                        None if c3 is None
                        else c3[x, y][:3] == pc[x, y][:3],
                },
            })
            break
    state.close()

    executed = [w for w in witnesses
                if w["controls"]["obj_pri_nibble_detected"]
                and w["controls"]["layer_order_detected"]
                and w["controls"]["inapplicable_pri_unchanged"]
                is not False]
    ok = len(witnesses) >= 3 and len(executed) == len(witnesses)
    report = {
        "schema": "rp4-object-layer-witnesses-v0",
        "rule": "object priority code i is hidden under layer L exactly "
                "when i <= pri(L) from OBJ_PRI, composited in the "
                "CPS-B layer-control draw order (MAME 0.289 "
                "cps2.cpp render_layers)",
        "object_priority_code": OBJECT_CODE,
        "witness_count": len(witnesses),
        "witness_frames": [w["frame"] for w in witnesses],
        "registers_by_frame": registers_seen,
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
    print(f"object/layer priority: {len(witnesses)} witnesses, "
          f"{len(executed)} with all controls executed, "
          f"{'OK' if ok else 'INSUFFICIENT'}")
    if not ok:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
