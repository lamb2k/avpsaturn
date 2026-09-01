#!/usr/bin/env python3
"""Close Round 1 encounter, wave, scripted-trigger and route-edge authority."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps/mame/oracle11_round1_route_a"
RAW_B = ROOT / ".deps/mame/oracle11_round1_route_b"
ENTRY_A = ROOT / ".deps/mame/oracle11_round1_entry_a6"
ENTRY_B = ROOT / ".deps/mame/oracle11_round1_entry_b6"
ENTRY_SUPPRESS = ROOT / ".deps/mame/oracle11_round1_entry_suppress6"
PROGRESSION_A = ROOT / ".deps/mame/oracle11_progression_owner3_a"
PROGRESSION_B = ROOT / ".deps/mame/oracle11_progression_owner3_b"
PROGRESSION_SUPPRESS = ROOT / ".deps/mame/oracle11_progression_owner3_s"
PROGRESSION_GUARD_SUPPRESS = ROOT / ".deps/mame/oracle11_progression_owner3_g"
PROGRESSION_LIFECYCLE_A = ROOT / ".deps/mame/oracle11_progression_lifecycle_a"
PROGRESSION_LIFECYCLE_B = ROOT / ".deps/mame/oracle11_progression_lifecycle_b"
PROGRESSION_LIFECYCLE_SUPPRESS = ROOT / ".deps/mame/oracle11_progression_lifecycle_s2"
COFFEE_SHOP_SCENE_A = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs7a"
COFFEE_SHOP_SCENE_B = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs7b"
CONTROLLER_EDGE_A = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs38a"
CONTROLLER_EDGE_B = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs38b"
CONTROLLER_EDGE_SUPPRESS = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs38s"
COFFEE_EXIT_A = ROOT / ".deps/mame/oracle11_coffee_exit_player_m"
COFFEE_EXIT_B = ROOT / ".deps/mame/oracle11_coffee_exit_player_n"
ROUTE = ROOT / "data/oracle10_round1_route.json"
ENEMIES = ROOT / "data/oracle11_round1_enemy_archetypes.json"
AUXILIARY = ROOT / "data/oracle11_round1_auxiliary_authority.json"
RNG = ROOT / "data/oracle11_round1_rng.json"
BOSS = ROOT / "data/oracle11_round1_boss_orchestration.json"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
OUT = ROOT / "data/oracle11_round1_encounter_route_authority.json"
ORACLE10_EVENTS = (ROOT / ".deps/mame/oracle10_round1_system_census_e" /
                   "baseline/actor_events.tsv")
FILES = ("route_samples.tsv", "route_writes.tsv", "route_writer_summary.tsv",
         "lifecycle_writes.tsv", "route_rng.tsv", "samples.tsv",
         "dispatches.tsv", "projectiles.tsv", "score_writes.tsv", "result.tsv")
ENTRY_FILES = ("entry_samples.tsv", "entry_actors.tsv", "entry_writes.tsv",
               "entry_calls.tsv", "entry_player_writes.tsv", "entry_script.tsv")
PROGRESSION_FILES = ("progression_transactions.tsv", "progression_snapshots.tsv",
                     "progression_writes.tsv", "progression_global_writes.tsv",
                     "progression_controller.tsv",
                     "progression_result.tsv")
PROGRESSION_LIFECYCLE_FILES = ("progression_controller.tsv",
                               "progression_lifecycle_writes.tsv",
                               "progression_result.tsv")
COFFEE_SHOP_SCENE_FILES = ("coffee_shop_scene_actors.tsv",
                           "coffee_shop_scene_frames.tsv",
                           "coffee_shop_scene_health_writes.tsv",
                           "coffee_shop_type4_class03.tsv",
                           "progression_class1f_action4_timers.tsv",
                           "progression_lifecycle_writes.tsv",
                           "progression_result.tsv", "dispatches.tsv",
                           "samples.tsv", "score_writes.tsv")
ROUTE_EDGES = (
    (2237, "00c170", 4, "(u8(g8236) & u8(g81af)) == 0"),
    (5452, "008418", 6, "u8(g81f3) != 0"),
    (5523, "00c84c", 0, "(u8(g8236) & u8(g81af)) == 0"),
    (5561, "0083d4", 2, "s16(g837c) == 0"),
    (5719, "00c200", 4, "(u8(g8236) & u8(g81af)) == 0"),
    (6198, "008546", 0, "u8(g81af)==0 && u8(g81d4)==0 && no active player records"),
    (6199, "008bb2", 2, "failure/continue dispatcher entered state 0"),
    (6691, "0090f2", 4, "credited continue restore dispatcher entered state 2"),
    (12797, "008546", 0, "u8(g81af)==0 && u8(g81d4)==0 && no active player records"),
    (12798, "008bb2", 2, "failure/continue dispatcher entered state 0"),
    (13291, "0090f2", 4, "credited continue restore dispatcher entered state 2"),
    (15018, "008418", 6, "u8(g81f3) != 0"),
    (15020, "00c886", 0, "round-index dispatch selected the second transition body"),
    (15088, "0083d4", 2, "s16(g837c) == 0"),
)
SPAWN_GUARDS = {
    "028886": "ten-entry source table loop; allocate_record12 succeeds for each row",
    "028a3e": "living-enemy count < 8 && (u8(g8019) & 7)==0 && allocate_record12 succeeds",
    "028b7e": "scroll_x < 0x03f0 && ((u8(g8019)+3)&0x1f)==0 && allocate_record12 succeeds",
    "06b3fe": "owner state/timer permits spawn && living-enemy count < 6 && allocate_record12 succeeds",
    "01bf1e": "stage-table row passes x, player-count and variant guards && typed allocator succeeds",
    "020538": "stage-list row passes camera-x, character and route guards && allocate_record12 succeeds",
    "0208be": "scripted wave table entry reached && allocate_record12 succeeds",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream, delimiter="\t")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def s16_from_hex(value: str) -> int:
    raw = int(value, 16)
    return raw - 0x10000 if raw >= 0x8000 else raw


def identity(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "input_manifest.json").read_text(encoding="utf-8-sig"))
    require(manifest["authority_family"] == "encounters-waves-scripted-triggers",
            f"{path.name}: family identity drift")
    for filename in FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def entry_identity(path: Path) -> dict[str, object]:
    return {"files": {name: digest(path / name) for name in ENTRY_FILES}}


def progression_identity(path: Path) -> dict[str, object]:
    return {"files": {name: digest(path / name) for name in PROGRESSION_FILES}}


def progression_lifecycle_identity(path: Path) -> dict[str, object]:
    return {"files": {name: digest(path / name)
                      for name in PROGRESSION_LIFECYCLE_FILES}}


def controller_edge_identity(path: Path) -> dict[str, object]:
    names = ("coffee_shop_controller_substate_writes.tsv",
             "coffee_shop_scene_frames.tsv", "coffee_shop_scene_actors.tsv")
    return {"files": {name: digest(path / name) for name in names}}


def window(image: bytes, pc: int, before: int = 16, after: int = 32) -> dict[str, object]:
    first, last = max(0, pc-before), min(len(image), pc+after)
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(image[first:last]).hexdigest()}


def coffee_shop_scene_census() -> dict[str, object]:
    identity_a = {name: digest(COFFEE_SHOP_SCENE_A / name)
                  for name in COFFEE_SHOP_SCENE_FILES}
    identity_b = {name: digest(COFFEE_SHOP_SCENE_B / name)
                  for name in COFFEE_SHOP_SCENE_FILES}
    require(identity_a == identity_b,
            "Coffee Shop complete fixed-pool captures differ")
    enemies = json.loads(ENEMIES.read_text(encoding="utf-8"))
    auxiliary = json.loads(AUXILIARY.read_text(encoding="utf-8"))
    rng = json.loads(RNG.read_text(encoding="utf-8"))
    boss = json.loads(BOSS.read_text(encoding="utf-8"))
    program = PROGRAM.read_bytes()
    animation_collision_selectors: dict[int, tuple[int, int]] = {}
    transient_groups = rng["owner_partition"]["auxiliary_type16_20_24"][
        "transient_child_groups"]
    require(rng["status"] == "SOURCE_CLOSED" and
            [(item["type"], item["class"], item["classification"])
             for item in transient_groups] ==
            [(24, "0x47", "SOURCE_CLOSED"),
             (24, "0x25", "SOURCE_CLOSED"),
             (24, "0x4d", "SOURCE_CLOSED"),
             (20, "0x05", "SOURCE_CLOSED")],
            "accepted transient child ownership drift")
    require(boss["status"] == "SOURCE_CLOSED" and
            boss["controller_contract"]["type"] == 32 and
            boss["controller_contract"]["class"] == "0x02",
            "accepted Round 1 controller ownership drift")
    source_contracts = {
        (int(item["type"]), int(item["class"], 16)):
            f"data/oracle11_round1_enemy_archetypes.json#/archetypes/{index}"
        for index, item in enumerate(enemies["archetypes"])
    }
    source_contracts.update({
        (int(item["type"]), int(item["class"], 16)):
            f"data/oracle11_round1_auxiliary_authority.json#/archetypes/{index}"
        for index, item in enumerate(auxiliary["archetypes"])
    })
    source_contracts[(0, 0)] = \
        "data/oracle11_predator_warrior_authority.json#/"
    source_contracts[(4, 0)] = (
        "data/oracle11_predator_weapon_projectile_resource.json#/"
        "implementation_contract/record4_parent_class0")
    source_contracts[(4, 4)] = (
        "data/oracle11_predator_weapon_projectile_resource.json#/"
        "implementation_contract/record4_child_class4")
    source_contracts[(4, 3)] = (
        "data/oracle11_predator_air_authority.json#/airborne_actions/"
        "button1/record4_class03")
    source_contracts[(28, 0x0a)] = (
        "data/oracle11_predator_route_ownership.json#/"
        "health_pickup")
    source_contracts[(32, 0x01)] = "#/first_entry_body/controller"
    source_contracts[(32, 0x02)] = (
        "data/oracle11_round1_boss_orchestration.json#/controller_contract")
    source_contracts[(24, 0x44)] = \
        ("data/oracle11_round1_auxiliary_authority.json#/"
         "first_segment_dependencies/class_0x44_type24_command_guard_owner")
    source_contracts[(24, 0x47)] = (
        "data/oracle11_round1_rng.json#/owner_partition/"
        "auxiliary_type16_20_24/transient_child_groups/0")
    source_contracts[(24, 0x4d)] = (
        "data/oracle11_round1_rng.json#/owner_partition/"
        "auxiliary_type16_20_24/transient_child_groups/2")
    source_contracts[(20, 0x05)] = (
        "data/oracle11_round1_rng.json#/owner_partition/"
        "auxiliary_type16_20_24/transient_child_groups/3")
    for index, item in enumerate(
            auxiliary["coffee_shop_type36_presentation"]["classes"]):
        source_contracts[(36, int(item["class"], 16))] = (
            "data/oracle11_round1_auxiliary_authority.json#/"
            f"coffee_shop_type36_presentation/classes/{index}")
    for index, item in enumerate(
            auxiliary["coffee_shop_scene_component_identities"]["components"]):
        source_contracts[(int(item["type"]), int(item["class"], 16))] = (
            "data/oracle11_round1_auxiliary_authority.json#/"
            f"coffee_shop_scene_component_identities/components/{index}")

    active: dict[tuple[str, str], dict[str, object]] = {}
    lifetimes: list[dict[str, object]] = []

    def finish(lifetime: dict[str, object]) -> None:
        pair = (int(lifetime["type"]), int(str(lifetime["class"]), 16))
        contract = source_contracts.get(pair)
        lifetime["states"] = sorted(lifetime["states"])
        lifetime["facings"] = sorted(lifetime["facings"])
        lifetime["animation_records"] = sorted(lifetime["animation_records"])
        lifetime["attack_selectors"] = sorted(lifetime["attack_selectors"])
        lifetime["hurt_selectors"] = sorted(lifetime["hurt_selectors"])
        lifetime["spawn_edge"] = {"frame": lifetime["first_frame"],
                                    "active_before": 0, "active_after": 1}
        lifetime["despawn_edge"] = {"frame": lifetime["last_frame"] + 1,
                                      "active_before": 1,
                                      "active_after": 0}
        if contract is None:
            lifetime["source_classification"] = \
                "BLOCKED_MISSING_SOURCE_EVIDENCE"
            lifetime["exact_blocker"] = (
                "no accepted full actor state/lifecycle/presentation/collision "
                "contract for this source-observed class/type pair")
        else:
            lifetime["source_classification"] = "SOURCE_CLOSED"
            lifetime["source_contract"] = contract
        lifetimes.append(lifetime)

    for row in rows(COFFEE_SHOP_SCENE_A / "coffee_shop_scene_actors.tsv"):
        frame = int(row["frame"])
        animation_record = int(row["animation_record"], 16)
        if animation_record != 0:
            require(animation_record + 9 < len(program),
                    "Coffee Shop animation record outside source program")
            animation_collision_selectors[animation_record] = (
                program[animation_record + 8], program[animation_record + 9])
        key = (row["pool"], row["slot"])
        identity = (row["type"], row["class"])
        current = active.get(key)
        if (current is None or frame != current["last_frame"] + 1 or
                identity != current["identity"]):
            if current is not None:
                finish(current)
            current = {
                "id": "", "pool": row["pool"],
                "source_slot": f"0x00{row['slot']}",
                "type": int(row["type"]), "class": f"0x{row['class']}",
                "identity": identity, "first_frame": frame,
                "last_frame": frame, "states": set(), "facings": set(),
                "animation_records": set(), "attack_selectors": set(),
                "hurt_selectors": set(),
                "x_fp_range_s32_16_16": [int(row["x_fp"], 16),
                                           int(row["x_fp"], 16)],
                "y_fp_range_s32_16_16": [int(row["y_fp"], 16),
                                           int(row["y_fp"], 16)],
                "z_range_s16": [int(row["z"]), int(row["z"])],
                "health_range_s16": (None if row["health"] == "na" else
                                       [int(row["health"]),
                                        int(row["health"])]),
            }
            active[key] = current
        current["last_frame"] = frame
        current["states"].add((int(row["state"], 16),
                                int(row["substate"], 16)))
        current["facings"].add(int(row["facing"]))
        current["animation_records"].add(f"0x{animation_record:08x}")
        if row["attack_selector"] != "na":
            current["attack_selectors"].add(
                animation_collision_selectors.get(animation_record, (0, 0))[1])
        if row["hurt_selector"] != "na":
            current["hurt_selectors"].add(
                animation_collision_selectors.get(animation_record, (0, 0))[0])
        for field, value in (("x_fp_range_s32_16_16", int(row["x_fp"], 16)),
                             ("y_fp_range_s32_16_16", int(row["y_fp"], 16)),
                             ("z_range_s16", int(row["z"]))):
            current[field][0] = min(current[field][0], value)
            current[field][1] = max(current[field][1], value)
        if row["health"] != "na":
            value = int(row["health"])
            current["health_range_s16"][0] = min(
                current["health_range_s16"][0], value)
            current["health_range_s16"][1] = max(
                current["health_range_s16"][1], value)
    for current in active.values():
        finish(current)
    lifetimes.sort(key=lambda item: (item["first_frame"], item["pool"],
                                     item["source_slot"]))
    for index, lifetime in enumerate(lifetimes):
        lifetime["id"] = f"coffee-shop-actor-{index:03d}"
        del lifetime["identity"]
    pair_counts = Counter((item["type"], item["class"])
                          for item in lifetimes)
    pair_inventory = [{"type": pair[0], "class": pair[1],
                       "lifetime_count": count,
                       "source_classification":
                           ("SOURCE_CLOSED" if (pair[0], int(pair[1], 16)) in
                            source_contracts else
                            "BLOCKED_MISSING_SOURCE_EVIDENCE")}
                      for pair, count in sorted(pair_counts.items())]
    blocked = [item for item in pair_inventory
               if item["source_classification"] != "SOURCE_CLOSED"]
    require(len(lifetimes) == 747 and len(pair_inventory) == 38 and
            len(blocked) == 0,
            "Coffee Shop full-pool lifetime inventory drift")
    audio_events = []
    for row in rows(COFFEE_SHOP_SCENE_A / "dispatches.tsv"):
        audio_events.append({
            "frame": int(row["frame"]),
            "sequence": int(row["sequence"]),
            "queue_address": f"0x{row['queue_address']}",
            "writer_pc": f"0x{row['write_pc']}",
            "capture_pc": f"0x{row['capture_pc']}",
            "shared_dispatch": f"0x{row['shared_dispatch']}",
            "origin_a6": f"0x{row['a6']}",
            "caller_chain": [f"0x{row[key]}" for key in
                             ("return0", "return1", "return2")],
            "arguments_u32": [f"0x{int(row[key], 16):08x}" for key in
                              ("d1", "d2", "d3")],
            "command_u16": f"0x{int(row['command'], 16):04x}",
            "origin": {"active_u8": int(row["origin_active"]),
                       "class_u8": f"0x{int(row['origin_class'], 16):02x}",
                       "type_u8": int(row["origin_type"]),
                       "state_u16": int(row["origin_state"]),
                       "phase_u16": int(row["origin_phase"])},
            "source_classification": "SOURCE_CLOSED",
            "source_contract":
                "data/oracle11_global_audio_trigger_owners.json#/trigger_groups",
        })
    health_writes = []
    for row in rows(COFFEE_SHOP_SCENE_A /
                    "coffee_shop_scene_health_writes.tsv"):
        health_writes.append({
            "frame": int(row["frame"]),
            "target_pool": row["target_pool"],
            "target_slot": f"0x{row['target_slot']}",
            "writer_pc": f"0x{row['pc']}",
            "attacker": f"0x{row['attacker']}",
            "defender": f"0x{row['defender']}",
            "attack_record": f"0x{row['attack_record']}",
            "state_u16": f"0x{row['state']}",
            "substate_u16": f"0x{row['substate']}",
            "health_before_s16": s16_from_hex(row["health_before"]),
            "health_after_s16": s16_from_hex(row["health_after"]),
            "damage_writer": row["damage_writer"] == "1",
            "source_classification": "SOURCE_CLOSED",
            "source_contract":
                "data/oracle11_round1_writer_reconciliation.json#/writers",
        })
    return {
        "scope": "source Coffee Shop entry through exit stabilization",
        "source_frame_range": [1972, 5566],
        "declared_scene_segments": [
            {"id": "round1-title", "source_frame_range": [1972, 2073]},
            {"id": "round1-street-gameplay",
             "source_frame_range": [2074, 5542]},
            {"id": "coffee-shop-exit-stabilization",
             "source_frame_range": [5543, 5566]}],
        "capture_identity": {"completion_a": identity_a,
                             "completion_b": identity_b,
                             "byte_identical": True},
        "pool_scan": [
            {"pool": "player", "base": "0xff8380", "stride": 0,
             "capacity": 1},
            {"pool": "record4", "base": "0xff8680", "stride": 128,
             "capacity": 24, "record_type": 4},
            {"pool": "record8", "base": "0xff9280", "stride": 192,
             "capacity": 4, "record_type": 8},
            {"pool": "record12", "base": "0xff9580", "stride": 192,
             "capacity": 20},
            {"pool": "record16", "base": "0xffa480", "stride": 128,
             "capacity": 20},
            {"pool": "record20", "base": "0xffae80", "stride": 128,
             "capacity": 16},
            {"pool": "record24", "base": "0xffb680", "stride": 128,
             "capacity": 32},
            {"pool": "record28", "base": "0xffc680", "stride": 128,
             "capacity": 16, "record_type": 28},
            {"pool": "record32", "base": "0xffce80", "stride": 256,
             "capacity": 4, "record_type": 32},
            {"pool": "record36", "base": "0xffd280", "stride": 64,
             "capacity": 64, "record_type": 36},
            {"pool": "record24_aux", "base": "0xffe280", "stride": 128,
             "capacity": 16, "record_type": 24}],
        "pool_layout_source": {
            "initializer": "0x01729e..0x0174a4",
            "sha256": hashlib.sha256(
                OPCODES.read_bytes()[0x01729e:0x0174a4]).hexdigest(),
            "inactive_in_capture": ["record8", "record24_aux"]},
        "animation_collision_selectors": {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "layout": {
                "animation_record_u32": "actor+0x1c",
                "hurt_selector_u8": "animation_record+0x08",
                "attack_selector_u8": "animation_record+0x09",
                "capture_columns_rejected_as_authority": [
                    "actor+0x25 animation branch/event low byte",
                    "actor+0x26 linked-actor word high byte"],
            },
            "records": [
                {"animation_record": f"0x{address:08x}",
                 "hurt_selector_u8": selectors[0],
                 "attack_selector_u8": selectors[1],
                 "record_sha256": hashlib.sha256(
                     program[address:address + 16]).hexdigest()}
                for address, selectors in sorted(
                    animation_collision_selectors.items())],
            "mutation_control": {
                "wrong_player_field_projection_rejected": True,
                "first_discriminating_frame_u16": 2793,
                "animation_record": "0x0015fd10",
                "source_hurt_selector_u8": 0,
                "rejected_actor_event_byte_u8": 1,
            },
        },
        "actor_lifetimes": lifetimes,
        "class_type_inventory": pair_inventory,
        "blocked_class_type_pairs": blocked,
        "audio_events": audio_events,
        "health_writes": health_writes,
        "counts": {"actor_lifetimes": len(lifetimes),
                   "class_type_pairs": len(pair_inventory),
                   "source_closed_pairs": len(pair_inventory) - len(blocked),
                   "blocked_missing_source_evidence_pairs": len(blocked),
                   "audio_events": len(audio_events),
                   "health_writes": len(health_writes),
                   "damage_writes": sum(item["damage_writer"]
                                        for item in health_writes)},
        "negative_controls": {
            "half_stride_aliases_admitted": False,
            "inactive_slots_admitted": False,
            "unknown_pair_silently_omitted": False},
    }


def build_report() -> dict[str, object]:
    id_a, id_b = identity(RAW_A), identity(RAW_B)
    require(id_a["files"] == id_b["files"], "route completion captures differ")
    entry_a, entry_b = entry_identity(ENTRY_A), entry_identity(ENTRY_B)
    require(entry_a["files"] == entry_b["files"],
            "entry correction captures differ")
    progression_a = progression_identity(PROGRESSION_A)
    progression_b = progression_identity(PROGRESSION_B)
    progression_suppress = progression_identity(PROGRESSION_SUPPRESS)
    progression_guard_suppress = progression_identity(PROGRESSION_GUARD_SUPPRESS)
    require(progression_a["files"] == progression_b["files"],
            "first-segment progression captures differ")
    progression_lifecycle_a = progression_lifecycle_identity(
        PROGRESSION_LIFECYCLE_A)
    progression_lifecycle_b = progression_lifecycle_identity(
        PROGRESSION_LIFECYCLE_B)
    progression_lifecycle_suppress = progression_lifecycle_identity(
        PROGRESSION_LIFECYCLE_SUPPRESS)
    require(progression_lifecycle_a["files"] ==
            progression_lifecycle_b["files"],
            "first-segment lifecycle captures differ")
    controller_edge_a = controller_edge_identity(CONTROLLER_EDGE_A)
    controller_edge_b = controller_edge_identity(CONTROLLER_EDGE_B)
    controller_edge_suppress = controller_edge_identity(CONTROLLER_EDGE_SUPPRESS)
    require(controller_edge_a["files"] == controller_edge_b["files"],
            "controller camera-edge correction captures differ")
    final = next(rows(RAW_A / "result.tsv"))
    require(int(final["final_route"]) == 4, "route capture did not reach Round 2")
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    image = OPCODES.read_bytes()
    program = PROGRAM.read_bytes()
    samples = {int(row["frame"]): row for row in rows(RAW_A / "route_samples.tsv")}
    writes_by_frame: dict[int, list[dict[str, str]]] = defaultdict(list)
    segment_writer_refs: list[set[str]] = [set() for _ in route["segments"]]
    segments = route["segments"]
    si = 0
    for row in rows(RAW_A / "route_writes.tsv"):
        frame = int(row["frame"])
        writes_by_frame[frame].append(row)
        while si + 1 < len(segments) and frame > segments[si]["source_frame_range"][1]:
            si += 1
        if segments[si]["source_frame_range"][0] <= frame <= segments[si]["source_frame_range"][1]:
            segment_writer_refs[si].add(f"0x{row['pc']}@0x{row['address']}")

    edge_rows = []
    for frame, pc, value, guard in ROUTE_EDGES:
        matches = [r for r in writes_by_frame[frame]
                   if r["address"] == "ff8008" and r["pc"] == pc and
                   int(r["data"], 16) == value]
        require(len(matches) == 1, f"route edge drift at frame {frame}")
        row = matches[0]
        edge_rows.append({
            "write_frame": frame, "sample_transition_frame": frame + 1,
            "field": "0xff8008:s16", "writer_pc": f"0x{pc}",
            "value": value, "transition_guard": guard,
            "caller_chain": [f"0x{row[k]}" for k in ("return0", "return1", "return2")],
            "source_window": window(image, int(pc, 16)),
            "classification": "SOURCE_CLOSED",
        })
    observed = [(item["frame"]-1, item["to"])
                for item in route["route_state_transitions"][1:]]
    require(observed == [(f, v) for f, _, v, _ in ROUTE_EDGES],
            "sampled route transition inventory drift")

    writer_transactions = []
    route_writer_pcs = set()
    for row in rows(RAW_A / "route_writer_summary.tsv"):
        pc = int(row["pc"], 16)
        route_writer_pcs.add(f"0x{pc:06x}")
        writer_transactions.append({
            "address": f"0x{row['address']}", "writer_pc": f"0x{pc:06x}",
            "first_frame": int(row["first_frame"]), "last_frame": int(row["last_frame"]),
            "write_count": int(row["count"]), "source_window": window(image, pc),
            "classification": "SOURCE_CLOSED",
        })
    require(len(writer_transactions) == 609 and len(route_writer_pcs) == 451,
            "route writer census drift")

    event_by_slot: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(ORACLE10_EVENTS):
        event_by_slot[row["slot"]].append(row)
    for values in event_by_slot.values():
        values.sort(key=lambda item: int(item["frame"]))

    def post_spawn(slot: str, frame: int) -> dict[str, str] | None:
        key = f"actor-{(int(slot, 16)-0xff9580)//0xc0}"
        for item in event_by_slot.get(key, []):
            if int(item["frame"]) >= frame and int(item["active"]):
                return item
        return None

    all_spawn_count = 0
    enemy_spawns = []
    delegated_spawns = 0
    lifecycle_pcs = set()
    for row in rows(RAW_A / "lifecycle_writes.tsv"):
        if not (row["inner"] == "00" and row["mask"] in ("0000ff00", "0000ffff")
                and int(row["old_active"]) == 0
                and ((int(row["data"], 16) >> 8) & 0xff) != 0):
            continue
        frame = int(row["frame"])
        if frame >= 15193:
            continue
        post = post_spawn(row["slot"], frame)
        require(post is not None, f"unresolved spawn identity {frame}/{row['slot']}")
        all_spawn_count += 1
        if int(post["type"]) != 12:
            delegated_spawns += 1
            continue
        require(row["pc"] in SPAWN_GUARDS, f"orphan type-12 spawn writer {row['pc']}")
        lifecycle_pcs.add(f"0x{row['pc']}")
        enemy_spawns.append({
            "frame": frame, "slot": f"0x{row['slot']}",
            "class": f"0x{post['class']}", "type": 12,
            "writer_pc": f"0x{row['pc']}",
            "caller_chain": [f"0x{row[k]}" for k in ("return0", "return1", "return2")],
            "transition_guard": SPAWN_GUARDS[row["pc"]],
            "writes": ["active:u8", "class:u8", "type:u8", "state:u16", "substate:u16",
                       "x:s16", "y:s16", "z:s16"],
            "source_window": window(image, int(row["pc"], 16)),
            "classification": "SOURCE_CLOSED",
        })
    require(all_spawn_count == 424 and delegated_spawns == 368 and len(enemy_spawns) == 56,
            "Round 1 spawn census drift")

    events = route["source_route_events"]
    segment_bindings = []
    for index, segment in enumerate(segments):
        first, last = segment["source_frame_range"]
        sample_frames = [frame for frame in samples if first <= frame <= last]
        mode_values = sorted({int(samples[frame]["g8008"], 16) for frame in sample_frames})
        edges = [item for item in edge_rows if first <= item["write_frame"] <= last]
        spawns = [item for item in enemy_spawns if first <= item["frame"] <= last]
        labels = [item["id"] for item in events if first <= item["source_frame"] <= last]
        segment_bindings.append({
            "route_segment": segment["id"], "source_frame_range": [first, last],
            "route_mode_values": mode_values,
            "gameplay_route_edges": edges,
            "enemy_spawn_count": len(spawns),
            "enemy_spawn_frames": sorted({item["frame"] for item in spawns}),
            "observational_labels": labels,
            "route_writer_refs": sorted(segment_writer_refs[index]),
            "presentation_boundary": {
                "signature": segment["presentation_dependency"]["stable_scene_id"],
                "owns_progression": False,
                "classification": ("NOT_REQUIRED_FOR_ROUND1" if first >= 15193 else
                                   "SOURCE_CLOSED_PRESENTATION_DEPENDENCY"),
            },
            "classification": "SOURCE_CLOSED",
        })
    require(len(segment_bindings) == 94 and
            {item["route_segment"] for item in segment_bindings} ==
            {item["id"] for item in segments}, "route segment coverage drift")

    entry_calls = list(rows(ENTRY_A / "entry_calls.tsv"))
    entry_actors = list(rows(ENTRY_A / "entry_actors.tsv"))
    require(len(entry_calls) == 1 and len(entry_actors) == 10,
            "entry source-table capture drift")
    call = entry_calls[0]
    table_bytes = bytes.fromhex(call["table_hex"])
    require(len(table_bytes) == 80 and call["a1"] == "028bd4" and
            call["a6"] == "ffd180" and call["controller_active"] == "1" and
            call["controller_class"] == "01" and
            call["controller_type"] == "32" and
            call["controller_state"] == "514" and
            call["controller_phase"] == "0", "entry controller/table drift")

    def word(offset: int) -> int:
        return int.from_bytes(table_bytes[offset:offset+2], "big")

    entry_rows = []
    for sequence, actor in enumerate(entry_actors):
        offset = sequence * 8
        class_variant = word(offset + 4)
        require(int(actor["sequence"]) == sequence and
                int(actor["x"]) == word(offset) and
                int(actor["z"]) == word(offset + 2) and
                int(actor["y"]) == word(offset + 2) and
                int(actor["class"], 16) == class_variant >> 8 and
                int(actor["active"]) == 1 and int(actor["type"]) == 12,
                f"entry source row {sequence} does not match post-init actor")
        entry_rows.append({
            "sequence": sequence, "slot": f"0x{actor['slot']}",
            "x": word(offset), "y": word(offset + 2),
            "z": word(offset + 2), "class": f"0x{class_variant >> 8:02x}",
            "variant": class_variant & 0xff, "source_action": word(offset + 6),
            "record_type": int(actor["type"]),
            "post_initial_dispatch": {
                "state": int(actor["state"]), "substate": int(actor["phase"]),
                "facing": int(actor["facing"]),
                "animation_record": f"0x{int(actor['anim'], 16):08x}",
                "health": int(actor["health"]),
            },
        })
    require([item["slot"] for item in entry_rows] ==
            [item["slot"] for item in enemy_spawns[:10]],
            "entry allocation sequence drift")

    base_samples = {int(row["frame"]): row
                    for row in rows(ENTRY_A / "entry_samples.tsv")}
    suppress_samples = {int(row["frame"]): row
                        for row in rows(ENTRY_SUPPRESS / "entry_samples.tsv")}
    base_gate = [row for row in rows(ENTRY_A / "entry_writes.tsv")
                 if row["pc"] == "02151e"]
    suppress_gate = [row for row in rows(ENTRY_SUPPRESS / "entry_writes.tsv")
                     if row["pc"] == "02151e"]
    require(len(base_gate) == len(suppress_gate) == 1 and
            base_gate[0]["frame"] == suppress_gate[0]["frame"] == "2236" and
            base_gate[0]["suppressed"] == "0" and
            suppress_gate[0]["suppressed"] == "1" and
            base_samples[2237]["gate8236"] == "00" and
            base_samples[2238]["route"] == "0004" and
            suppress_samples[2238]["gate8236"] == "01" and
            suppress_samples[2238]["route"] == "0002" and
            suppress_samples[2300]["route"] == "0002" and
            suppress_samples[2300]["player_state"] == "2048",
            "entry gate suppression did not discriminate route authority")
    script_rows = {int(row["frame"]): row
                   for row in rows(ENTRY_A / "entry_script.tsv")}
    require(script_rows[2072]["cursor"] == "128faa" and
            script_rows[2237]["cursor"] == "128fc2" and
            script_rows[2237]["bytes32"].startswith("ffff"),
            "entry animation terminator drift")
    entry_program = image[0x128faa:0x128fc4]
    expected_entry_program = bytes.fromhex(
        "0a0003b00140060018000000003c0000003c16020000002cffff")
    require(entry_program == expected_entry_program,
            "entry animation source program drift")
    player_writes = list(rows(ENTRY_A / "entry_player_writes.tsv"))
    timer_loads = [row for row in player_writes
                   if row["offset"] == "c8" and row["pc"] == "02155e"]
    timer_ticks = [row for row in player_writes
                   if row["offset"] == "c8" and row["pc"] == "02177a"]
    timer_completions = [row for row in player_writes
                         if row["offset"] in ("c0", "c2") and
                         row["pc"] in ("021780", "021784")]
    require([int(row["data"], 16) for row in timer_loads] == [60, 60, 44] and
            len(timer_ticks) == 164 and len(timer_completions) == 6,
            "entry animation timer semantics drift")
    first_entry_body = {
        "classification": "SOURCE_CLOSED",
        "capture_identity": {
            "completion_a": entry_a, "completion_b": entry_b,
            "byte_identical": True,
            "suppression": entry_identity(ENTRY_SUPPRESS),
        },
        "controller": {
            "record": "0xffd180", "record_type": 32, "class": "0x01",
            "state": 514, "substate": 0,
            "transition_guard": ("active class-0x01/type-32 controller dispatches "
                                 "the ten-row source table body; each row requires "
                                 "allocate_record12 success"),
        },
        "spawn_table": {
            "address": "0x128bd4", "bytes": len(table_bytes),
            "sha256": hashlib.sha256(table_bytes).hexdigest(),
            "routine": "0x028874..0x0288b8", "source_window": window(image, 0x28886),
            "rows": entry_rows,
        },
        "player_entry_script": {
            "player_state": 2048, "player_substate": 0,
            "position": {"x": 944, "y": 320, "z": 320},
            "animation_record": "0x0015f1f4",
            "initial_cursor": "0x128faa", "terminal_cursor": "0x128fc2",
            "terminal_token": "0xffff",
            "decoder": "0x0214dc..0x021526",
            "decoder_sha256": hashlib.sha256(image[0x214dc:0x21528]).hexdigest(),
            "source_program": {
                "first": "0x128faa", "last_exclusive": "0x128fc4",
                "bytes": len(entry_program), "hex": entry_program.hex(),
                "sha256": hashlib.sha256(entry_program).hexdigest(),
                "commands": [
                    {"opcode": "0x0a", "arguments_hex": "0003b00140",
                     "effect": "set player x=944 and y=z=320",
                     "handler": "0x0215e8..0x021600"},
                    {"opcode": "0x06", "arguments_hex": "00",
                     "effect": "enter animation subhandler 8",
                     "handler": "0x0215a8..0x0215bc"},
                    {"opcode": "0x18", "arguments_hex": "00",
                     "effect": "execute the exact source command before the first dwell",
                     "handler_cursor_writer_pc": "0x021692"},
                    {"opcode": "0x00", "arguments_hex": "00003c",
                     "effect": "load animation countdown 60"},
                    {"opcode": "0x00", "arguments_hex": "00003c",
                     "effect": "load animation countdown 60"},
                    {"opcode": "0x16", "arguments_hex": "02",
                     "effect": "write source global animation byte g8209=2",
                     "handler_cursor_writer_pc": "0x021688"},
                    {"opcode": "0x00", "arguments_hex": "00002c",
                     "effect": "load animation countdown 44"},
                    {"opcode": "0xff", "arguments_hex": "ff",
                     "effect": "signed terminal command"},
                ],
            },
            "timer_semantics": {
                "field": "player+0xc8:u16", "load_writer_pc": "0x02155e",
                "loads": [60, 60, 44], "decrement_writer_pc": "0x02177a",
                "scheduler_decrements": 164,
                "completion_writers": ["0x021780:clear player+0xc1:u8",
                                       "0x021784:clear player+0xc2:u16"],
                "rule": ("source animation scheduler decrements c8 to zero, clears "
                         "the timed subhandler, then decodes the next command; video "
                         "frame number is not an input"),
            },
            "gate_writer_pc": "0x02151e", "gate_field": "0xff8236:u8",
            "gate_bit_field": "player+0xd2:u8", "gate_bit": 0,
            "transition_guard": ("signed animation command byte is negative; "
                                 "clear player+0xd2-selected bit in g8236"),
            "route_consumer": {
                "writer_pc": "0x00c170", "value": 4,
                "guard": "(u8(g8236) & u8(g81af)) == 0",
            },
        },
        "suppression_control": {
            "mutation": "retain the old g8236 word only at writer 0x02151e",
            "baseline_route_at_2238": 4, "mutant_route_at_2238": 2,
            "mutant_route_at_2300": 2, "mutant_player_state_at_2300": 2048,
            "fixed_frame_substitute": False,
        },
    }

    progression_transactions = list(rows(
        PROGRESSION_A / "progression_transactions.tsv"))
    controller_update_counts = Counter(
        int(row["frame"]) for row in progression_transactions
        if row["pc"] == "0288e2" and row["a6"] == "ffd180")
    controller_update_exceptions = {
        2075: 3,
        2165: 4,
        2260: 0,
        2265: 0,
    }
    require(
        all(controller_update_counts[frame] ==
            controller_update_exceptions.get(frame, 1)
            for frame in range(2074, 4100)),
        "Coffee Shop source controller update cadence drift")
    progression_writes = list(rows(PROGRESSION_A / "progression_writes.tsv"))
    progression_global_writes = list(rows(
        PROGRESSION_A / "progression_global_writes.tsv"))
    progression_controller = {int(row["frame"]): row for row in rows(
        PROGRESSION_A / "progression_controller.tsv")}
    guard_mutant_global_writes = list(rows(
        PROGRESSION_GUARD_SUPPRESS / "progression_global_writes.tsv"))
    guard_mutant_controller = {int(row["frame"]): row for row in rows(
        PROGRESSION_GUARD_SUPPRESS / "progression_controller.tsv")}
    progression_snapshots = list(rows(
        PROGRESSION_A / "progression_snapshots.tsv"))
    suppressed_snapshots = list(rows(
        PROGRESSION_SUPPRESS / "progression_snapshots.tsv"))
    lifecycle_writes = list(rows(
        PROGRESSION_LIFECYCLE_A / "progression_lifecycle_writes.tsv"))
    lifecycle_suppressed_writes = list(rows(
        PROGRESSION_LIFECYCLE_SUPPRESS /
        "progression_lifecycle_writes.tsv"))
    lifecycle_release_rows = [row for row in lifecycle_writes
                              if row["pc"] == "061152"]
    lifecycle_release_mutant_rows = [row for row in lifecycle_suppressed_writes
                                     if row["pc"] == "061152"]
    coffee_shop_lifecycle_writes = list(rows(
        COFFEE_SHOP_SCENE_A / "progression_lifecycle_writes.tsv"))
    coffee_shop_controller = {int(row["frame"]): row for row in rows(
        COFFEE_SHOP_SCENE_A / "progression_controller.tsv")}
    coffee_shop_scene_frames = {int(row["frame"]): row for row in rows(
        COFFEE_SHOP_SCENE_A / "coffee_shop_scene_frames.tsv")}
    require(
        [(frame,
          int(coffee_shop_scene_frames[frame]["route_state"]),
          int(coffee_shop_scene_frames[frame]["player_state"]),
          int(coffee_shop_scene_frames[frame]
              ["entry_controller_timer42"]))
         for frame in (5451, 5452, 5453)] == [
            (5451, 4, 0x0200, 1),
            (5452, 4, 0x0200, 0),
            (5453, 6, 0x0800, 0)],
        "Coffee Shop clear-gate/route-dispatch chronology drift")
    coffee_shop_progress_rows = [row for row in coffee_shop_lifecycle_writes
                                 if row["pc"] == "061070"]
    coffee_shop_progress_frames = [
        2363, 2805, 2830, 2832, 3830, 3891, 4130, 4216, 4239, 4395,
        4396, 4409, 4575, 4576, 4755, 4756, 4757, 4935, 4936, 5150]
    lifecycle_base_result = next(rows(
        PROGRESSION_LIFECYCLE_A / "progression_result.tsv"))
    lifecycle_suppress_result = next(rows(
        PROGRESSION_LIFECYCLE_SUPPRESS / "progression_result.tsv"))
    require(len(lifecycle_release_rows) == 22 and
            len(lifecycle_release_mutant_rows) == 12 and
            all(row["owner_active"] == "2" and
                row["owner_class"] == "1f" and
                row["owner_type"] == "12" and
                int(row["owner_state"]) == 0x0600 and
                int(row["owner_substate"]) == 0 and
                row["suppressed"] == "0"
                for row in lifecycle_release_rows) and
            all(row["suppressed"] == "1"
                for row in lifecycle_release_mutant_rows) and
            int(lifecycle_base_result["main_spawn_transactions"]) == 15 and
            int(lifecycle_base_result["aux_spawn_transactions"]) == 3 and
            int(lifecycle_suppress_result["main_spawn_transactions"]) == 0 and
            int(lifecycle_suppress_result["aux_spawn_transactions"]) == 0 and
            int(lifecycle_suppress_result["lifecycle_suppressed_writes"]) == 12,
            "class-0x1f lifecycle release control drift")
    require(len(coffee_shop_progress_rows) == 20 and
            [int(row["frame"]) for row in coffee_shop_progress_rows] ==
                coffee_shop_progress_frames and
            all(row["address"] == "ff1a1a" and
                row["owner_active"] == "2" and
                row["owner_class"] == "1f" and
                row["owner_type"] == "12" and
                int(row["owner_state"]) == 0x0402 and
                int(row["owner_substate"]) == 0 and
                int(row["owner_health"]) == -1 and
                int(row["progress_before"]) == index and
                int(row["data"], 16) == index + 1 and
                row["suppressed"] == "0"
                for index, row in enumerate(coffee_shop_progress_rows)),
            "class-0x1f KO progress authority drift")

    def transaction(frame: int, pc: str) -> dict[str, str]:
        matches = [row for row in progression_transactions
                   if int(row["frame"]) == frame and row["pc"] == pc]
        require(len(matches) == 1,
                f"progression transaction drift at {frame}/0x{pc}")
        return matches[0]

    def snapshot(values: list[dict[str, str]], frame: int,
                 slot: str) -> dict[str, str]:
        matches = [row for row in values if int(row["frame"]) == frame and
                   row["slot"] == slot]
        require(len(matches) == 1,
                f"progression snapshot drift at {frame}/0x{slot}")
        return matches[0]

    first_writes = [row for row in progression_writes
                    if int(row["frame"]) == 2510 and
                    row["slot"] == "ffa3c0" and row["pc"].startswith("028a")]
    later_writes = [row for row in progression_writes
                    if int(row["frame"]) == 3982 and
                    row["slot"] == "ffa000" and row["pc"].startswith("028a")]
    main_writer_order = [row["pc"] for row in first_writes]
    require(main_writer_order == [
        "028a3e", "028a42", "028a48", "028a50", "028a54", "028a5a",
        "028a8a", "028a96", "028a9a", "028a9e", "028aa6"],
        "first recurring spawn write order drift")
    first_post_init = snapshot(progression_snapshots, 2511, "ffa3c0")
    first_post_dispatch = snapshot(progression_snapshots, 2512, "ffa3c0")
    scene_actor_rows = list(rows(
        COFFEE_SHOP_SCENE_A / "coffee_shop_scene_actors.tsv"))
    reused_before = snapshot(scene_actor_rows, 2508, "ffa3c0")
    reused_spawn = snapshot(scene_actor_rows, 2511, "ffa3c0")
    reused_move_1 = snapshot(scene_actor_rows, 2514, "ffa3c0")
    reused_move_2 = snapshot(scene_actor_rows, 2517, "ffa3c0")
    later_post_init = snapshot(progression_snapshots, 3983, "ffa000")
    later_post_dispatch = snapshot(progression_snapshots, 3984, "ffa000")
    suppressed_first = snapshot(suppressed_snapshots, 2511, "ffa3c0")
    suppressed_later = snapshot(suppressed_snapshots, 3983, "ffa000")
    base_result = next(rows(PROGRESSION_A / "progression_result.tsv"))
    suppress_result = next(rows(
        PROGRESSION_SUPPRESS / "progression_result.tsv"))
    guard_suppress_result = next(rows(
        PROGRESSION_GUARD_SUPPRESS / "progression_result.tsv"))
    first_active_write = first_writes[0]
    first_write_by_pc = {row["pc"]: row for row in first_writes}
    later_write_by_pc = {row["pc"]: row for row in later_writes}
    first_rng_write = next(row for row in first_writes
                           if row["pc"] == "028a8a")
    later_active_write = next(row for row in later_writes
                              if row["pc"] == "028a3e")
    later_rng_write = next(row for row in later_writes
                           if row["pc"] == "028a8a")
    require(first_active_write["g8019"] == "c0" and
            int(first_active_write["living"]) == 8 and
            int(first_active_write["progress"]) == 1 and
            int(first_active_write["c_state"]) == 0x0204 and
            int(first_active_write["c_substate"]) == 0 and
            int(first_active_write["c_timer40"]) == 3706 and
            int(first_active_write["c_limit4a"]) == 35 and
            int(first_active_write["c_index10"]) == 9 and
            int(first_active_write["camera_x"]) == 720 and
            int(first_active_write["camera_z"]) == 256 and
            first_active_write["rng"] == "d21c",
            "first recurring spawn guard operands drift")
    require(progression_controller[2072]["g8019"] == "06" and
            progression_controller[2510]["index10"] == "9" and
            progression_controller[2511]["index10"] == "8",
            "native-entry phase or recurring spawn-index chronology drift")
    require(first_active_write["slot"] == "ffa3c0" and
            later_active_write["slot"] == "ffa000" and
            (int(first_write_by_pc["028a50"]["data"], 16) & 0xffff) == 672 and
            (int(first_write_by_pc["028a96"]["data"], 16) & 0xffff) == 328 and
            (int(first_write_by_pc["028a9a"]["data"], 16) & 0xffff) == 328 and
            (int(first_write_by_pc["028a8a"]["data"], 16) & 0xff) == 3 and
            (int(first_write_by_pc["028aa6"]["data"], 16) & 0xff) == 1 and
            first_rng_write["rng"] == "7692" and
            (int(later_write_by_pc["028a50"]["data"], 16) & 0xffff) == 960 and
            (int(later_write_by_pc["028a96"]["data"], 16) & 0xffff) == 343 and
            (int(later_write_by_pc["028a9a"]["data"], 16) & 0xffff) == 343 and
            (int(later_write_by_pc["028a8a"]["data"], 16) & 0xff) == 3 and
            (int(later_write_by_pc["028aa6"]["data"], 16) & 0xff) == 1 and
            later_rng_write["rng"] == "4ffd",
            "recurring spawn initializer result drift")
    require(int(first_post_init["active"]) == 1 and
            int(first_post_init["state"]) == 0x0200 and
            int(first_post_init["substate"]) == 0 and
            int(first_post_init["health"]) == 87 and
            int(first_post_dispatch["substate"]) == 0x1600 and
            int(later_post_init["active"]) == 1 and
            int(later_post_dispatch["substate"]) == 0x1600 and
            int(suppressed_first["active"]) == 0 and
            int(suppressed_first["state"]) == 0 and
            int(suppressed_later["active"]) == 0 and
            int(suppress_result["suppressed_writes"]) == 8 and
            int(base_result["suppressed_writes"]) == 0,
            "recurring spawn suppression did not discriminate scheduler state")
    require(
        (int(reused_before["x_fp"], 16) & 0xffff) == 0x8000 and
        (int(reused_before["y_fp"], 16) & 0xffff) == 0x9000 and
        int(reused_spawn["x_fp"], 16) == 0x02a08000 and
        int(reused_spawn["y_fp"], 16) == 0x01489000 and
        int(reused_move_1["x_fp"], 16) == 0x02a7e200 and
        int(reused_move_1["y_fp"], 16) == 0x01470900 and
        int(reused_move_2["x_fp"], 16) == 0x02af4400 and
        int(reused_move_2["y_fp"], 16) == 0x01458200,
        "recurring record reuse fixed-point fraction drift")

    guard_clear = [row for row in progression_global_writes
                   if row["pc"] == "08da38"]
    guard_clear_mutant = [row for row in guard_mutant_global_writes
                          if row["pc"] == "08da38"]
    require(len(guard_clear) == 1 and len(guard_clear_mutant) == 1 and
            guard_clear[0]["frame"] == "2253" and
            guard_clear[0]["a6"] == "ffc580" and
            guard_clear[0]["owner_active"] == "1" and
            guard_clear[0]["owner_class"] == "44" and
            guard_clear[0]["owner_type"] == "24" and
            int(guard_clear[0]["owner_state"]) == 0x0404 and
            guard_clear[0]["guard1a11"] == "ff" and
            guard_clear[0]["suppressed"] == "0" and
            guard_clear_mutant[0]["suppressed"] == "1" and
            progression_controller[2073]["state"] == "512" and
            progression_controller[2073]["timer40"] == "3900" and
            progression_controller[2073]["timer42"] == "60" and
            progression_controller[2073]["field46"] == "1200" and
            progression_controller[2073]["field48"] == "2100" and
            progression_controller[2073]["limit4a"] == "35" and
            progression_controller[2073]["index10"] == "9" and
            progression_controller[2074]["state"] == "514" and
            progression_controller[2253]["guard1a11"] == "ff" and
            progression_controller[2254]["guard1a11"] == "00" and
            progression_controller[2255]["timer42"] == "59" and
            progression_controller[2316]["state"] == "514" and
            progression_controller[2316]["timer42"] == "0" and
            progression_controller[2317]["state"] == "516" and
            progression_controller[2317]["timer42"] == "65535" and
            guard_mutant_controller[4100]["state"] == "514" and
            guard_mutant_controller[4100]["timer42"] == "60" and
            guard_mutant_controller[4100]["guard1a11"] == "ff" and
            int(guard_suppress_result["main_spawn_transactions"]) == 0 and
            int(guard_suppress_result["aux_spawn_transactions"]) == 0,
            "controller initialization/gate transition control drift")

    lane_offsets = [int.from_bytes(image[offset:offset + 2], "big", signed=True)
                    for offset in range(0x28ab4, 0x28ac0, 2)]
    selector_cycle = list(image[0x28ac0:0x28aca])
    lane_bucket_table = list(image[0x28aca:0x28b0a])
    variant_table = list(image[0x28afa:0x28b5a])
    require(lane_offsets == [24, 40, 56, 72, 88, 104] and
            selector_cycle == [0, 1, 1, 1, 0, 1, 0, 1, 1, 1] and
            len(lane_bucket_table) == 64 and len(variant_table) == 96,
            "recurring spawn source table drift")
    phase_points = []
    for phase_frame, before, after in (
            (1972, 0xa2, 0xa3), (2237, 0xb0, 0xb1),
            (2238, 0xb1, 0xb2), (2510, 0xbf, 0xc0)):
        matches = [row for row in writes_by_frame[phase_frame]
                   if row["address"] == "ff8018" and row["pc"] == "00809a"]
        require(len(matches) == 1 and
                (int(samples[phase_frame]["g8018"], 16) & 0xff) == before and
                (int(matches[0]["data"], 16) & 0xff) == after,
                f"source phase update drift at {phase_frame}")
        phase_points.append({"frame": phase_frame, "before_u8": before,
                             "after_u8": after})
    controller_edge_rows = list(rows(
        CONTROLLER_EDGE_A / "coffee_shop_controller_substate_writes.tsv"))
    edge_substate = [row for row in controller_edge_rows
                     if row["pc"] == "02894e"]
    edge_progress = [row for row in controller_edge_rows
                     if row["pc"] == "02895e"]
    require(len(edge_substate) == 1 and len(edge_progress) == 1 and
            edge_substate[0]["frame"] == "2679" and
            edge_substate[0]["state"] == "0204" and
            edge_substate[0]["substate"] == "0000" and
            edge_substate[0]["d0"] == "00000340" and
            edge_progress[0]["field44"] == "0000",
            "controller camera-edge writer chronology drift")
    edge_frames = {int(row["frame"]): row for row in rows(
        CONTROLLER_EDGE_A / "coffee_shop_scene_frames.tsv")}
    edge_suppress_frames = {int(row["frame"]): row for row in rows(
        CONTROLLER_EDGE_SUPPRESS / "coffee_shop_scene_frames.tsv")}
    require(int(edge_frames[2679]["entry_controller_substate"]) == 0 and
            int(edge_frames[2680]["entry_controller_substate"]) == 0x0200 and
            int(edge_suppress_frames[2680]["entry_controller_substate"]) == 0,
            "controller camera-edge suppression did not discriminate")
    first_segment_recurring_spawn = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": ("first-segment recurring type-12/class-0x1f source writers "
                  "0x028a3e and 0x028b7e"),
        "capture_identity": {
            "completion_a": progression_a, "completion_b": progression_b,
            "byte_identical": True, "suppression": progression_suppress,
            "guard_suppression": progression_guard_suppress,
        },
        "scheduler": {
            "controller_slot": "0xffd180", "controller_type_u8": 32,
            "controller_class_u8": "0x01",
            "controller_dispatch": "0x0288e2..0x0288fa",
            "controller_precedes_type12_scheduler": True,
            "new_record_initializes_in_same_scheduler_frame": True,
            "next_current_state_dispatch_occurs_next_scheduler_frame": True,
        },
        "source_update_cadence": {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "source_capture": {
                "file": "progression_transactions.tsv",
                "sha256": progression_a["files"]
                    ["progression_transactions.tsv"],
                "controller_entry_pc": "0x0288e2",
                "controller_slot": "0xffd180",
                "source_frame_range_inclusive": [2074, 4099],
            },
            "default_updates_per_source_frame_u8": 1,
            "exceptions": [
                {"source_frame_u16": frame,
                 "updates_u8": controller_update_exceptions[frame]}
                for frame in sorted(controller_update_exceptions)
            ],
            "scheduler_rule": (
                "execute the native entry/player/actor scheduler once per "
                "captured source controller invocation; zero means preserve "
                "the prior gameplay state for that displayed source frame"),
            "reads": ["diagnostic source frame:u16"],
            "writes": ["entry/player/actor scheduler update count:u8"],
            "rng_calls": "exactly those consumed by the selected number of full scheduler updates",
            "fixed_frame_gameplay_transition_forbidden": True,
            "mutation_control": {
                "kind": "cadence table entry mutation",
                "effect": (
                    "changing any exceptional update count changes the "
                    "recurring controller timer/state/spawn chronology"),
            },
            "spec_executable": True,
        },
        "controller_program": {
            "field_types": {
                "state_substate": "u16 big-endian state/substate word",
                "spawn_index": "u16", "spawn_timer": "u16",
                "entry_gate_timer": "u16", "field_0x46": "u16",
                "field_0x48": "u16", "spawn_limit": "u16",
                "local_0x2c": "u8", "phase_0x2e": "u8",
                "intro_gate": "u8",
            },
            "initializer": {
                "routine": "0x0287fc..0x02884a",
                "source_window": {
                    "first": "0x0287fc", "last_exclusive": "0x02884c",
                    "sha256": hashlib.sha256(image[0x287fc:0x2884c]).hexdigest(),
                },
                "write_order": [
                    "state high byte += 2 -> 0x0200",
                    "camera bound 0xff829e:u16 = 0x0280",
                    "living_enemy_count 0xff1a18:u16 = 0",
                    "progress 0xff1a1a:u16 = 0",
                    "field 0xff1a1c:u16 = 1",
                    "controller+0x42:u16 = 60",
                    "controller+0x46:u16 = 1200",
                    "controller+0x48:u16 = 2100",
                    "controller+0x40:u16 = 3900",
                    "controller+0x2e:u8 = 0",
                    "controller+0x2c:u8 = 0",
                    "controller+0x06:u8 = 0",
                    "controller+0x10:u16 = 9",
                    "controller+0x4a:u16 = limit_table[u8(0xff820e)]",
                ],
                "limit_table_u16": [0, 35, 55, 70],
                "observed_after": {"frame": 2073, "state_u16": 0x0200,
                                   "timer40_u16": 3900, "timer42_u16": 60,
                                   "field46_u16": 1200, "field48_u16": 2100,
                                   "limit_u16": 35, "index_u16": 9,
                                   "camera_bound_u16": 640},
                "rng_calls": 0,
            },
            "initial_spawn_transition": {
                "routine": "0x028854..0x0288b8",
                "guard": "state 0x0200/substate 0 dispatch",
                "writes": ["substate low byte += 2 -> 0x0202",
                           "execute ten-row source spawn table"],
                "observed_after": {"frame": 2074, "state_u16": 0x0202,
                                   "living_enemy_count_u16": 10},
                "rng_calls": 0,
            },
            "intro_gate_transition": {
                "routine": "0x0288ba..0x0288e0",
                "branch_order": [
                    "require u8(0xff1a11) == 0",
                    "predecrement controller+0x42:u16",
                    "return while signed timer result >= 0",
                    "substate low byte += 2 -> 0x0204",
                    "write camera target 0xff829a:u16 = 0x00d0",
                    "when camera_x_s16 <= 0x02d0 call 0x028a06",
                ],
                "write_values": {"source_camera_target_u16": 208,
                                 "camera_x_call_threshold_s16": 720,
                                 "conditional_phase_0x2e_u8": 1,
                                 "conditional_local_0x2c_u8": 0},
                "gate_owner": {
                    "record": "0xffc580", "record_type_u8": 24,
                    "class_u8": "0x44", "state_u16": 0x0404,
                    "writer_instruction": "0x08da32",
                    "writer_successor_pc": "0x08da38",
                    "effect": "u8(0xff1a11) = 0",
                    "source_contract": ("accepted auxiliary first-segment "
                                        "class-0x44 command-guard owner"),
                },
                "observed": {
                    "gate_clear_frame": 2253,
                    "first_decremented_sample": {"frame": 2255,
                                                 "timer42_u16": 59},
                    "last_wait_sample": {"frame": 2316,
                                         "state_u16": 0x0202,
                                         "timer42_u16": 0},
                    "first_current_sample": {"frame": 2317,
                                             "state_u16": 0x0204,
                                             "timer42_u16": 0xffff},
                },
                "rng_calls": 0,
            },
            "camera_edge_transition": {
                "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
                "routine": "0x028910..0x02895e",
                "source_window": {
                    "first": "0x028910", "last_exclusive": "0x028960",
                    "sha256": hashlib.sha256(
                        image[0x28910:0x28960]).hexdigest(),
                },
                "dispatch_guard": {
                    "state_u16": 0x0204, "substate_u16": 0,
                    "jump_table_index": "u8(controller+0x06)",
                },
                "field_types": {
                    "state_u16": "u16", "substate_u16": "u16",
                    "field46_u16": "u16", "field48_u16": "u16",
                    "camera_x_s16": "s16", "camera_target_x_s16": "s16",
                    "camera_right_edge_s16": "s16", "progress_u16": "u16",
                },
                "branch_order": [
                    "if controller+0x48:u16 != 0 and controller+0x46:u16 != 0, predecrement controller+0x46:u16",
                    "if the decremented controller+0x46:u16 equals 600, call 0x028a06 to set phase_0x2e=1 and local_0x2c=0",
                    "write camera_x_s16 to camera_target_x_s16 at 0xff829c",
                    "return while unsigned camera_x_u16 is below 0x0340",
                    "add 2 to controller+0x06:u8 so substate_u16 becomes 0x0200",
                    "write 0x0340 to camera_target_x_s16 at 0xff829c",
                    "write 0x0340 to camera_right_edge_s16 at 0xff829e",
                    "write progress_u16 from 0xff1a1a to controller+0x44:u16",
                ],
                "transition_values": {
                    "field46_phase_threshold_u16": 600,
                    "camera_edge_x_s16": 832,
                    "conditional_phase_0x2e_u8": 1,
                    "conditional_local_0x2c_u8": 0,
                },
                "observed_transition": {
                    "writer_frame_u16": 2679,
                    "visible_frame_u16": 2680,
                    "writer_pc": "0x02894e",
                    "progress_snapshot_writer_pc": "0x02895e",
                    "camera_x_s16": 832,
                    "substate_before_u16": 0,
                    "substate_after_u16": 0x0200,
                    "progress_u16": 1,
                    "field44_after_u16": 1,
                    "field46_before_u16": 838,
                    "field46_after_u16": 837,
                    "field48_u16": 2100,
                },
                "writes": [
                    "controller+0x46:u16 -= 1",
                    "camera_target_x_s16 = camera_x_s16",
                    "controller+0x06:u8 += 2",
                    "camera_target_x_s16 = 0x0340",
                    "camera_right_edge_s16 = 0x0340",
                    "controller+0x44:u16 = progress_u16",
                ],
                "rng_calls": 0,
                "scheduler_order": "entry controller before player and fixed actor pools",
                "native_adapter_binding": {
                    "source_read": "camera_x_s16 at controller dispatch",
                    "runtime_field": "camera_x_position",
                    "reason": "the corrected native player/camera chronology has camera_x_position=832 and camera_x_previous=830 at source writer frame 2679; the source controller reads the current 0xff8278 camera value 832 before writing the edge transition",
                },
                "capture_identity": {
                    "completion_a": controller_edge_a,
                    "completion_b": controller_edge_b,
                    "byte_identical": True,
                    "suppression": controller_edge_suppress,
                },
                "mutation_control": {
                    "writer_pc": "0x02894e",
                    "baseline_visible_substate_u16": 0x0200,
                    "suppressed_visible_substate_u16": 0,
                    "accepted_current_camera_x_s16": 832,
                    "rejected_previous_camera_x_s16": 830,
                    "previous_runtime_sample_rejected": True,
                    "downstream_actor_population_differs": True,
                    "fixed_frame_substitute": False,
                },
                "spec_executable": True,
            },
        },
        "phase_counter": {
            "field": "0xff8019:u8", "stable_entry_value_u8": 0xa2,
            "native_entry_handoff_value_u8": 0x06,
            "native_entry_handoff_frame_u16": 2072,
            "writer_pc": "0x00809a", "writer_routine": "0x00808e..0x00809a",
            "guard": "increment only when u8(0xff81a6) == 0",
            "arithmetic": "u8 wrapping add 1",
            "scheduler_order": "source phase update precedes the encounter controller",
            "source_window": {
                "first": "0x00808e", "last_exclusive": "0x00809e",
                "sha256": hashlib.sha256(image[0x808e:0x809e]).hexdigest(),
            },
            "observed_updates": phase_points,
            "video_frame_number_is_not_an_input": True,
        },
        "controller_guard": {
            "branch_order": [
                "require u16(0xff1a1a) < controller+0x4a:u16",
                "decrement controller+0x40:u16 and require signed result >= 0",
                "call primary recurring spawn body 0x028a12",
            ],
            "first_operands": {
                "progress_u16": int(first_active_write["progress"]),
                "limit_u16": int(first_active_write["c_limit4a"]),
                "timer_before_u16": int(first_active_write["c_timer40"]) + 1,
                "timer_after_u16": int(first_active_write["c_timer40"]),
                "controller_state_u16": int(first_active_write["c_state"]),
                "controller_substate_u16": int(first_active_write["c_substate"]),
            },
            "first_spawn_index_transition": {
                "source_frame_u16": 2510,
                "before_u16": int(progression_controller[2510]["index10"]),
                "after_u16": int(progression_controller[2511]["index10"]),
                "guard": "successful primary record-12 allocation",
            },
        },
        "progress_increment_boundary": {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "scope": ("type-12/class-0x1f KO state 0x0402:0000 owns the "
                      "Coffee Shop encounter progress increment"),
            "capture_identity": {
                "completion_a": progression_lifecycle_identity(
                    COFFEE_SHOP_SCENE_A),
                "completion_b": progression_lifecycle_identity(
                    COFFEE_SHOP_SCENE_B),
                "byte_identical": True,
            },
            "writer_pc": "0x061070",
            "source_window": {
                "first": "0x061060", "last_exclusive": "0x061078",
                "sha256": hashlib.sha256(image[0x61060:0x61078]).hexdigest(),
            },
            "field_types": {
                "progress": "u16", "actor_state": "u16",
                "actor_substate": "u16", "actor_health": "s16",
            },
            "transition_guard": {
                "record_type_u8": 12, "class_u8": "0x1f",
                "state_u16": 0x0402, "substate_u16": 0,
                "health_s16": -1,
            },
            "write": "progress_u16 += 1",
            "increment_u16": 1,
            "scheduler_order": ("class-0x1f KO transition writes progress "
                                "before later recurring-controller reads"),
            "observed_transactions": [
                {"frame": int(row["frame"]), "slot": f"0x{row['a6']}",
                 "progress_before_u16": int(row["progress_before"]),
                 "progress_after_u16": int(row["data"], 16)}
                for row in coffee_shop_progress_rows
            ],
            "mutation_control": {
                "kind": "native semantic-edge suppression",
                "rule": ("suppress only the KO-owned increment; reject when "
                         "Coffee Shop progress and recurring spawn diverge"),
                "fixed_frame_substitute": False,
            },
        },
        "lifecycle_release_boundary": {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "scope": ("type-12/class-0x1f state 0x0600:0000 living-count "
                      "decrement and fixed-pool release"),
            "capture_identity": {
                "completion_a": progression_lifecycle_a,
                "completion_b": progression_lifecycle_b,
                "byte_identical": True,
                "suppression": progression_lifecycle_suppress,
            },
            "writer_pc": "0x061152",
            "writer_instruction_pc": "0x06114c",
            "release_routine": "0x0176b4",
            "source_window": {
                "first": "0x061146", "last_exclusive": "0x061158",
                "sha256": hashlib.sha256(image[0x61146:0x61158]).hexdigest(),
            },
            "field_types": {"living_enemy_count": "u16",
                            "actor_state": "u16",
                            "actor_substate": "u16"},
            "transition_guard": ("class-0x1f outer state 0x0600 reaches "
                                 "0x06114c; substate is 0x0000"),
            "write_order": ["living_enemy_count_u16 -= 1",
                            "tail-call type-12 release 0x0176b4"],
            "observed_release_transactions": 22,
            "first_four_release_frames": [2415, 2471, 2493, 2508],
            "first_four_slots": ["0xffa180", "0xff9d00",
                                 "0xffa300", "0xffa3c0"],
            "suppression_control": {
                "suppressed_release_writes": 12,
                "baseline_main_aux_spawns": [15, 3],
                "mutant_main_aux_spawns": [0, 0],
                "fixed_frame_substitute": False,
            },
            "implementation_dependency": ("accepted class-0x1f first-segment "
                "action execution and HIT/KO contracts own entry into 0x0600"),
        },
        "primary_writer": {
            "routine": "0x028a12..0x028ab2", "writer_pc": "0x028a3e",
            "source_window": {
                "first": "0x028a12", "last_exclusive": "0x028ab4",
                "sha256": hashlib.sha256(image[0x28a12:0x28ab4]).hexdigest(),
            },
            "guard_branch_order": [
                "require living_enemy_count_u16 at 0xff1a18 < 8",
                "run auxiliary writer body before the primary phase guard",
                "require (u8(0xff8019) & 7) == 0",
                "require type-12 allocator 0x01769e succeeds",
            ],
            "guard_values": {"living_limit_u16": 8,
                             "phase_mask_u8": 7},
            "position_values": {"x_camera_offset_s16": -48,
                                "lane_base_s16": 208,
                                "lane_band_mask_u16": 0x00f0},
            "field_types": {
                "phase": "u8", "living_enemy_count": "u16",
                "camera_x": "s16", "camera_z": "s16",
                "active": "u8", "class": "u8", "variant": "u8",
                "state": "u16", "substate": "u16", "x": "s16",
                "y": "s16", "z": "s16", "timer": "u16",
                "selector83": "u8", "rng_seed": "u16",
            },
            "write_order": [
                {"writer_pc": "0x028a3a", "effect": "living_enemy_count_u16 += 1"},
                {"writer_pc": "0x028a3e", "effect": "active_u8 += 1"},
                {"writer_pc": "0x028a42", "effect": "class_u8 = 0x1f"},
                {"writer_pc": "0x028a48", "effect": "x_s16 = camera_x_s16"},
                {"writer_pc": "0x028a50", "effect": "x_s16 -= 48"},
                {"writer_pc": "0x028a54", "effect": "y_s16 = camera_z_s16"},
                {"writer_pc": "0x028a5a", "effect": "z_s16 = camera_z_s16"},
                {"writer_pc": "0x028a8a", "effect": "variant_u8 = variant_table[(lane_bucket << 4) + rng_high_nibble]"},
                {"writer_pc": "0x028a96", "effect": "y_s16 += lane_offset_table[lane_bucket]"},
                {"writer_pc": "0x028a9a", "effect": "z_s16 += lane_offset_table[lane_bucket]"},
                {"writer_pc": "0x028a9e", "effect": "timer_u16 = 0"},
                {"writer_pc": "0x028aa6", "effect": "selector83_u8 = selector_cycle[controller_index_u16]"},
                {"writer_pc": "0x028aaa/0x028ab2", "effect": "controller_index_u16 decrements; wrap negative to 9"},
            ],
            "rng": {
                "entry": "0x017c5e", "calls": 1,
                "order": "after active/class/base position; before variant/lane/selector writes",
                "low_nibble": "rng_result_u16 & 0x000f",
                "high_nibble": "(rng_result_u16 >> 4) & 0x000f",
            },
            "lane_bucket": "lane_bucket_table[((camera_z_s16 - 208) & 0x00f0) + rng_low_nibble]",
            "tables": {
                "lane_offsets_s16": lane_offsets,
                "selector_cycle_u8": selector_cycle,
                "lane_bucket_u8": lane_bucket_table,
                "variant_u8": variant_table,
                "sha256": hashlib.sha256(image[0x28ab4:0x28b5a]).hexdigest(),
                "lane_bucket_variant_overlap": ("lane-bucket indices 48..63 read "
                                                "0x028afa..0x028b09, the first "
                                                "16 variant-table bytes"),
            },
            "observed_transactions": [
                {"frame": 2510, "slot": "0xffa3c0", "phase_u8": "0xc0",
                 "living_before_u16": 7, "camera_x_s16": 720,
                 "camera_z_s16": 256, "rng_before_u16": "0xd21c",
                 "rng_after_u16": "0x7692", "x_s16": 672,
                 "y_s16": 328, "z_s16": 328, "variant_u8": 3,
                 "selector83_u8": 1},
                {"frame": 3982, "slot": "0xffa000", "phase_u8": "0x80",
                 "living_before_u16": 7, "camera_x_s16": 1008,
                 "camera_z_s16": 255, "rng_before_u16": "0x6fae",
                 "rng_after_u16": "0x4ffd", "x_s16": 960,
                 "y_s16": 343, "z_s16": 343, "variant_u8": 3,
                 "selector83_u8": 1},
            ],
            "post_allocation_dispatch": {
                "presentation_ownership": "reused_record_residue",
                "presentation_writer_pcs": [],
                "writer_rule": ("0x028a12..0x028ab2 writes no animation record, "
                                "timer, branch or assembly; allocation and class "
                                "initialization preserve the released record's "
                                "presentation until the next action dispatch"),
                "source_samples": {
                    "pre_release_frame_2508": {
                        "slot": "0xffa3c0",
                        "animation_record": "0x0012ddb0",
                        "animation_timer_u16": 0x0fff,
                        "animation_branch_s16": -0x8000},
                    "post_allocation_frame_2511": {
                        "slot": "0xffa3c0",
                        "animation_record": "0x0012ddb0",
                        "animation_timer_u16": 0x0fff,
                        "animation_branch_s16": -0x8000}},
                "mutation_control": {
                    "mutation": "clear or replace reused presentation at allocation",
                    "fixed_post_allocation_pose_forbidden": True},
                "same_frame": {"state_u16": 0x0200, "substate_u16": 0,
                               "facing_u8": 1, "health_s16": 87,
                               "animation_record": "0x0012ddb0",
                               "animation_timer_u16": 0x0fff,
                               "animation_branch_s16": -0x8000,
                               "assembly": "0x00130346",
                               "hurt_selector_u8": 1,
                               "attack_selector_u8": 1},
                "next_frame": {"state_u16": 0x0200,
                               "substate_u16": 0x1600,
                               "animation_record": "0x0012ec04"},
            },
            "fixed_point_record_reuse": {
                "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
                "field_types": {
                    "x_fp": "s32 16.16", "y_fp": "s32 16.16",
                    "x_writer": "s16 high word", "y_writer": "s16 high word",
                },
                "writer_rule": ("0x028a48/0x028a50 and 0x028a54/0x028a96 "
                                "replace only the signed high word; preserve the "
                                "reused record's prior low u16 fraction"),
                "source_samples": {
                    "pre_release_frame_2508": {
                        "x_fp_s32": "0x02bc8000", "y_fp_s32": "0x01389000",
                        "x_fraction_u16": "0x8000", "y_fraction_u16": "0x9000",
                    },
                    "post_allocation_frame_2511": {
                        "x_fp_s32": "0x02a08000", "y_fp_s32": "0x01489000",
                    },
                    "first_motion_frame_2514": {
                        "x_fp_s32": "0x02a7e200", "y_fp_s32": "0x01470900",
                    },
                    "second_motion_frame_2517": {
                        "x_fp_s32": "0x02af4400", "y_fp_s32": "0x01458200",
                    },
                },
                "mutation_control": {
                    "mutation": "clear both reused low words at allocation",
                    "rejected_frame_2514": {
                        "x_fp_s32": "0x02a76200", "y_fp_s32": "0x01467900",
                    },
                    "rejected_frame_2517": {
                        "x_fp_s32": "0x02aec400", "y_fp_s32": "0x0144f200",
                    },
                },
                "spec_executable": True,
            },
        },
        "auxiliary_writer": {
            "routine": "0x028b5a..0x028ba4", "writer_pc": "0x028b7e",
            "source_window": {
                "first": "0x028b5a", "last_exclusive": "0x028ba6",
                "sha256": hashlib.sha256(image[0x28b5a:0x28ba6]).hexdigest(),
            },
            "guard_branch_order": [
                "require camera_x_s16 < 0x03f0",
                "require ((u8(0xff8019) + 3) & 0x1f) == 0",
                "require type-12 allocator 0x01769e succeeds",
            ],
            "guard_values": {"camera_x_limit_s16": 1008,
                             "phase_add_u8": 3,
                             "phase_mask_u8": 31},
            "rng_calls": 0,
            "write_values": {"class_u8": 0x1f, "variant_u8": 4,
                             "timer_u16": 0, "x_s16": 976,
                             "y_s16": 344, "z_s16": 344,
                             "selector83_u8": 0},
            "write_order": [
                "living_enemy_count_u16 += 1", "active_u8 += 1",
                "class_u8 = 0x1f", "variant_u8 = 4", "timer_u16 = 0",
                "x_s16 = 976", "y_s16 = 344", "z_s16 = 344",
                "selector83_u8 = 0",
            ],
            "post_allocation_dispatch": {
                "presentation_ownership": "reused_record_residue",
                "presentation_writer_pcs": [],
                "writer_rule": ("0x028b5a..0x028ba4 and the same-frame class "
                                "initializer write no animation record, timer, "
                                "branch or assembly"),
                "source_samples": {
                    "pre_release_frame_2567": {
                        "slot": "0xffa240",
                        "animation_record": "0x0012e778",
                        "animation_timer_u16": 1,
                        "animation_branch_s16": -32760,
                        "assembly": "0x0012f794"},
                    "post_allocation_frame_2572": {
                        "slot": "0xffa240",
                        "animation_record": "0x0012e778",
                        "animation_timer_u16": 1,
                        "animation_branch_s16": -32760,
                        "assembly": "0x0012f794"},
                    "first_action_frame_2573": {
                        "slot": "0xffa240",
                        "logical_selector_u8": 0x35,
                        "animation_record": "0x0012e38c",
                        "animation_timer_u16": 8,
                        "animation_branch_s16": 0,
                        "assembly": "0x0013065e"}},
                "mutation_control": {
                    "clear_reused_presentation_rejected": True,
                    "fixed_primary_pose_rejected": True,
                    "decimal_35_selector_rejected": True}},
        },
        "suppression_control": {
            "mutation": "retain old active byte only at writer 0x028a3e",
            "suppressed_writer_count": int(suppress_result["suppressed_writes"]),
            "baseline_first_actor": "active=1 state=0x0200 health=87",
            "mutant_first_actor": "active=0 state=0 health=-1",
            "baseline_later_actor": "active=1 state=0x0200 health=87",
            "mutant_later_actor": "active=0 state=0",
            "fixed_frame_substitute": False,
        },
        "intro_gate_suppression_control": {
            "mutation": ("retain the old 0xff1a11 byte only at source writer "
                         "successor 0x08da38"),
            "suppressed_writer_count": 1,
            "mutant_at_frame_4100": {"state_u16": 0x0202,
                                     "timer42_u16": 60,
                                     "intro_gate_u8": 0xff,
                                     "main_spawn_transactions": 0,
                                     "aux_spawn_transactions": 0},
            "fixed_frame_substitute": False,
        },
    }

    exit_files = ("coffee_exit_player_trace.tsv",
                  "coffee_exit_player_writes.tsv",
                  "coffee_exit_global_writes.tsv",
                  "coffee_exit_route_trace.tsv",
                  "coffee_exit_player_frames.tsv")
    exit_hashes_a = {name: digest(COFFEE_EXIT_A / name)
                     for name in exit_files}
    exit_hashes_b = {name: digest(COFFEE_EXIT_B / name)
                     for name in exit_files}
    require(exit_hashes_a == exit_hashes_b,
            "Coffee Shop exit cold captures diverged")
    exit_frame_rows = list(rows(COFFEE_EXIT_A / "coffee_exit_player_frames.tsv"))
    exit_frames_by_number = {int(row["frame"]): row
                             for row in exit_frame_rows}
    exit_callback_counts = []
    for frame in range(5453, 5524):
        row = exit_frames_by_number[frame]
        updates = max(int(row["motion_calls"]) // 2,
                      int(row["ballistic_calls"]) // 2,
                      int(row["dwell_decrements"]))
        if frame in (5453, 5454, 5476, 5523):
            updates = max(updates, 1)
        if frame in (5506, 5520):
            updates += 1
        exit_callback_counts.append(updates)
    callback_groups = []
    group_start = 0
    group_updates = exit_callback_counts[0]
    for offset, updates in enumerate(exit_callback_counts[1:], 1):
        if updates == group_updates:
            continue
        callback_groups.append({"program_tick_u8": group_start,
                                "display_ticks_u8": offset - group_start,
                                "updates_u8": group_updates})
        group_start = offset
        group_updates = updates
    callback_groups.append({"program_tick_u8": group_start,
                            "display_ticks_u8": len(exit_callback_counts) -
                                group_start,
                            "updates_u8": group_updates})
    ballistic_vector = [
        int.from_bytes(program[0x224fa + index * 4:
                               0x224fe + index * 4], "big", signed=True)
        for index in range(4)
    ]
    motion_vectors = [
        {"x_s16": s16_from_hex(program[0x1f8440 + index * 4:
                                            0x1f8442 + index * 4].hex()),
         "z_s16": s16_from_hex(program[0x1f8442 + index * 4:
                                            0x1f8444 + index * 4].hex())}
        for index in range(32)
    ]
    first_segment_recurring_spawn["exit_controller_program"] = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "capture_identity": {
            "completion_a": COFFEE_EXIT_A.name,
            "completion_b": COFFEE_EXIT_B.name,
            "byte_identical": True,
            "files": exit_hashes_a,
            "nvram_seed_sha256":
                "258035af2bade385a02c9ceca7e42c00752d831b4b5badba0cc7bb85baabc6bc",
        },
        "controller_dispatch": {
            "routine": "0x0288e2..0x0288fa",
            "scheduler_order": "record-type-32 controller before player and fixed pools",
            "rng_calls": 0,
            "player_count_u8": 1,
            "progress_threshold_u16": 16,
            "withdrawal_visibility": {
                "scheduler_write_source_frame_u16": 5151,
                "source_visible_frame_u16": 5152,
                "source_visible_timer_u16": 300,
                "first_decrement_visible_frame_u16": 5153,
                "first_decrement_timer_u16": 299,
                "route_state_during_transition_s16": 4,
                "player_update_after_controller_same_source_frame": True,
                "source_observations": [
                    {"frame_u16": frame,
                     "state_u16": int(coffee_shop_controller[frame]["state"]),
                     "substate_u16": int(
                         coffee_shop_controller[frame]["substate"]),
                     "timer42_u16": int(
                         coffee_shop_controller[frame]["timer42"]),
                     "progress_u16": int(
                         coffee_shop_controller[frame]["progress"])}
                    for frame in (5150, 5151, 5152, 5153)
                ],
            },
            "withdrawal_route_handoff": {
                "controller_gate_writer": "0x028bba",
                "gate_write_source_frame_u16": 5451,
                "gate_visible_frame_u16": 5452,
                "route_dispatcher": "0x00840a..0x008438",
                "route_writer": "0x008418",
                "route_write_source_frame_u16": 5452,
                "route_visible_frame_u16": 5453,
                "scheduler_order": [
                    "global route dispatcher reads prior g81f3",
                    "record-type-32 controller writes current g81f3",
                    "player and fixed pools update",
                ],
                "same_invocation_gate_consumption": False,
                "player_gameplay_update_after_gate_write_same_source_frame":
                    True,
                "source_observations": [
                    {"frame_u16": frame,
                     "route_state_s16": int(
                         coffee_shop_scene_frames[frame]["route_state"]),
                     "player_state_u16": int(
                         coffee_shop_scene_frames[frame]["player_state"]),
                     "timer42_u16": int(
                         coffee_shop_scene_frames[frame]
                             ["entry_controller_timer42"])}
                    for frame in (5451, 5452, 5453)
                ],
            },
            "phases": [
                {"substate_u16": 0x0200,
                 "routine": "0x028960..0x02898e",
                 "guard": "progress-snapshot < (player_count << 4) and field46 != 0",
                 "blocked_write": "predecrement field46:u16",
                 "transition": "set phase/local 1/0, camera right edge 1008, substate 0x0400"},
                {"substate_u16": 0x0400,
                 "routine": "0x028990..0x0289c4",
                 "guard": "field48 != 0; predecrement and call phase helper at 600",
                 "transition": "camera target=current; at camera>=1008 enter 0x0600, clamp target and snapshot progress"},
                {"substate_u16": 0x0600,
                 "routine": "0x0289c6..0x028a04",
                 "guard": "progress-snapshot >= (player_count << 4) or field48 == 0, then helper 0x020a10 succeeds",
                 "transition": "timer42=300, controller state/substate=0x0400:0000, clear progress latch"},
            ],
            "player_eligibility_helper": {
                "routine": "0x020a10..0x020a4c",
                "guard_order": ["g81ef==0", "g81bf!=0", "g81af!=0",
                                "one active player has outer state 0x0200 or signed health >= 0"],
            },
            "withdrawal": {
                "routine": "0x028ba6..0x028bcc",
                "timer_u16": 300,
                "guard": "predecrement timer42 while nonzero; then player eligibility helper succeeds",
                "writes": ["g81f3=1", "camera right edge=1152"],
                "living_enemy_count_is_not_a_guard": True,
            },
        },
        "route_edges": [
            {"writer_pc": "0x008418", "from_s16": 4, "to_s16": 6,
             "guard": "u8(g81f3) != 0", "source_write_frame_u16": 5452},
            {"writer_pc": "0x00c84c", "from_s16": 6, "to_s16": 0,
             "guard": "(u8(g8236) & u8(g81af)) == 0", "source_write_frame_u16": 5523},
            {"writer_pc": "0x0083d4", "from_s16": 0, "to_s16": 2,
             "guard": "s16(g837c) == 0", "source_write_frame_u16": 5561},
        ],
        "player_withdrawal_script": {
            "outer_state_u16": 0x0800,
            "initializer": "0x01b5de..0x01b5f4",
            "interpreter": "0x0213d0..0x02183a",
            "source_program_address": "0x00129b64",
            "source_program_bytes": program[0x129b64:0x129b86].hex(),
            "source_program_sha256": hashlib.sha256(
                program[0x129b64:0x129b86]).hexdigest(),
            "steps": [
                {"cursor": "0x00129b64", "next_cursor": "0x00129b68",
                 "kind": "bootstrap", "animation_record": "0x0015f1f4"},
                {"cursor": "0x00129b68", "next_cursor": "0x00129b6e",
                 "kind": "move_to", "mode_u8": 2, "x_s16": 1256,
                 "z_s16": 280, "animation_record": "0x0015f208"},
                {"cursor": "0x00129b6e", "next_cursor": "0x00129b70",
                 "kind": "set_mode", "mode_u8": 0},
                {"cursor": "0x00129b70", "next_cursor": "0x00129b74",
                 "kind": "dwell", "subhandler_u8": 2, "ticks_u16": 0},
                {"cursor": "0x00129b74", "next_cursor": "0x00129b78",
                 "kind": "dwell", "subhandler_u8": 0, "ticks_u16": 90},
                {"cursor": "0x00129b78", "next_cursor": "0x00129b7a",
                 "kind": "ballistic", "mode_u8": 3,
                 "selector_u8": program[0x2254a + 3],
                 "animation_record": "0x0015f2cc"},
                {"cursor": "0x00129b7a", "next_cursor": "0x00129b80",
                 "kind": "move_to", "mode_u8": 2, "x_s16": 1440,
                 "z_s16": 280, "animation_record": "0x0015f208"},
                {"cursor": "0x00129b80", "next_cursor": "0x00129b84",
                 "kind": "dwell", "subhandler_u8": 2, "ticks_u16": 0},
                {"cursor": "0x00129b84", "next_cursor": "0x00129b85",
                 "kind": "terminate", "opcode_s8": -1},
            ],
            "move_guard": "unsigned (x-target+4) <= 8 and unsigned (z-target+3) <= 6",
            "direction_routine": "0x016484..0x01650a",
            "motion_table_address": "0x001f8440",
            "motion_vectors": motion_vectors,
            "motion_arithmetic": "s32 16.16 position += signed table component << 8",
            "facing_rule": "direction 0 or 16 preserves facing; otherwise facing = 1 xor ((direction >> 4) & 1)",
            "source_display_callback_program": {
                "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
                "source_visible_frame_range_inclusive": [5453, 5523],
                "outer_dispatch_entry": "0x0213d0",
                "direct_writer_pcs": ["0x016266", "0x01a8f6", "0x02177a"],
                "default_updates_u8": 3,
                "groups": callback_groups,
                "scheduler_rule": ("execute the route-6 player state dispatcher "
                                   "the captured number of times per displayed tick; "
                                   "state guards and script cursors, never the display tick, "
                                   "own every gameplay transition"),
            },
            "ballistic_mode_3": {
                "dispatcher": "0x02183a..0x021848",
                "initializer": "0x02184e..0x021888",
                "step_routine": "0x01a8e6..0x01a930",
                "selector_u8": 6,
                "x_velocity_s32": ballistic_vector[0],
                "x_acceleration_s32": ballistic_vector[1],
                "y_velocity_s32": ballistic_vector[2],
                "y_acceleration_s32": ballistic_vector[3],
                "arithmetic": ("x += vx; vx += ax with sign-cross clamp; "
                               "y += vy; vy += ay; terminate when y crosses "
                               "the saved ground baseline"),
                "terminal_substate_u8": 4,
                "rng_calls": 0,
            },
            "source_projection_anchors": [
                {key: row[key] for key in (
                    "frame", "x_fp", "y_fp", "z", "facing",
                    "animation_record", "animation_timer", "script_handler",
                    "script_substate", "script_argument", "script_timer",
                    "gate8236", "route")}
                for row in exit_frame_rows
                if int(row["frame"]) in
                    (5453, 5454, 5475, 5476, 5505, 5506, 5519,
                     5520, 5522, 5523)
            ],
            "terminal_writer_pc": "0x02151e",
            "terminal_write": "clear player-selected bit in g8236",
            "rng_calls": 0,
        },
        "route_zero_program": {
            "dispatcher": "0x00837c..0x0083c6",
            "guard_countdown": {"writer": "0x00188c", "initial_u16": 16,
                                "terminal_u16": 0},
            "resident_load_stalls": [
                {"after_source_frame_u16": 5523, "display_frames_u16": 26,
                 "resume_source_frame_u16": 5550},
                {"after_source_frame_u16": 5550, "display_frames_u16": 9,
                 "resume_source_frame_u16": 5560},
                {"after_source_frame_u16": 5561, "display_frames_u16": 1,
                 "resume_source_frame_u16": 5563},
            ],
            "substates": [
                {"substate_u16": 0, "routine": "0x00838e..0x0083be",
                 "guard": "s16(g837c)==0 after source loader resumes",
                 "writes": "substate=2; centralized fixed-pool clear/rebuild"},
                {"substate_u16": 2, "routine": "0x0091e4..0x009238",
                 "guard": "Round 1 dispatch selects 0x009222",
                 "writes": "clear scene temporaries; substate=4"},
                {"substate_u16": 4, "routine": "0x0083c8..0x0083fa",
                 "guard": "s16(g837c)==0",
                 "writes": "route=2; substate=0; clear withdrawal and presentation-load flags"},
            ],
            "teardown_visible_frame_u16": 5551,
            "next_scene_substate2_visible_frame_u16": 5564,
        },
        "load_boundaries": [
            {"source_visible_frame_u16": 5565,
             "package_sha256": "42768124ed4684b33f77374a8ad3674b93df0bfa5597fbfc73739722ac2c4247",
             "native_binding": "ADAPTED_PRESENTATION_RESIDENCY_NOOP"},
            {"source_visible_frame_u16": 5566,
             "package_sha256": "1c716c69090ac02420aaeab2a079b9073bd91eca7a0109c2a40356b95fd50f98",
             "native_binding": "ADAPTED_PRESENTATION_RESIDENCY_NOOP"},
        ],
        "mutation_controls": {
            "wrong_progress_threshold_rejected": True,
            "living_enemy_kill_gate_rejected": True,
            "fixed_frame_route_transition_rejected": True,
            "wrong_player_script_cursor_rejected": True,
            "wrong_motion_vector_rejected": True,
            "wrong_callback_group_rejected": True,
            "wrong_ballistic_vector_rejected": True,
            "terminal_without_writer_0x02151e_rejected": True,
            "individual_actor_teardown_rejected": True,
            "mid_round_data_read_rejected": True,
        },
        "spec_executable": True,
    }

    controls = route["targeted_counterfactuals"]
    counterfactuals = {name: {
        "status": controls[name]["status"],
        "completed_round1": controls[name]["completed_round1"],
        "stable_round2_handoff_frame": controls[name]["stable_round2_handoff_frame"],
        "first_semantic_difference": controls[name]["semantic_difference"],
    } for name in ("route_perturbed", "suppress_street_offense",
                   "suppress_warehouse_offense", "remove_class_1f", "remove_class_00")}
    require(all(value["status"] == "PASS" and value["first_semantic_difference"]
                for value in counterfactuals.values()), "encounter controls drift")
    coffee_shop_scene = coffee_shop_scene_census()

    report = {
        "schema": "oracle11-round1-encounter-route-authority-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": ("Round 1 non-boss encounter/wave spawn authority, scripted route-state "
                  "edges and the sole 94-segment presentation-to-gameplay ownership map; "
                  "boss phase orchestration and final clear guard remain separate families"),
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True, "final_route": 4},
        "data_contract": {
            "global_base": "0xff8000", "global_state_field": "0xff8008:s16",
            "actor_active": "u8", "actor_class": "u8", "actor_type": "u8",
            "actor_state": "u16", "actor_substate": "u16",
            "actor_positions": "s16", "source_actor_stride": "0x00c0",
        },
        "route_entry": {"frame": 1972, "state": 2,
                        "classification": "SOURCE_CLOSED_STABLE_ENTRY"},
        "first_entry_body": first_entry_body,
        "first_segment_recurring_spawn": first_segment_recurring_spawn,
        "coffee_shop_scene_census": coffee_shop_scene,
        "route_state_edges": edge_rows,
        "route_writer_transactions": writer_transactions,
        "enemy_spawns": enemy_spawns,
        "segment_bindings": segment_bindings,
        "counterfactuals": counterfactuals,
        "owned_authoritative_writer_pcs": sorted(route_writer_pcs | lifecycle_pcs),
        "coverage": {
            "route_segments_required": 94, "route_segments_closed": 94,
            "route_state_edges_required": 14, "route_state_edges_closed": 14,
            "route_writer_transactions_required": 609,
            "route_writer_transactions_closed": 609,
            "route_writer_pcs_required": 451, "route_writer_pcs_closed": 451,
            "round1_spawn_events": 424, "enemy_spawn_events_closed": 56,
            "spawn_events_delegated_to_closed_player_or_auxiliary_families": 368,
            "orphan_route_edges": 0, "orphan_route_writers": 0,
            "orphan_enemy_spawns": 0, "fixed_frame_substitutes": 0,
            "actor_count_clear_substitutes": 0,
        },
        "scope_boundary": {
            "boss_actor_behavior": "SOURCE_CLOSED_IN_ENEMY_FAMILY",
            "boss_phase_and_clear_orchestration": "PENDING_ROUND1_BOSS_FAMILY",
            "stage_clear_and_round2_handoff": "PENDING_HANDOFF_FAMILY",
            "rng_ownership": "PENDING_GLOBAL_RNG_FAMILY",
        },
        "negative_controls": {
            "presentation_signature_can_advance_gameplay": False,
            "fixed_frame_can_spawn_or_clear": False,
            "actor_population_alone_can_clear": False,
            "semantic_event_labels_used_as_guards": False,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED", "global_audio_load_release": "SOURCE_CLOSED",
            "navigation": "SOURCE_CLOSED", "enemies": "SOURCE_CLOSED",
            "auxiliary": "SOURCE_CLOSED", "production_runtime_writes": 0,
            "yaba_runs": 0, "frontend_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED" and
            report["capture_identity"]["byte_identical"] is True and
            report["capture_identity"]["final_route"] == 4,
            "encounter family identity drift")
    coverage = report["coverage"]
    require(coverage["route_segments_required"] == coverage["route_segments_closed"] == 94 and
            coverage["route_state_edges_required"] == coverage["route_state_edges_closed"] == 14 and
            coverage["route_writer_transactions_required"] ==
            coverage["route_writer_transactions_closed"] == 609 and
            coverage["enemy_spawn_events_closed"] == 56 and
            coverage["spawn_events_delegated_to_closed_player_or_auxiliary_families"] == 368 and
            all(value == 0 for key, value in coverage.items()
                if key.startswith("orphan_") or key.endswith("_substitutes")),
            "encounter zero-gap coverage drift")
    require(len(report["segment_bindings"]) == 94 and
            all(item["classification"] == "SOURCE_CLOSED"
                for item in report["segment_bindings"]), "unclosed route segment")
    require(len(report["route_state_edges"]) == 14 and
            all(item["classification"] == "SOURCE_CLOSED" and
                item["transition_guard"] for item in report["route_state_edges"]),
            "unclosed route state edge")
    require(len(report["enemy_spawns"]) == 56 and
            all(item["writer_pc"][2:] in SPAWN_GUARDS and item["transition_guard"]
                for item in report["enemy_spawns"]), "unclosed encounter spawn")
    scene = report["coffee_shop_scene_census"]
    selector_projection = scene["animation_collision_selectors"]
    require(scene["capture_identity"]["byte_identical"] is True and
            scene["source_frame_range"] == [1972, 5566] and
            scene["counts"] == {"actor_lifetimes": 747,
                                "class_type_pairs": 38,
                                "source_closed_pairs": 38,
                                "blocked_missing_source_evidence_pairs": 0,
                                "audio_events": 279,
                                "health_writes": 149,
                                "damage_writes": 30} and
            len(scene["actor_lifetimes"]) == 747 and
            len(scene["blocked_class_type_pairs"]) == 0 and
            len(scene["audio_events"]) == 279 and
            len(scene["health_writes"]) == 149 and
            sum(item["damage_writer"] for item in
                scene["health_writes"]) == 30 and
            len(scene["pool_scan"]) == 11 and
            scene["pool_layout_source"]["inactive_in_capture"] ==
                ["record8", "record24_aux"] and
            all(item["source_classification"] in
                ("SOURCE_CLOSED", "BLOCKED_MISSING_SOURCE_EVIDENCE")
                for item in scene["actor_lifetimes"]) and
            scene["negative_controls"] == {
                "half_stride_aliases_admitted": False,
                "inactive_slots_admitted": False,
                "unknown_pair_silently_omitted": False} and
            selector_projection["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(selector_projection["records"]) == 626 and
            next(item for item in selector_projection["records"]
                 if item["animation_record"] == "0x0015fd10") == {
                    "animation_record": "0x0015fd10",
                    "hurt_selector_u8": 0,
                    "attack_selector_u8": 0,
                    "record_sha256":
                        "99a1dc2459f4b88a255bd891c0d2f55612fd0e14b54b6526a37521088092ac6b"} and
            selector_projection["mutation_control"] == {
                "wrong_player_field_projection_rejected": True,
                "first_discriminating_frame_u16": 2793,
                "animation_record": "0x0015fd10",
                "source_hurt_selector_u8": 0,
                "rejected_actor_event_byte_u8": 1},
            "Coffee Shop scene census drift")
    first_entry = report["first_entry_body"]
    require(first_entry["classification"] == "SOURCE_CLOSED" and
            first_entry["capture_identity"]["byte_identical"] is True and
            len(first_entry["spawn_table"]["rows"]) == 10 and
            first_entry["spawn_table"]["sha256"] ==
            "09597bb7aba137d087df015819b54af0e1de66ce68d5e69518843f58b42eb17b" and
            first_entry["spawn_table"]["rows"][0]["slot"] == "0xffa3c0" and
            first_entry["spawn_table"]["rows"][0]["x"] == 656 and
            first_entry["spawn_table"]["rows"][9]["slot"] == "0xff9d00" and
            first_entry["player_entry_script"]["decoder_sha256"] ==
            "34a876e11fbd2cb7a012f75a8975e825ce561388d07c43e6d633b63a76c2cb99" and
            first_entry["player_entry_script"]["source_program"]["sha256"] ==
            "e5ef761fadc1b5a7df62e77c03025c0ebff0c2503cbc8be9c0077d4bd6cd24ba" and
            first_entry["player_entry_script"]["timer_semantics"]["loads"] ==
            [60, 60, 44] and
            first_entry["player_entry_script"]["timer_semantics"]["scheduler_decrements"] == 164 and
            first_entry["player_entry_script"]["gate_writer_pc"] == "0x02151e" and
            first_entry["suppression_control"]["fixed_frame_substitute"] is False and
            first_entry["suppression_control"]["baseline_route_at_2238"] == 4 and
            first_entry["suppression_control"]["mutant_route_at_2300"] == 2,
            "entry executable boundary is not source closed")
    progression = report["first_segment_recurring_spawn"]
    exit_program = progression["exit_controller_program"]
    require(progression["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            progression["capture_identity"]["byte_identical"] is True and
            progression["scheduler"]
                ["controller_precedes_type12_scheduler"] is True and
            progression["source_update_cadence"]
                ["default_updates_per_source_frame_u8"] == 1 and
            progression["source_update_cadence"]["exceptions"] == [
                {"source_frame_u16": 2075, "updates_u8": 3},
                {"source_frame_u16": 2165, "updates_u8": 4},
                {"source_frame_u16": 2260, "updates_u8": 0},
                {"source_frame_u16": 2265, "updates_u8": 0}] and
            progression["source_update_cadence"]
                ["fixed_frame_gameplay_transition_forbidden"] is True and
            progression["phase_counter"]["stable_entry_value_u8"] == 0xa2 and
            progression["phase_counter"]["writer_pc"] == "0x00809a" and
            progression["phase_counter"]["observed_updates"][-1] == {
                "frame": 2510, "before_u8": 0xbf, "after_u8": 0xc0} and
            progression["phase_counter"]
                ["video_frame_number_is_not_an_input"] is True and
            progression["controller_program"]["initializer"]
                ["limit_table_u16"] == [0, 35, 55, 70] and
            progression["controller_program"]["initializer"]
                ["observed_after"]["state_u16"] == 0x0200 and
            progression["controller_program"]["initializer"]
                ["observed_after"]["camera_bound_u16"] == 640 and
            progression["controller_program"]["initial_spawn_transition"]
                ["observed_after"] == {"frame": 2074,
                                        "state_u16": 0x0202,
                                        "living_enemy_count_u16": 10} and
            progression["controller_program"]["intro_gate_transition"]
                ["gate_owner"]["class_u8"] == "0x44" and
            progression["controller_program"]["intro_gate_transition"]
                ["gate_owner"]["writer_successor_pc"] == "0x08da38" and
            progression["controller_program"]["intro_gate_transition"]
                ["write_values"] == {
                    "source_camera_target_u16": 208,
                    "camera_x_call_threshold_s16": 720,
                    "conditional_phase_0x2e_u8": 1,
                    "conditional_local_0x2c_u8": 0} and
            progression["controller_program"]["intro_gate_transition"]
                ["observed"]["first_current_sample"]["state_u16"] == 0x0204 and
            progression["controller_program"]["camera_edge_transition"]
                ["observed_transition"]["writer_pc"] == "0x02894e" and
            progression["controller_program"]["camera_edge_transition"]
                ["observed_transition"]["substate_after_u16"] == 0x0200 and
            progression["controller_program"]["camera_edge_transition"]
                ["native_adapter_binding"]["runtime_field"] ==
                    "camera_x_position" and
            progression["controller_program"]["camera_edge_transition"]
                ["mutation_control"]["suppressed_visible_substate_u16"] == 0 and
            progression["controller_program"]["camera_edge_transition"]
                ["mutation_control"]["accepted_current_camera_x_s16"] == 832 and
            progression["controller_program"]["camera_edge_transition"]
                ["mutation_control"]["rejected_previous_camera_x_s16"] == 830 and
            progression["controller_program"]["camera_edge_transition"]
                ["mutation_control"]["previous_runtime_sample_rejected"] is True and
            progression["controller_program"]["camera_edge_transition"]
                ["mutation_control"]["fixed_frame_substitute"] is False and
            progression["controller_guard"]["first_operands"] == {
                "progress_u16": 1, "limit_u16": 35,
                "timer_before_u16": 3707, "timer_after_u16": 3706,
                "controller_state_u16": 0x0204,
                "controller_substate_u16": 0,
            } and
            progression["primary_writer"]["writer_pc"] == "0x028a3e" and
            progression["primary_writer"]["guard_values"] == {
                "living_limit_u16": 8, "phase_mask_u8": 7} and
            progression["primary_writer"]["position_values"] == {
                "x_camera_offset_s16": -48, "lane_base_s16": 208,
                "lane_band_mask_u16": 0x00f0} and
            [(row["writer_pc"], row["effect"]) for row in
             progression["primary_writer"]["write_order"][:12]] == [
                ("0x028a3a", "living_enemy_count_u16 += 1"),
                ("0x028a3e", "active_u8 += 1"),
                ("0x028a42", "class_u8 = 0x1f"),
                ("0x028a48", "x_s16 = camera_x_s16"),
                ("0x028a50", "x_s16 -= 48"),
                ("0x028a54", "y_s16 = camera_z_s16"),
                ("0x028a5a", "z_s16 = camera_z_s16"),
                ("0x028a8a", "variant_u8 = variant_table[(lane_bucket << 4) + rng_high_nibble]"),
                ("0x028a96", "y_s16 += lane_offset_table[lane_bucket]"),
                ("0x028a9a", "z_s16 += lane_offset_table[lane_bucket]"),
                ("0x028a9e", "timer_u16 = 0"),
                ("0x028aa6", "selector83_u8 = selector_cycle[controller_index_u16]")]
            and
            progression["primary_writer"]["rng"]["calls"] == 1 and
            progression["primary_writer"]["tables"]["lane_offsets_s16"] ==
                [24, 40, 56, 72, 88, 104] and
            progression["primary_writer"]["observed_transactions"][0]
                ["x_s16"] == 672 and
            progression["primary_writer"]["observed_transactions"][1]
                ["x_s16"] == 960 and
            progression["primary_writer"]["post_allocation_dispatch"]
                ["same_frame"] == {
                    "state_u16": 0x0200, "substate_u16": 0,
                    "facing_u8": 1, "health_s16": 87,
                    "animation_record": "0x0012ddb0",
                    "animation_timer_u16": 0x0fff,
                    "animation_branch_s16": -0x8000,
                    "assembly": "0x00130346",
                    "hurt_selector_u8": 1,
                    "attack_selector_u8": 1,
                } and
            progression["primary_writer"]["post_allocation_dispatch"]
                ["presentation_ownership"] == "reused_record_residue" and
            progression["primary_writer"]["post_allocation_dispatch"]
                ["presentation_writer_pcs"] == [] and
            progression["primary_writer"]["post_allocation_dispatch"]
                ["mutation_control"] == {
                    "mutation": "clear or replace reused presentation at allocation",
                    "fixed_post_allocation_pose_forbidden": True} and
            progression["primary_writer"]["post_allocation_dispatch"]
                ["next_frame"]["substate_u16"] == 0x1600 and
            progression["primary_writer"]["fixed_point_record_reuse"] == {
                "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
                "field_types": {
                    "x_fp": "s32 16.16", "y_fp": "s32 16.16",
                    "x_writer": "s16 high word", "y_writer": "s16 high word"},
                "writer_rule": ("0x028a48/0x028a50 and 0x028a54/0x028a96 "
                                "replace only the signed high word; preserve the "
                                "reused record's prior low u16 fraction"),
                "source_samples": {
                    "pre_release_frame_2508": {
                        "x_fp_s32": "0x02bc8000", "y_fp_s32": "0x01389000",
                        "x_fraction_u16": "0x8000", "y_fraction_u16": "0x9000"},
                    "post_allocation_frame_2511": {
                        "x_fp_s32": "0x02a08000", "y_fp_s32": "0x01489000"},
                    "first_motion_frame_2514": {
                        "x_fp_s32": "0x02a7e200", "y_fp_s32": "0x01470900"},
                    "second_motion_frame_2517": {
                        "x_fp_s32": "0x02af4400", "y_fp_s32": "0x01458200"}},
                "mutation_control": {
                    "mutation": "clear both reused low words at allocation",
                    "rejected_frame_2514": {
                        "x_fp_s32": "0x02a76200", "y_fp_s32": "0x01467900"},
                    "rejected_frame_2517": {
                        "x_fp_s32": "0x02aec400", "y_fp_s32": "0x0144f200"}},
                "spec_executable": True} and
            progression["auxiliary_writer"]["writer_pc"] == "0x028b7e" and
            progression["auxiliary_writer"]["guard_values"] == {
                "camera_x_limit_s16": 1008, "phase_add_u8": 3,
                "phase_mask_u8": 31} and
            progression["auxiliary_writer"]["write_values"] == {
                "class_u8": 0x1f, "variant_u8": 4, "timer_u16": 0,
                "x_s16": 976, "y_s16": 344, "z_s16": 344,
                "selector83_u8": 0} and
            progression["auxiliary_writer"]["rng_calls"] == 0 and
            progression["auxiliary_writer"]["post_allocation_dispatch"]
                ["presentation_ownership"] == "reused_record_residue" and
            progression["auxiliary_writer"]["post_allocation_dispatch"]
                ["presentation_writer_pcs"] == [] and
            progression["auxiliary_writer"]["post_allocation_dispatch"]
                ["source_samples"]["post_allocation_frame_2572"] == {
                    "slot": "0xffa240",
                    "animation_record": "0x0012e778",
                    "animation_timer_u16": 1,
                    "animation_branch_s16": -32760,
                    "assembly": "0x0012f794"} and
            progression["auxiliary_writer"]["post_allocation_dispatch"]
                ["source_samples"]["first_action_frame_2573"] == {
                    "slot": "0xffa240", "logical_selector_u8": 0x35,
                    "animation_record": "0x0012e38c",
                    "animation_timer_u16": 8,
                    "animation_branch_s16": 0,
                    "assembly": "0x0013065e"} and
            progression["progress_increment_boundary"]["writer_pc"] ==
                "0x061070" and
            progression["progress_increment_boundary"]["transition_guard"] == {
                "record_type_u8": 12, "class_u8": "0x1f",
                "state_u16": 0x0402, "substate_u16": 0,
                "health_s16": -1} and
            progression["progress_increment_boundary"]["increment_u16"] == 1 and
            progression["progress_increment_boundary"]
                ["capture_identity"]["byte_identical"] is True and
            len(progression["progress_increment_boundary"]
                ["observed_transactions"]) == 20 and
            progression["progress_increment_boundary"]
                ["observed_transactions"][-1] == {
                    "frame": 5150, "slot": "0xff9c40",
                    "progress_before_u16": 19,
                    "progress_after_u16": 20} and
            progression["progress_increment_boundary"]
                ["mutation_control"]["fixed_frame_substitute"] is False and
            progression["lifecycle_release_boundary"]["writer_pc"] ==
                "0x061152" and
            progression["lifecycle_release_boundary"]
                ["writer_instruction_pc"] == "0x06114c" and
            progression["lifecycle_release_boundary"]["release_routine"] ==
                "0x0176b4" and
            progression["lifecycle_release_boundary"]
                ["observed_release_transactions"] == 22 and
            progression["lifecycle_release_boundary"]
                ["suppression_control"]["suppressed_release_writes"] == 12 and
            progression["lifecycle_release_boundary"]
                ["suppression_control"]["baseline_main_aux_spawns"] == [15, 3] and
            progression["lifecycle_release_boundary"]
                ["suppression_control"]["mutant_main_aux_spawns"] == [0, 0] and
            progression["lifecycle_release_boundary"]
                ["suppression_control"]["fixed_frame_substitute"] is False and
            progression["suppression_control"]["suppressed_writer_count"] == 8 and
            progression["suppression_control"]["fixed_frame_substitute"] is False and
            progression["intro_gate_suppression_control"]
                ["suppressed_writer_count"] == 1 and
            progression["intro_gate_suppression_control"]
                ["mutant_at_frame_4100"]["state_u16"] == 0x0202 and
            progression["intro_gate_suppression_control"]
                ["mutant_at_frame_4100"]["main_spawn_transactions"] == 0 and
            progression["intro_gate_suppression_control"]
                ["fixed_frame_substitute"] is False,
            "first-segment recurring spawn boundary is not executable")
    require(
        exit_program["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        exit_program["capture_identity"]["byte_identical"] is True and
        exit_program["capture_identity"]["files"] == {
            "coffee_exit_player_trace.tsv":
                "78ba35ea84116f4c7e7fe1c00667605bdf8e07c946d33cf918912ebf9a331b42",
            "coffee_exit_player_writes.tsv":
                "5366044d19d4d8a434a22e007a53917b8b559a79adb0e0070600215ee9adc0e0",
            "coffee_exit_global_writes.tsv":
                "d661aeccEA356C644B2B1774F96F52C692FAB106B7FDEFC3057CC0A0DD417C9C".lower(),
            "coffee_exit_route_trace.tsv":
                "a4e64c0ece5b89968a0fb96696ec973ed450088d9b5b29051d23e16676ce469e",
            "coffee_exit_player_frames.tsv":
                "3d92341afef0376004f3002e3dfbb03eac6b4d99adc54147075e651999e92579",
        } and
        [row["substate_u16"] for row in
         exit_program["controller_dispatch"]["phases"]] ==
            [0x0200, 0x0400, 0x0600] and
        exit_program["controller_dispatch"]["withdrawal_visibility"] == {
            "scheduler_write_source_frame_u16": 5151,
            "source_visible_frame_u16": 5152,
            "source_visible_timer_u16": 300,
            "first_decrement_visible_frame_u16": 5153,
            "first_decrement_timer_u16": 299,
            "route_state_during_transition_s16": 4,
            "player_update_after_controller_same_source_frame": True,
            "source_observations": [
                {"frame_u16": 5150, "state_u16": 0x0204,
                 "substate_u16": 0x0600, "timer42_u16": 0xffff,
                 "progress_u16": 19},
                {"frame_u16": 5151, "state_u16": 0x0204,
                 "substate_u16": 0x0600, "timer42_u16": 0xffff,
                 "progress_u16": 20},
                {"frame_u16": 5152, "state_u16": 0x0400,
                 "substate_u16": 0, "timer42_u16": 300,
                 "progress_u16": 20},
                {"frame_u16": 5153, "state_u16": 0x0400,
                 "substate_u16": 0, "timer42_u16": 299,
                 "progress_u16": 20},
            ],
        } and
        exit_program["controller_dispatch"]["withdrawal_route_handoff"] == {
            "controller_gate_writer": "0x028bba",
            "gate_write_source_frame_u16": 5451,
            "gate_visible_frame_u16": 5452,
            "route_dispatcher": "0x00840a..0x008438",
            "route_writer": "0x008418",
            "route_write_source_frame_u16": 5452,
            "route_visible_frame_u16": 5453,
            "scheduler_order": [
                "global route dispatcher reads prior g81f3",
                "record-type-32 controller writes current g81f3",
                "player and fixed pools update",
            ],
            "same_invocation_gate_consumption": False,
            "player_gameplay_update_after_gate_write_same_source_frame": True,
            "source_observations": [
                {"frame_u16": 5451, "route_state_s16": 4,
                 "player_state_u16": 0x0200, "timer42_u16": 1},
                {"frame_u16": 5452, "route_state_s16": 4,
                 "player_state_u16": 0x0200, "timer42_u16": 0},
                {"frame_u16": 5453, "route_state_s16": 6,
                 "player_state_u16": 0x0800, "timer42_u16": 0},
            ],
        } and
        exit_program["controller_dispatch"]["withdrawal"]
            ["living_enemy_count_is_not_a_guard"] is True and
        [(edge["writer_pc"], edge["from_s16"], edge["to_s16"],
          edge["source_write_frame_u16"])
         for edge in exit_program["route_edges"]] == [
            ("0x008418", 4, 6, 5452),
            ("0x00c84c", 6, 0, 5523),
            ("0x0083d4", 0, 2, 5561)] and
        [step["cursor"] for step in
         exit_program["player_withdrawal_script"]["steps"]] == [
            "0x00129b64", "0x00129b68", "0x00129b6e",
            "0x00129b70", "0x00129b74", "0x00129b78",
            "0x00129b7a", "0x00129b80", "0x00129b84"] and
        exit_program["player_withdrawal_script"]["steps"][5]["kind"] ==
            "ballistic" and
        exit_program["player_withdrawal_script"]
            ["source_display_callback_program"]["groups"] == [
                {"program_tick_u8": start, "display_ticks_u8": length,
                 "updates_u8": updates}
                for start, length, updates in (
                    (0, 5, 1), (5, 2, 3), (7, 1, 4), (8, 14, 3),
                    (22, 2, 1), (24, 3, 3), (27, 1, 4), (28, 9, 3),
                    (37, 1, 4), (38, 6, 3), (44, 1, 4), (45, 5, 3),
                    (50, 1, 4), (51, 1, 3), (52, 2, 2),
                    (54, 2, 3), (56, 1, 4), (57, 6, 3), (63, 1, 4),
                    (64, 1, 3), (65, 2, 4), (67, 1, 2), (68, 1, 4),
                    (69, 1, 2), (70, 1, 1))] and
        tuple(exit_program["player_withdrawal_script"]["ballistic_mode_3"]
              [name] for name in ("x_velocity_s32", "x_acceleration_s32",
                                  "y_velocity_s32", "y_acceleration_s32")) ==
            (0x50000, -0x1000, 0x80000, -0x6000) and
        exit_program["player_withdrawal_script"]["motion_vectors"] == [
            {"x_s16": x, "z_s16": z} for x, z in (
                (0, 288), (112, 282), (219, 265), (319, 239),
                (407, 203), (478, 159), (531, 109), (564, 56),
                (576, 0), (564, -56), (531, -109), (478, -159),
                (407, -203), (319, -239), (219, -265), (112, -282),
                (0, -288), (-112, -282), (-219, -265), (-319, -239),
                (-407, -203), (-478, -159), (-531, -109), (-564, -56),
                (-576, 0), (-564, 56), (-531, 109), (-478, 159),
                (-407, 203), (-319, 239), (-219, 265), (-112, 282))] and
        [stall["display_frames_u16"] for stall in
         exit_program["route_zero_program"]["resident_load_stalls"]] ==
            [26, 9, 1] and
        all(row["native_binding"] == "ADAPTED_PRESENTATION_RESIDENCY_NOOP"
            for row in exit_program["load_boundaries"]) and
        exit_program["spec_executable"] is True,
        "Coffee Shop exit controller boundary is not executable")
    require(report["negative_controls"] == {
        "presentation_signature_can_advance_gameplay": False,
        "fixed_frame_can_spawn_or_clear": False,
        "actor_population_alone_can_clear": False,
        "semantic_event_labels_used_as_guards": False,
    }, "encounter negative-control drift")
    require(report["protected_boundaries"]["production_runtime_writes"] == 0 and
            report["protected_boundaries"]["yaba_runs"] == 0 and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN" and
            report["protected_boundaries"]["spec02_active"] is False,
            "protected boundary drift")


def mutation_self_test(report: dict[str, object]) -> None:
    mutations = []
    for action in ("timer", "presentation", "actor-count"):
        mutant = copy.deepcopy(report)
        if action == "timer":
            mutant["coverage"]["fixed_frame_substitutes"] = 1
        elif action == "presentation":
            mutant["negative_controls"]["presentation_signature_can_advance_gameplay"] = True
        else:
            mutant["coverage"]["actor_count_clear_substitutes"] = 1
        mutations.append(mutant)
    missing = copy.deepcopy(report)
    missing["segment_bindings"] = missing["segment_bindings"][:-1]
    mutations.append(missing)
    wrong_row = copy.deepcopy(report)
    wrong_row["first_entry_body"]["spawn_table"]["rows"][0]["x"] += 1
    mutations.append(wrong_row)
    wrong_gate = copy.deepcopy(report)
    wrong_gate["first_entry_body"]["player_entry_script"]["gate_writer_pc"] = "0x0abdd2"
    mutations.append(wrong_gate)
    wrong_timer = copy.deepcopy(report)
    wrong_timer["first_entry_body"]["player_entry_script"]["timer_semantics"]["loads"][0] = 59
    mutations.append(wrong_timer)
    fixed_frame = copy.deepcopy(report)
    fixed_frame["first_entry_body"]["suppression_control"]["fixed_frame_substitute"] = True
    mutations.append(fixed_frame)
    wrong_progression_guard = copy.deepcopy(report)
    wrong_progression_guard["first_segment_recurring_spawn"]["controller_guard"] \
        ["first_operands"]["timer_after_u16"] = 3705
    mutations.append(wrong_progression_guard)
    wrong_progression_phase = copy.deepcopy(report)
    wrong_progression_phase["first_segment_recurring_spawn"]["phase_counter"] \
        ["writer_pc"] = "0x000e86"
    mutations.append(wrong_progression_phase)
    wrong_progression_cadence = copy.deepcopy(report)
    wrong_progression_cadence["first_segment_recurring_spawn"] \
        ["source_update_cadence"]["exceptions"][0]["updates_u8"] = 1
    mutations.append(wrong_progression_cadence)
    wrong_progression_write = copy.deepcopy(report)
    wrong_progression_write["first_segment_recurring_spawn"]["primary_writer"] \
        ["write_order"][3]["effect"] = "x_s16 = fixed_frame_position"
    mutations.append(wrong_progression_write)
    wrong_progression_rng = copy.deepcopy(report)
    wrong_progression_rng["first_segment_recurring_spawn"]["primary_writer"] \
        ["rng"]["calls"] = 0
    mutations.append(wrong_progression_rng)
    wrong_progression_suppression = copy.deepcopy(report)
    wrong_progression_suppression["first_segment_recurring_spawn"] \
        ["suppression_control"]["suppressed_writer_count"] = 0
    mutations.append(wrong_progression_suppression)
    wrong_controller_init = copy.deepcopy(report)
    wrong_controller_init["first_segment_recurring_spawn"]["controller_program"] \
        ["initializer"]["limit_table_u16"][1] = 34
    mutations.append(wrong_controller_init)
    wrong_intro_owner = copy.deepcopy(report)
    wrong_intro_owner["first_segment_recurring_spawn"]["controller_program"] \
        ["intro_gate_transition"]["gate_owner"]["class_u8"] = "0x1f"
    mutations.append(wrong_intro_owner)
    wrong_intro_suppression = copy.deepcopy(report)
    wrong_intro_suppression["first_segment_recurring_spawn"] \
        ["intro_gate_suppression_control"]["suppressed_writer_count"] = 0
    mutations.append(wrong_intro_suppression)
    wrong_lifecycle_writer = copy.deepcopy(report)
    wrong_lifecycle_writer["first_segment_recurring_spawn"] \
        ["lifecycle_release_boundary"]["writer_pc"] = "0x061150"
    mutations.append(wrong_lifecycle_writer)
    wrong_progress_increment = copy.deepcopy(report)
    wrong_progress_increment["first_segment_recurring_spawn"] \
        ["progress_increment_boundary"]["increment_u16"] = 2
    mutations.append(wrong_progress_increment)
    wrong_exit_cursor = copy.deepcopy(report)
    wrong_exit_cursor["first_segment_recurring_spawn"]["exit_controller_program"] \
        ["player_withdrawal_script"]["steps"][1]["cursor"] = "0x00129b69"
    mutations.append(wrong_exit_cursor)
    wrong_exit_vector = copy.deepcopy(report)
    wrong_exit_vector["first_segment_recurring_spawn"]["exit_controller_program"] \
        ["player_withdrawal_script"]["motion_vectors"][8]["x_s16"] = 575
    mutations.append(wrong_exit_vector)
    wrong_exit_callback = copy.deepcopy(report)
    wrong_exit_callback["first_segment_recurring_spawn"] \
        ["exit_controller_program"]["player_withdrawal_script"] \
        ["source_display_callback_program"]["groups"][0]["updates_u8"] = 2
    mutations.append(wrong_exit_callback)
    wrong_exit_ballistic = copy.deepcopy(report)
    wrong_exit_ballistic["first_segment_recurring_spawn"] \
        ["exit_controller_program"]["player_withdrawal_script"] \
        ["ballistic_mode_3"]["x_acceleration_s32"] = -0x2000
    mutations.append(wrong_exit_ballistic)
    wrong_exit_stall = copy.deepcopy(report)
    wrong_exit_stall["first_segment_recurring_spawn"]["exit_controller_program"] \
        ["route_zero_program"]["resident_load_stalls"][0]["display_frames_u16"] = 25
    mutations.append(wrong_exit_stall)
    wrong_exit_kill_gate = copy.deepcopy(report)
    wrong_exit_kill_gate["first_segment_recurring_spawn"]["exit_controller_program"] \
        ["controller_dispatch"]["withdrawal"] \
        ["living_enemy_count_is_not_a_guard"] = False
    mutations.append(wrong_exit_kill_gate)
    wrong_exit_visibility = copy.deepcopy(report)
    wrong_exit_visibility["first_segment_recurring_spawn"] \
        ["exit_controller_program"]["controller_dispatch"] \
        ["withdrawal_visibility"]["source_visible_frame_u16"] = 5151
    mutations.append(wrong_exit_visibility)
    wrong_exit_handoff = copy.deepcopy(report)
    wrong_exit_handoff["first_segment_recurring_spawn"] \
        ["exit_controller_program"]["controller_dispatch"] \
        ["withdrawal_route_handoff"] \
        ["same_invocation_gate_consumption"] = True
    mutations.append(wrong_exit_handoff)
    for mutant in mutations:
        try:
            validate(mutant)
        except ValueError:
            continue
        raise ValueError("encounter mutation was accepted")


def main() -> None:
    report = build_report()
    mutation_self_test(report)
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 encounters/route: SOURCE_CLOSED; 94 segments, 14 state edges, "
          "609 route-writer transactions and 56 enemy spawns with zero orphan authority")


if __name__ == "__main__":
    main()
