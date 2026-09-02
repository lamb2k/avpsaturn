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


def divergence_row(frame, actor_class, source=True, x=10):
    row = {
        "frame": str(frame), "type": "24", "class": actor_class,
        "state": "0200", "substate": "0000", "z": "0", "facing": "0",
        "animation_record": "00000001", "animation_timer": "1",
        "animation_branch": "0", "health": "1",
        "hurt_selector": "00", "attack_selector": "00"}
    if source:
        row.update({"active": "1", "slot": "00ffc300",
                    "x_fp": f"{x << 16:08x}", "y_fp": "00140000"})
    else:
        row.update({"source_slot": "00ffc300", "x": str(x), "y": "20",
                    "x_fp": str(x << 16), "y_fp": str(20 << 16)})
    return row


# Reused fixed-pool slots must retain the identity of the lifetime that owns a
# difference.  A prior class-0x4e lifetime cannot label a later class-0x10 gap.
identity_probe = MODULE.source_native_divergences(
    [divergence_row(1, "4e"), divergence_row(2, "10")],
    [divergence_row(1, "4e", False),
     divergence_row(2, "10", False, x=11)])
assert len(identity_probe) == 1 and identity_probe[0]["class"] == "0x10"

selector_contract = json.loads(MODULE.FIXTURES.read_text(encoding="ascii"))[\
    "scene_manifests"]["coffee_shop"]["animation_collision_selectors"]
selector_probe = MODULE.bind_source_collision_selectors(
    [{"animation_record": "0015fd10", "hurt_selector": "01",
      "attack_selector": "00"}], selector_contract)
assert selector_probe == [
    {"animation_record": "0015fd10", "hurt_selector": "00",
     "attack_selector": "00"}]

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
item["gaps"]["unowned_saturn_actors"] += 1
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
item = copy.deepcopy(BASE)
item["native_capture"]["recurring_spawn_phase_boundary"][
    "native_checkpoints"][1]["phase_u8"] = 191
mutations.append(("recurring spawn phase replay", item))
item = copy.deepcopy(BASE)
item["native_capture"]["recurring_spawn_phase_boundary"][
    "controller_spawn_index"][1]["native_spawn_index_u16"] = 9
mutations.append(("recurring spawn index retention", item))
item = copy.deepcopy(BASE)
item["native_capture"]["recurring_spawn_phase_boundary"][
    "spawned_record12"]["same_frame_presentation"]["native"]\
    ["animation_timer_u16"] = 0
mutations.append(("recurring same-frame presentation delay", item))
item = copy.deepcopy(BASE)
item["native_capture"]["recurring_spawn_phase_boundary"][
    "source_owner_guard_negative_control"]["class01_next_record12_tick"]\
    ["native"]["animation_record"] = "0x0012ddb0"
mutations.append(("generic dynamic-spawn presentation", item))
item = copy.deepcopy(BASE)
item["native_capture"]["recurring_spawn_phase_boundary"][
    "fixed_point_record_reuse"]["frames"]["2514"]["native"][
        "x_fp_s32"] = 0x02a76200
mutations.append(("cleared recurring position fraction", item))
item = copy.deepcopy(BASE)
item["native_capture"]["class1f_final_action_tail"][
    "normalized_action_authority_equal"] = False
mutations.append(("class1f final-tail gameplay normalization", item))
item = copy.deepcopy(BASE)
item["native_capture"]["class1f_final_action_tail"][
    "blanket_animation_ignore_forbidden"] = False
mutations.append(("class1f blanket animation ignore", item))
item = copy.deepcopy(BASE)
item["native_capture"]["class1f_final_action_tail"]["actors"][0][
    "cycle_order_equal"] = False
mutations.append(("class1f final-tail action order", item))
item = copy.deepcopy(BASE)
item["native_capture"]["record20_exit_scheduler_phase"][
    "source_native_projection_equal"] = False
mutations.append(("record20 exit prefix projection", item))
item = copy.deepcopy(BASE)
item["native_capture"]["record20_exit_scheduler_phase"][
    "source_phase_split_after_slot"] = "0x00ffb600"
mutations.append(("record20 exit phase split", item))

for label, mutant in mutations:
    try:
        MODULE.validate_report(mutant)
    except ValueError:
        continue
    raise AssertionError("mutation accepted: " + label)

print("REIMPLEMENT-13 Coffee Shop scene parity: PASS "
      f"({len(mutations)} mutations rejected)")
