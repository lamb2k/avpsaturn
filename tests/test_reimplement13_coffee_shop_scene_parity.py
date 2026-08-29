#!/usr/bin/env python3
"""Reject omissions and false acceptance in the Coffee Shop scene census."""
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "coffee_shop_scene_parity",
    ROOT / "tools" / "capture_reimplement13_coffee_shop_scene.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ARTIFACT = ROOT / "data" / "reimplement13_coffee_shop_scene_parity.json"
BASE_BYTES = ARTIFACT.read_bytes()
# A complete native lifetime row is retained as each missing source body is
# implemented.  Keep the one-line manifest bounded without penalizing real
# population parity growth.
assert len(BASE_BYTES) < 1_600_000, "Coffee Shop manifest is not compact"
assert BASE_BYTES.count(b"\n") == 1, "Coffee Shop manifest lost compact encoding"
BASE = json.loads(BASE_BYTES)

MODULE.validate_report(BASE)
mutations = []
item = copy.deepcopy(BASE)
item["actor_lifetime_timeline"]["source"].pop()
mutations.append(("source actor omission", item))
item = copy.deepcopy(BASE)
next(row for row in item["scene_component_map"]
     if row["classification"] == "NATIVE_IMPLEMENTED")["native_owner"] = None
mutations.append(("implemented owner omission", item))
item = copy.deepcopy(BASE)
item["spawn_despawn_timeline"].pop()
mutations.append(("spawn edge omission", item))
item = copy.deepcopy(BASE)
item["gaps"]["retained_gameplay_authorities"] = 1
item["acceptance"] = {"all_zero": False, "ready": True}
mutations.append(("retained authority false acceptance", item))
item = copy.deepcopy(BASE)
item["gaps"]["unowned_saturn_actors"] = 1
mutations.append(("native owner count drift", item))
item = copy.deepcopy(BASE)
item["missing_source_lifetime_ids"].pop()
mutations.append(("missing lifetime omission", item))
item = copy.deepcopy(BASE)
item["native_capture"]["first_button1_collision"][
    "native_damage_transaction"]["attack_record"] = "0x00030cb6"
mutations.append(("first collision attack record substitution", item))
item = copy.deepcopy(BASE)
item["native_capture"]["first_button1_collision"][
    "native_impact_transaction"]["allocation_visible_frame"] = 2308
mutations.append(("first impact allocation delay", item))
item = copy.deepcopy(BASE)
item["native_capture"]["fixed_slot_reuse_presentation"]["native"][1][
    "animation_record"] = "0x00000000"
mutations.append(("fixed-slot reused presentation clear", item))
item = copy.deepcopy(BASE)
item["native_capture"]["record4_parent_fixed_trajectory"]["native_anchors"][0][
    "x_fp_s32"] = "0x03b50000"
mutations.append(("record4 fixed-slot fractional residue clear", item))
item = copy.deepcopy(BASE)
item["native_capture"]["record4_parent_fixed_trajectory"]["native_anchors"][0][
    "angle_u8"] = 47
mutations.append(("record4 truncated target range", item))
item = copy.deepcopy(BASE)
item["native_capture"]["record4_parent_fixed_trajectory"]["native_anchors"][3][
    "animation_record"] = "0x0002fbb8"
mutations.append(("record4 terminal presentation early exit", item))
item = copy.deepcopy(BASE)
item["native_capture"]["class1f_action16_rng_reuse"][
    "native_seed_after_visible_frame"] = "0x1614"
mutations.append(("class1f action-0x16 duplicate RNG call", item))
item = copy.deepcopy(BASE)
item["native_capture"]["class1f_action16_latched_retry"][
    "native_checkpoints"][1]["transition_latch_u8"] = 0
mutations.append(("class1f action-0x16 latched retry bypass", item))
item = copy.deepcopy(BASE)
item["native_capture"]["deferred_record4_collision_registration"][
    "native_projectile"][1]["collision_registered_u8"] = 1
mutations.append(("record4 same-scan collision registration", item))

for label, mutant in mutations:
    try:
        MODULE.validate_report(mutant)
    except ValueError:
        continue
    raise AssertionError("mutation accepted: " + label)

print("REIMPLEMENT-13 Coffee Shop scene parity: PASS "
      f"({len(mutations)} mutations rejected)")
