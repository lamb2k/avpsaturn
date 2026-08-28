#!/usr/bin/env python3
"""Validate paired source-ledger evidence for the first Coffee Shop contact."""
import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
INVENTORY = json.loads((HERE / "inventory.json").read_text())
BASE = INVENTORY["build_root"]


def load(relative):
    return json.loads((ROOT / relative).read_text())


def validate(report):
    assert report["result"] == "PASS"
    assert report["evidence_mode"] == "COFFEE_SHOP_SOURCE_LEDGER"
    assert report["physical_saturn"] == "UNRUN"
    assert report["state"]["round1_spec_bound"] == 1
    assert report["state"]["round1_entry_valid"] == 1
    assert report["state"]["round1_canaries_ok"] == 1
    assert report["state"]["round1_fallback_count"] == 0
    assert report["state"]["round1_failure_count"] == 0
    assert report["state"]["round1_scheduler_failure_code"] == 0
    assert report["state"]["round1_native_presentation_decode_failures"] == 0
    assert report["state"]["round1_weapon_forbidden_actor_active"] == 0
    assert report["state"]["round1_weapon_forbidden_render_seen"] == 0
    assert report["vdp1_texture_integrity"]["mismatches"] == 0
    samples = report["samples"]
    assert len(samples) == 575
    by_source = {sample["round1_source_frame"]: sample for sample in samples}
    assert all(frame in by_source for frame in range(2280, 2311))
    assert by_source[2287]["round1_native_projectile_damage_writes"] == 0
    assert by_source[2288]["round1_native_projectile_damage_writes"] == 0
    assert by_source[2305]["round1_native_projectile_collision_writes"] == 0
    assert by_source[2305]["round1_native_projectile_damage_writes"] == 0
    assert by_source[2306]["round1_native_projectile_collision_writes"] == 1
    assert by_source[2306]["round1_native_projectile_damage_writes"] == 1
    before = (by_source[2306]["round1_auxiliary_state"] >> 12) & 0x0f
    after = (by_source[2307]["round1_auxiliary_state"] >> 12) & 0x0f
    assert after == before + 1


builds = [load(f"{BASE}/run-{run}/build.json") for run in (1, 2)]
normalizations = [load(f"{BASE}/run-{run}/iso-normalization.json")
                  for run in (1, 2)]
reports = [load(f"{BASE}/run-{run}/coffee-shop-readback.json")
           for run in (1, 2)]

assert builds[0]["source_commit"] == builds[1]["source_commit"]
assert builds[0]["source_tree"] == builds[1]["source_tree"]
assert normalizations[0]["normalized_iso_sha256"] == \
    normalizations[1]["normalized_iso_sha256"]
assert reports[0]["iso_sha256"] == reports[1]["iso_sha256"] == \
    normalizations[0]["normalized_iso_sha256"]
assert reports[0]["samples"] == reports[1]["samples"]
assert reports[0]["source_chronology"] == reports[1]["source_chronology"]
for report in reports:
    validate(report)

mutations = []
item = copy.deepcopy(reports[0])
item["samples"][247]["round1_native_projectile_damage_writes"] = 1
mutations.append(item)
item = copy.deepcopy(reports[0])
next(sample for sample in item["samples"]
     if sample["round1_source_frame"] == 2306)[
         "round1_native_projectile_damage_writes"] = 0
mutations.append(item)
item = copy.deepcopy(reports[0])
next(sample for sample in item["samples"]
     if sample["round1_source_frame"] == 2307)["round1_auxiliary_state"] -= 0x1000
mutations.append(item)
item = copy.deepcopy(reports[0])
item["state"]["round1_fallback_count"] = 1
mutations.append(item)
for mutant in mutations:
    try:
        validate(mutant)
    except AssertionError:
        continue
    raise AssertionError("Coffee Shop emulator mutation was accepted")

print("REIMPLEMENT-13 paired Coffee Shop emulator chronology: PASS "
      f"({len(mutations)} mutations rejected)")
