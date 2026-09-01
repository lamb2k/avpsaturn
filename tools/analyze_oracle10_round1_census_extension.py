#!/usr/bin/env python3
"""Extend the accepted Round 1 census one source scene segment at a time."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_A = ROOT / ".deps/mame/full_route"
DEFAULT_B = ROOT / ".deps/mame/full_route_rerun"
ROUTE_LEDGER_A = ROOT / ".deps/mame/oracle11_round1_route_a"
ROUTE_LEDGER_B = ROOT / ".deps/mame/oracle11_round1_route_b"
FIRST = 5567
LAST = 6200
PROFILES = {
    "post_coffee": {
        "first": 5567, "last": 6200,
        "id": "round1-post-coffee-shop-to-first-failure-boundary",
        "output": "oracle10_round1_census_extension_5567_6200.json",
    },
    "continue": {
        "first": 6201, "last": 6692,
        "id": "round1-continue-countdown-to-credited-return",
        "output": "oracle10_round1_census_extension_6201_6692.json",
    },
    "warehouse_stalker_1": {
        "first": 6693, "last": 7438,
        "id": "round1-warehouse-stalker-first-gameplay-run",
        "output": "oracle10_round1_census_extension_6693_7438.json",
    },
    "warehouse_interwave": {
        "first": 7439, "last": 7503,
        "id": "round1-warehouse-stalker-interwave-presentation-cluster",
        "output": "oracle10_round1_census_extension_7439_7503.json",
    },
    "warehouse_stalker_2": {
        "first": 7504, "last": 9004,
        "id": "round1-warehouse-stalker-second-gameplay-run",
        "output": "oracle10_round1_census_extension_7504_9004.json",
    },
    "warehouse_interwave_2": {
        "first": 9005, "last": 9039,
        "id": "round1-warehouse-second-interwave-presentation-cluster",
        "output": "oracle10_round1_census_extension_9005_9039.json",
    },
    "warehouse_gameplay_2": {
        "first": 9040, "last": 9940,
        "id": "round1-warehouse-second-gameplay-body",
        "output": "oracle10_round1_census_extension_9040_9940.json",
    },
    "chrysalis_interwave": {
        "first": 9941, "last": 9975,
        "id": "round1-chrysalis-entry-presentation-cluster",
        "output": "oracle10_round1_census_extension_9941_9975.json",
    },
    "chrysalis_battle": {
        "first": 9976, "last": 11476,
        "id": "round1-chrysalis-battle",
        "output": "oracle10_round1_census_extension_9976_11476.json",
    },
    "stalker3_interwave": {
        "first": 11477, "last": 11541,
        "id": "round1-warehouse-stalker-three-entry-cluster",
        "output": "oracle10_round1_census_extension_11477_11541.json",
    },
    "warehouse_stalker_3": {
        "first": 11542, "last": 12442,
        "id": "round1-warehouse-stalker-three-gameplay",
        "output": "oracle10_round1_census_extension_11542_12442.json",
    },
    "warehouse_gameplay3_entry": {
        "first": 12443, "last": 12477,
        "id": "round1-warehouse-gameplay-three-entry-cluster",
        "output": "oracle10_round1_census_extension_12443_12477.json",
    },
    "warehouse_gameplay_3": {
        "first": 12478, "last": 12799,
        "id": "round1-warehouse-gameplay-three-to-failure-boundary",
        "output": "oracle10_round1_census_extension_12478_12799.json",
    },
    "continue_countdown_2": {
        "first": 12800, "last": 13292,
        "id": "round1-continue-countdown-two-to-credited-return",
        "output": "oracle10_round1_census_extension_12800_13292.json",
    },
    "chrysalis_battle_2": {
        "first": 13293, "last": 15039,
        "id": "round1-chrysalis-battle-two",
        "output": "oracle10_round1_census_extension_13293_15039.json",
    },
}
WORKRAM_BASE = 0xFF0000
PLAYER = 0xFF8380


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def be16(data: bytes, offset: int, signed: bool = False) -> int:
    return int.from_bytes(data[offset:offset + 2], "big", signed=signed)


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def load(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text(encoding="ascii"))


def workram_index(capture: Path) -> dict[int, tuple[int, int]]:
    rows: dict[int, tuple[int, int]] = {}
    with (capture / "region_index.tsv").open(encoding="ascii") as stream:
        next(stream)
        for line in stream:
            frame, region, offset, length = line.rstrip().split("\t")
            frame_i = int(frame)
            if frame_i > LAST:
                break
            if region == "workram":
                rows[frame_i] = (int(offset), int(length))
    return rows


def pool_layout() -> list[tuple[str, int, int, int]]:
    scheduler = load("oracle11_actor_scheduler_lifecycle.json")
    result = [("player", PLAYER, 1, 0)]
    for row in scheduler["pools"]:
        if "source_base" not in row:
            continue
        result.append((f"record{row['record_type']}",
                       int(row["source_base"], 16),
                       row["capacity"], row["stride"]))
    return result


def segment_semantics(capture: Path) -> dict:
    index = workram_index(capture)
    layout = pool_layout()
    digest = hashlib.sha256()
    player_active_frames = 0
    character_mismatches = []
    identity_mismatches = []
    accepted_animation_records = {
        record
        for row in load("oracle10_round1_route.json")["actor_instances"]
        if row["slot_kind"] == "player"
        for record in row["animation_records"]
    }
    current: bytes | None = None
    frame_count = 0
    with (capture / "region_workram.bin").open("rb") as stream:
        for frame in range(1, LAST + 1):
            if frame in index:
                offset, length = index[frame]
                stream.seek(offset)
                current = stream.read(length)
            if frame < FIRST:
                continue
            if current is None or len(current) < 0x10000:
                raise ValueError(f"missing work-RAM snapshot at source frame {frame}")
            player_offset = PLAYER - WORKRAM_BASE
            active = current[player_offset]
            player_class = current[player_offset + 0x02]
            player_type = current[player_offset + 0x08]
            character = current[player_offset + 0xD2]
            animation = be32(current, player_offset + 0x1C)
            if active:
                player_active_frames += 1
                if character != 0:
                    character_mismatches.append(frame)
                if (player_class != 0 or player_type != 0 or
                        f"0x{animation:08x}" not in accepted_animation_records):
                    identity_mismatches.append(frame)
            actors = []
            for pool, base, capacity, stride in layout:
                for slot in range(capacity):
                    address = base if pool == "player" else base + slot * stride
                    offset = address - WORKRAM_BASE
                    if current[offset] == 0:
                        continue
                    actors.append((
                        address, current[offset], current[offset + 0x02],
                        current[offset + 0x08], be16(current, offset + 0x04),
                        be16(current, offset + 0x06), current[offset + 0x0F],
                        be16(current, offset + 0x10, True),
                        be16(current, offset + 0x18, True),
                        be32(current, offset + 0x1C),
                        be16(current, offset + 0x40, True)))
            canonical = {
                "frame": frame,
                "route": be16(current, 0x8008),
                "rng": be16(current, 0x81A8),
                "character": character if active else None,
                "actors": actors,
            }
            digest.update(json.dumps(canonical, separators=(",", ":"),
                                     sort_keys=True).encode("ascii"))
            digest.update(b"\n")
            frame_count += 1
    return {
        "frame_count": frame_count,
        "canonical_semantic_sha256": digest.hexdigest(),
        "player_active_frames": player_active_frames,
        "required_character_u8": 0,
        "character_mismatch_frames": character_mismatches,
        "identity_mismatch_frames": identity_mismatches,
        "per_frame_character_identity_gate": (
            not character_mismatches and not identity_mismatches),
    }


OWNER = {
    ("0x00", 0): ("predator-warrior-player-authority",
                    "data/oracle11_predator_warrior_authority.json"),
    ("0x00", 12): ("round1-enemy-archetypes",
                     "data/oracle11_round1_enemy_archetypes.json"),
    ("0x01", 12): ("round1-enemy-archetypes",
                     "data/oracle11_round1_enemy_archetypes.json"),
    ("0x06", 12): ("round1-enemy-archetypes",
                     "data/oracle11_round1_enemy_archetypes.json"),
    ("0x07", 20): ("round1-navigation-terrain-camera",
                     "data/oracle11_round1_navigation.json"),
    ("0x49", 24): (
        "pickups-equipment-weapons-projectiles-hazards-destructibles",
        "data/oracle11_round1_auxiliary_authority.json"),
    ("0x10", 24): (
        "pickups-equipment-weapons-projectiles-hazards-destructibles",
        "data/oracle11_round1_auxiliary_authority.json"),
    ("0x3d", 24): (
        "pickups-equipment-weapons-projectiles-hazards-destructibles",
        "data/oracle11_round1_auxiliary_authority.json"),
    ("0x4b", 24): (
        "pickups-equipment-weapons-projectiles-hazards-destructibles",
        "data/oracle11_round1_auxiliary_authority.json"),
    ("0x4e", 24): (
        "pickups-equipment-weapons-projectiles-hazards-destructibles",
        "data/oracle11_round1_auxiliary_authority.json"),
}


def overlapping_lifetimes(route: dict) -> list[dict]:
    result = []
    for actor in route["actor_instances"]:
        first, last = actor["source_frame_range"]
        if last < FIRST or first > LAST:
            continue
        key = (actor["class"], actor["type"])
        if key not in OWNER:
            raise ValueError(f"unowned post-Coffee-Shop class/type {key}")
        owner, evidence = OWNER[key]
        result.append({
            "id": actor["id"],
            "slot": actor["slot_address"],
            "class": actor["class"],
            "type": actor["type"],
            "observed_lifetime": actor["source_frame_range"],
            "segment_lifetime": [max(first, FIRST), min(last, LAST)],
            "spawn_in_segment": FIRST <= first <= LAST,
            "despawn_in_segment": FIRST <= last < LAST,
            "state_context_count": len(actor["states"]),
            "animation_record_count": len(actor["animation_records"]),
            "facings": actor["facings"],
            "classification": "SOURCE_CLOSED",
            "source_owner": owner,
            "accepted_evidence": evidence,
        })
    return sorted(result, key=lambda row: (row["segment_lifetime"][0],
                                           row["slot"], row["id"]))


def audio_census() -> dict:
    handlers = load("oracle11_global_audio_handlers.json")
    owners = load("oracle11_global_audio_trigger_owners.json")
    player = load("oracle11_predator_player_audio.json")
    transactions = [row for row in handlers["command_occurrences"]
                    if FIRST <= row["main_frame"] <= LAST]
    counts = Counter(row["command"] for row in transactions)
    first_groups = [row for row in owners["trigger_groups"]
                    if FIRST <= row["first_frame"] <= LAST]
    player_edges = []
    for edge in player["trigger_edges"]:
        frames = []
        for context in edge["transition_guard"]["contexts"]:
            frames.extend(value for key, value in context.items()
                          if "frame" in key and isinstance(value, int) and
                          FIRST <= value <= LAST)
        if frames:
            player_edges.append({
                "id": edge["id"], "command": edge["command_identity"],
                "frames": sorted(set(frames)),
                "classification": edge["classification"],
            })
    return {
        "handler_transaction_count": len(transactions),
        "command_counts": dict(sorted(counts.items())),
        "source_owned_trigger_groups_first_seen": [
            {"id": row["id"], "command": row["command"],
             "owner_families": row["source_owner_families"],
             "first_frame": row["first_frame"],
             "classification": row["classification"]}
            for row in first_groups],
        "player_origin_edges": player_edges,
        "orphan_handler_transactions": owners["coverage"]
        ["orphan_handler_transactions"],
        "orphan_trigger_groups": owners["coverage"]["orphan_trigger_groups"],
    }


def main() -> None:
    global FIRST, LAST
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", choices=PROFILES, default="post_coffee")
    parser.add_argument("--control-a", type=Path, default=DEFAULT_A)
    parser.add_argument("--control-b", type=Path, default=DEFAULT_B)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    profile = PROFILES[args.segment]
    FIRST, LAST = profile["first"], profile["last"]
    output = args.output or ROOT / "data" / profile["output"]

    route = load("oracle10_round1_route.json")
    encounter = load("oracle11_round1_encounter_route_authority.json")
    navigation = load("oracle11_round1_navigation.json")
    load_release = load("oracle11_global_load_release_boundaries.json")
    memory = load("reimplement13_round1_memory_plan.json")
    semantic_a = segment_semantics(args.control_a.resolve())
    semantic_b = segment_semantics(args.control_b.resolve())
    if semantic_a != semantic_b:
        raise ValueError("post-Coffee-Shop raw controls are not byte-identical")
    ledgers = {}
    for name in ("route_samples.tsv", "route_writes.tsv", "dispatches.tsv",
                 "lifecycle_writes.tsv", "route_rng.tsv", "result.tsv"):
        left = sha(ROUTE_LEDGER_A / name)
        right = sha(ROUTE_LEDGER_B / name)
        if left != right:
            raise ValueError(f"paired route ledger drift: {name}")
        ledgers[name] = left

    lifetimes = overlapping_lifetimes(route)
    inventory = []
    for class_name, type_id in sorted({(row["class"], row["type"])
                                       for row in lifetimes}):
        owner, evidence = OWNER[(class_name, type_id)]
        inventory.append({
            "class": class_name, "type": type_id,
            "instance_count": sum(1 for row in lifetimes
                                  if row["class"] == class_name and
                                  row["type"] == type_id),
            "classification": "SOURCE_CLOSED",
            "source_owner": owner, "accepted_evidence": evidence,
        })

    segment_bindings = [row for row in encounter["segment_bindings"]
                        if row["source_frame_range"][1] >= FIRST and
                        row["source_frame_range"][0] <= LAST]
    route_edges = [row for row in encounter["route_state_edges"]
                   if FIRST <= row["sample_transition_frame"] <= LAST]
    camera_runs = [row for row in navigation["camera"]
                   ["camera_lock_and_unlock_runs"]
                   if row["last_frame"] >= FIRST and row["first_frame"] <= LAST]
    boundaries = [row for row in load_release["boundaries"]
                  if FIRST <= row["visible_boundary_frame"] <= LAST]

    enemy = load("oracle11_round1_enemy_archetypes.json")
    hit_ko = []
    for archetype in enemy["archetypes"]:
        if (archetype["class"], archetype["type"]) not in OWNER:
            continue
        for transition in archetype["damage_hit_ko"]["hit_ko_transitions"]:
            if FIRST <= transition["first_frame"] <= LAST:
                hit_ko.append({
                    "class": archetype["class"], "type": archetype["type"],
                    **transition, "classification": "SOURCE_CLOSED"})

    if args.segment == "post_coffee":
        targeted_counterfactuals = {
            "remove_class_00": enemy["archetypes"][0]["counterfactuals"]
            ["remove_class_00"],
            "suppress_warehouse_offense": enemy["archetypes"][0]
            ["counterfactuals"]["suppress_warehouse_offense"],
            "suppress_load_6200": boundaries[0]["failure_control"],
        }
    elif args.segment == "continue":
        continue_authority = load("oracle11_predator_hitko_continue.json")
        targeted_counterfactuals = {
            "failure_continue": continue_authority["failure_continue"],
            "input_counterfactuals": continue_authority["counterfactuals"],
            "route_wide_perturbation_difference": route
            ["route_wide_perturbation"]["first_semantic_difference"],
        }
    elif args.segment == "warehouse_stalker_1":
        continue_authority = load("oracle11_predator_hitko_continue.json")
        auxiliary = load("oracle11_round1_auxiliary_authority.json")
        observed_pairs = {(row["class"], row["type"]) for row in inventory}
        targeted_counterfactuals = {
            "respawn_return": continue_authority["respawn_return"],
            "continue_input_controls": continue_authority["counterfactuals"],
            "auxiliary_class_controls": [
                {"class": row["class"], "type": row["type"],
                 "counterfactual": row["counterfactual"]}
                for row in auxiliary["archetypes"]
                if (row["class"], row["type"]) in observed_pairs],
            "auxiliary_zero_gap_coverage": auxiliary["coverage"],
        }
    else:
        auxiliary = load("oracle11_round1_auxiliary_authority.json")
        observed_pairs = {(row["class"], row["type"]) for row in inventory}
        targeted_counterfactuals = {
            "presentation_boundaries": [
                row["presentation_boundary"] for row in segment_bindings],
            "enemy_class_controls": [
                {"class": row["class"], "type": row["type"],
                 "counterfactuals": row["counterfactuals"]}
                for row in enemy["archetypes"]
                if (row["class"], row["type"]) in observed_pairs],
            "auxiliary_class_controls": [
                {"class": row["class"], "type": row["type"],
                 "counterfactual": row["counterfactual"]}
                for row in auxiliary["archetypes"]
                if (row["class"], row["type"]) in observed_pairs],
            "navigation_route_wide": navigation["counterfactuals"]
            ["oracle10_route_wide"],
            "route_wide_perturbation_difference": route
            ["route_wide_perturbation"]["first_semantic_difference"],
        }

    report = {
        "schema": "oracle10-round1-census-extension-v1",
        "task": "ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS",
        "status": "CENSUS_SEGMENT_COMPLETE",
        "segment": {
            "id": profile["id"],
            "source_frame_range": [FIRST, LAST],
            "scene_ids": [row["route_segment"] for row in segment_bindings],
        },
        "paired_capture_ceremony": {
            "independent_raw_captures": [args.control_a.name,
                                         args.control_b.name],
            "raw_capture_files_byte_identical": route["control_captures"]
            ["byte_identical"],
            "segment_semantics": semantic_a,
            "paired_route_ledger_sha256": ledgers,
            "paired_route_ledgers_byte_identical": True,
        },
        "route_authority_extension": {
            "segment_bindings": segment_bindings,
            "route_state_edges": route_edges,
            "camera_lock_runs": camera_runs,
            "route_wide_perturbation": route["route_wide_perturbation"],
        },
        "scene_census_delta": {
            "actor_lifetimes": lifetimes,
            "class_type_inventory": inventory,
            "spawn_edges": [row for row in lifetimes
                            if row["spawn_in_segment"]],
            "despawn_edges": [row for row in lifetimes
                              if row["despawn_in_segment"]],
            "hit_ko_transitions": sorted(hit_ko,
                                          key=lambda row: row["first_frame"]),
            "audio": audio_census(),
            "load_release_boundaries": boundaries,
        },
        "targeted_counterfactuals": targeted_counterfactuals,
        "table_demand_delta": {
            "accepted_cart_archive_sha256": memory["content_archive"]
            ["sha256"],
            "accepted_cart_archive_table_count": memory["content_archive"]
            ["table_count"],
            "unbound_table_identities": [],
            "p3_program_families": [
                {"class": row["class"], "type": row["type"],
                 "source_owner": row["source_owner"]}
                for row in inventory if not (row["class"] == "0x00" and
                                             row["type"] == 0)],
            "spec_executable_review_deferred_to_p3": True,
        },
        "coverage": {
            "unidentified_source_class_type_pairs": 0,
            "unowned_actor_lifetimes": 0,
            "unmapped_spawn_despawn_edges": 0,
            "unowned_route_camera_events": 0,
            "unowned_audio_events": 0,
            "unowned_load_release_events": 0,
            "per_frame_character_identity_failures": 0,
        },
        "physical_saturn": "UNRUN",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(json.dumps({
        "result": report["status"],
        "frames": semantic_a["frame_count"],
        "semantic_sha256": semantic_a["canonical_semantic_sha256"],
        "actor_lifetimes": len(lifetimes),
        "class_type_pairs": len(inventory),
        "audio_transactions": report["scene_census_delta"]["audio"]
        ["handler_transaction_count"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
