#!/usr/bin/env python3
"""RP4 v1: execute the source-side controls of the source-order contract.

v0 asserted that the object priority code names an actor class and that
Round 1 contains a deliberate actor-over-foreground overlap. Both were
falsified route-wide and that verdict is preserved, not rewritten.

v1 asserts what the hardware is actually programmed to do:

  within one source object priority code the EARLIER object-RAM entry
  wins, and the code's relationship to each tile layer is fixed by the
  OBJ_PRI nibbles under the CPS-B layer-control draw order, with the
  tile-pen priority masks measured zero and therefore inert.

Each control perturbs exactly one input, rebuilds the whole composite,
and compares the result against what the decoded model PREDICTS. A
control passes when prediction and observation agree, which is stricter
than "the pixel changed": the mask-bit control predicts NO change,
because zero masks are inert in the CPS2 render path, and a change there
would falsify the model just as surely as a missing change elsewhere.

Results merge into data/rp4_v1_source_order.json.
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
    LAYER_CONTROL_INDEX, MASK_INDEXES, OBJECT_CODE,
    compose_from_registers, perturbed_order, read_registers)
from pin_street_object_order import entries_of, swap_entries  # noqa: E402
from rp4_status import build_v1_status, v1_exit_code      # noqa: E402

CAPTURE = ROOT / ".deps" / "mame" / "full_route"
MANIFEST = ROOT / "data" / "avsp_scene_manifest.json"
ORDER_WITNESSES = ROOT / "data" / "rp4_object_order_witnesses.json"
LAYER_WITNESSES = ROOT / "data" / "rp4_object_layer_witnesses.json"
OUTPUT = ROOT / "data" / "rp4_v1_source_order.json"


def differing_pixels(a: Image.Image, b: Image.Image) -> int:
    pa, pb = a.load(), b.load()
    width, height = a.size
    return sum(1 for y in range(height) for x in range(width)
               if pa[x, y][:3] != pb[x, y][:3])


def load_frame(state: RouteState, target: int):
    for rec in state.frames():
        if rec["frame"] == target:
            return Frame(state, rec), read_registers(state, Frame(
                state, rec))
    raise SystemExit(f"frame {target} not present in the capture")


def main() -> None:
    order = json.loads(ORDER_WITNESSES.read_text())
    layers = json.loads(LAYER_WITNESSES.read_text())
    witness = order["witnesses"][0]
    target = witness["frame"]

    state = RouteState(CAPTURE)
    frame, regs = load_frame(state, target)
    state.close()
    gfx = avsp.load_gfx_region()

    correct = compose_from_registers(gfx, frame, regs)
    truth = Image.open(
        CAPTURE / f"reference_{target:05d}.png").convert("RGBA")
    x, y = witness["source_xy"]
    controls: dict[str, dict] = {}

    def record(name: str, perturbed: Image.Image, predicted_change: bool,
               note: str) -> None:
        changed = differing_pixels(correct, perturbed)
        controls[name] = {
            "detected": (changed > 0) == predicted_change,
            "predicted_change": predicted_change,
            "pixels_changed": changed,
            "note": note,
        }

    # 1. Reverse the two same-code entries of the witness pair.
    swapped = list(frame.words)
    swapped = swap_entries(swapped, witness["earlier"]["slot"],
                           witness["later"]["slot"])
    reversed_frame = Frame.__new__(Frame)
    reversed_frame.__dict__ = dict(frame.__dict__)
    reversed_frame.words = swapped
    record("reverse_same_code_entries",
           compose_from_registers(gfx, reversed_frame, regs), True,
           "the earlier entry wins, so exchanging the pair must move "
           "the witness pixel")

    # 2. Change one object's source priority code.
    recoded = list(frame.words)
    slot = witness["earlier"]["slot"] * 4
    recoded[slot] = (recoded[slot] & ~0xE000) | (1 << 13)
    recoded_frame = Frame.__new__(Frame)
    recoded_frame.__dict__ = dict(frame.__dict__)
    recoded_frame.words = recoded
    record("change_source_priority_code",
           compose_from_registers(gfx, recoded_frame, regs), True,
           "code 1 is hidden under every tile layer, so the object must "
           "leave the visible composite")

    # 3. Flip a CPS-B tile-pen priority mask bit.
    masked = list(frame.cps_b)
    masked[MASK_INDEXES[0]] ^= 0x0001
    masked_frame = Frame.__new__(Frame)
    masked_frame.__dict__ = dict(frame.__dict__)
    masked_frame.cps_b = masked
    record("flip_cps_b_mask_bit",
           compose_from_registers(gfx, masked_frame, regs, cps_b=masked),
           False,
           "the measured masks are zero and the CPS2 render path does "
           "not draw front pens, so the split is inert: the model "
           "predicts NO change, and any change would falsify it")

    # 4. Change the layer-order field.
    beaten = layers["witnesses"][0]["beaten_layer"]
    reordered = dict(regs)
    reordered["layer_control"] = perturbed_order(
        regs["layer_control"], beaten)
    order_cps_b = list(frame.cps_b)
    order_cps_b[LAYER_CONTROL_INDEX] = reordered["layer_control"]
    record("change_layer_order_field",
           compose_from_registers(gfx, frame, reordered,
                                  cps_b=order_cps_b), True,
           "moving the beaten layer to the front of the draw order must "
           "change the composite")

    # 5. Shift the witness object by one fitted pixel.
    shifted = list(frame.words)
    shifted[slot] = (shifted[slot] & ~0x3FF) | ((shifted[slot] + 1) & 0x3FF)
    shifted_frame = Frame.__new__(Frame)
    shifted_frame.__dict__ = dict(frame.__dict__)
    shifted_frame.words = shifted
    record("shift_object_one_fitted_pixel",
           compose_from_registers(gfx, shifted_frame, regs), True,
           "a one-pixel source shift must survive the endpoint-aligned "
           "384-to-352 map at the witness column")

    fitted_x = witness["fitted_x"]
    composite_mismatch = int(
        correct.load()[in_of(fitted_x), y][:3] !=
        truth.load()[in_of(fitted_x), y][:3])

    status = build_v1_status(
        controls,
        {"object_order": order["witness_count"],
         "object_layer": layers["witness_count"],
         "counterexamples": order["counterexamples"]},
        composite_mismatch)

    report = {
        "schema": "rp4-v1-source-order-v0",
        "contract": "within one source object priority code the earlier "
                    "object-RAM entry wins; the code's relationship to "
                    "each tile layer is set by OBJ_PRI under the CPS-B "
                    "layer-control draw order; zero tile-pen masks are "
                    "inert",
        "witness_frame": target,
        "witness_source_xy": [x, y],
        "controls": controls,
        "status": status,
        "saturn_controls_note":
            "the three Saturn-side controls (CMDCOLR priority bits, "
            "command order, PRIS/PRIN) are executed against the "
            "StreetTest build, not here",
        "inputs_sha256": {
            "order_witnesses": hashlib.sha256(
                ORDER_WITNESSES.read_bytes()).hexdigest(),
            "layer_witnesses": hashlib.sha256(
                LAYER_WITNESSES.read_bytes()).hexdigest(),
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    passed = sum(1 for c in controls.values() if c["detected"])
    print(f"rp4 v1 source controls: {passed}/{len(controls)} agree with "
          f"the model; rp4_v1_status={status['rp4_v1_status']} "
          f"(Saturn controls not run here)")
    for name, control in sorted(controls.items()):
        if not control["detected"]:
            print(f"  MISMATCH {name}: predicted change="
                  f"{control['predicted_change']}, pixels changed="
                  f"{control['pixels_changed']}")
    raise SystemExit(v1_exit_code(status))


if __name__ == "__main__":
    main()
