#!/usr/bin/env python3
"""Close route-wide Round 1 navigation, terrain, obstacle and camera authority."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_A = ROOT / ".deps" / "mame" / "oracle11_round1_navigation_a"
BASE_B = ROOT / ".deps" / "mame" / "oracle11_round1_navigation_b"
PERTURBED = ROOT / ".deps" / "mame" / "oracle11_round1_navigation_perturbed"
CORRECTIVE_A = ROOT / ".deps" / "mame" / "reimplement13_navigation_fields_g"
CORRECTIVE_B = ROOT / ".deps" / "mame" / "reimplement13_navigation_fields_h"
OBSTACLE_A = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs21a"
OBSTACLE_B = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs21b"
OBSTACLE_MUTANT = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs21s"
ORACLE08 = ROOT / "data" / "oracle08_round1_navigation_bounds.json"
ORACLE10 = ROOT / "data" / "oracle10_round1_route.json"
SCHEDULER = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"
GLOBAL_AUDIO = ROOT / "data" / "oracle11_global_audio_trigger_owners.json"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
OUT = ROOT / "data" / "oracle11_round1_navigation.json"
CAPTURE_FILES = (
    "navigation_samples.tsv", "navigation_writes.tsv",
    "navigation_body_writes.tsv", "camera_writes.tsv", "samples.tsv",
    "dispatches.tsv", "projectiles.tsv", "score_writes.tsv", "result.tsv",
)
CORRECTIVE_FILES = (
    "navigation_fields.tsv", "navigation_resolves.tsv",
    "camera_bound_writes.tsv", "terrain_map.bin",
)
TERRAIN_RECORDS = {
    "0x0b20c6": "0080808080808080",
    "0x0b20d6": "0202808010100080",
    "0x0b2136": "0202808010080080",
    "0x0b2186": "0604020100008080",
    "0x0b218e": "0604020100088080",
    "0x0b220e": "0402020100088080",
}
TYPE20_ROUTINES = {
    "0x07": (0x06D1AA, 0x06D418),
    "0x08": (0x06D53C, 0x06D7B8),
    "0x09": (0x06D926, 0x06DBDA),
    "0x0a": (0x06DE92, 0x06E136),
}
OBSTACLE_CAPTURE_FILES = (
    "coffee_shop_obstacle_trace.tsv", "coffee_shop_obstacle_writes.tsv",
    "coffee_shop_obstacle_guard.tsv", "coffee_shop_type36_writes.tsv",
    "coffee_shop_scene_actors.tsv", "coffee_shop_scene_frames.tsv",
    "coffee_shop_scene_health_writes.tsv", "coffee_shop_rng_calls.tsv",
    "dispatches.tsv", "progression_result.tsv",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def corrective_identity(path: Path) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    require(manifest["task"] == "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1" and
            manifest["authority_family"] ==
            "round1-navigation-terrain-camera-corrective-oracle" and
            manifest["frame_window"] == [3400, 5200],
            f"{path.name}: corrective authority identity drift")
    for filename in CORRECTIVE_FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {
        "manifest_sha256": digest(manifest_path),
        "mame_sha256": manifest["mame_sha256"],
        "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
        "files": {name: manifest["sha256"][name]
                  for name in CORRECTIVE_FILES},
    }


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def capture_identity(path: Path) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    require(manifest["authority_family"] == "round1-navigation-terrain-camera",
            f"{path.name}: authority-family identity drift")
    for filename in CAPTURE_FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {
        "manifest_sha256": digest(manifest_path),
        "variant": manifest["variant"],
        "mame_sha256": manifest["mame_sha256"],
        "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
        "files": {name: manifest["sha256"][name] for name in CAPTURE_FILES},
    }


def parse_result(path: Path) -> dict[str, object]:
    row = rows(path / "result.tsv")[0]
    return {key: int(value) if key not in ("variant", "final_score") else value
            for key, value in row.items()}


def coffee_shop_obstacle_lifecycle(opcodes: bytes,
                                   program: bytes) -> dict[str, object]:
    def animation_record(address: int) -> dict[str, object]:
        blob = program[address:address + 16]
        require(len(blob) == 16, "Coffee Shop animation record outside program")
        return {
            "animation_record": f"0x{address:06x}",
            "timer_u16": int.from_bytes(blob[0:2], "big"),
            "branch_s16": int.from_bytes(blob[2:4], "big", signed=True),
            "assembly": f"0x{int.from_bytes(blob[4:8], 'big'):06x}",
            "hurt_selector_u8": blob[8], "attack_selector_u8": blob[9],
            "record_sha256": hashlib.sha256(blob).hexdigest(),
        }
    identity_a = {name: digest(OBSTACLE_A / name)
                  for name in OBSTACLE_CAPTURE_FILES}
    identity_b = {name: digest(OBSTACLE_B / name)
                  for name in OBSTACLE_CAPTURE_FILES}
    identity_mutant = {name: digest(OBSTACLE_MUTANT / name)
                       for name in OBSTACLE_CAPTURE_FILES}
    require(identity_a == identity_b,
            "Coffee Shop obstacle lifecycle baselines differ")
    trace = rows(OBSTACLE_A / "coffee_shop_obstacle_trace.tsv")
    writes = rows(OBSTACLE_A / "coffee_shop_obstacle_writes.tsv")
    guard_writes = rows(OBSTACLE_A / "coffee_shop_obstacle_guard.tsv")
    rng_calls = rows(OBSTACLE_A / "coffee_shop_rng_calls.tsv")
    actors = rows(OBSTACLE_A / "coffee_shop_scene_actors.tsv")
    baseline_result = rows(OBSTACLE_A / "progression_result.tsv")[0]
    mutant_result = rows(OBSTACLE_MUTANT / "progression_result.tsv")[0]
    obstacle = [row for row in actors if row["slot"] == "ffb380" and
                row["type"] == "20" and row["class"] == "0a"]
    children = [row for row in actors if row["type"] == "36" and
                row["class"] == "05"]
    require(len(obstacle) == 603 and int(obstacle[0]["frame"]) == 2246 and
            int(obstacle[-1]["frame"]) == 2848,
            "Coffee Shop obstacle lifetime drift")
    require({row["state"] for row in obstacle} ==
            {"0200", "0400", "0402", "0404", "0604"} and
            {row["substate"] for row in obstacle} ==
            {"0000", "0200", "0300"},
            "Coffee Shop obstacle state coverage drift")
    require(len(children) == 2244 and
            {row["slot"] for row in children} ==
            {"ffe180", "ffe1c0", "ffe200", "ffe240"} and
            {row["variant"] for row in children} ==
            {"00", "01", "02", "03"} and
            min(int(row["frame"]) for row in children) == 2246 and
            max(int(row["frame"]) for row in children) == 2806,
            "Coffee Shop obstacle child lifetimes drift")
    spawn_writes = [row for row in writes if row["frame"] == "2245" and
                    row["pc"].startswith("01bf")]
    require([row["pc"] for row in spawn_writes] ==
            ["01bf1e", "01bf22", "01bf28", "01bf2e", "01bf34",
             "01bf3a", "01bf40"], "Coffee Shop obstacle spawn writes drift")
    init_guards = [row for row in trace if row["pc"] == "06dea6"]
    require(len(init_guards) == 1 and init_guards[0]["frame"] == "2245" and
            init_guards[0]["guard_ffee8f"] == "40",
            "Coffee Shop obstacle type-36 guard drift")
    child_allocations = [row for row in guard_writes
                         if row["frame"] == "2245" and
                         row["pc"] == "017882"]
    require([row["value_before"] for row in child_allocations] ==
            ["40", "3f", "3e", "3d"],
            "Coffee Shop obstacle child allocation order drift")
    damage = [row for row in writes if row["frame"] == "2804" and
              row["pc"] in {"01d590", "01d598", "01d4aa"}]
    require([row["pc"] for row in damage] ==
            ["01d590", "01d598", "01d4aa", "01d4aa"] and
            damage[0]["health_before"] == "0" and
            damage[1]["health_before"] == "-25" and
            damage[2]["health_before"] == "-1" and
            damage[2]["a1"] == "ffb380" and
            damage[2]["a3"] == "11af76",
            "Coffee Shop obstacle damage transition drift")
    obstacle_break_rng = [row for row in rng_calls
                          if row["frame"] == "2805" and
                          row["a6"] == "ffb380"]
    require(len(obstacle_break_rng) == 1 and
            obstacle_break_rng[0]["entry_pc"] == "017c5e" and
            obstacle_break_rng[0]["rng_before"] == "441b" and
            obstacle_break_rng[0]["state"] == "0402" and
            obstacle_break_rng[0]["substate"] == "0000",
            "Coffee Shop obstacle break RNG transaction drift")
    audio = json.loads(GLOBAL_AUDIO.read_text(encoding="ascii"))
    obstacle_audio = [group for group in audio["trigger_groups"]
                      if group["id"] ==
                      "global-audio-ffb380-003a8e-0142"]
    require(len(obstacle_audio) == 1 and
            obstacle_audio[0]["command"] == "0x0142" and
            obstacle_audio[0]["argument_variants"] ==
            [["00000142", "00001b00", "00000000"]] and
            obstacle_audio[0]["transition_guard"]["contexts"][0]
                ["source_call"]["address"] == "0x06df42",
            "Coffee Shop obstacle break audio ownership drift")
    require(int(baseline_result["obstacle_transition_suppressed_writes"]) == 0 and
            int(mutant_result["obstacle_transition_suppressed_writes"]) == 18 and
            int(baseline_result["final_route"]) == 2 and
            int(mutant_result["final_route"]) == 4 and
            identity_a["coffee_shop_scene_actors.tsv"] !=
            identity_mutant["coffee_shop_scene_actors.tsv"] and
            identity_a["coffee_shop_scene_frames.tsv"] !=
            identity_mutant["coffee_shop_scene_frames.tsv"] and
            identity_a["dispatches.tsv"] != identity_mutant["dispatches.tsv"],
            "Coffee Shop obstacle transition suppression did not discriminate")
    physics_entry = [row for row in trace if row["frame"] == "2815" and
                     row["pc"] == "06e09a"]
    require(len(physics_entry) == 1 and
            physics_entry[0]["state"] == "0404" and
            physics_entry[0]["field4f"] == "01" and
            physics_entry[0]["field60"] == "04630000" and
            physics_entry[0]["field64"] == "04630000" and
            physics_entry[0]["field68"] == "01730002" and
            physics_entry[0]["field6c"] == "01430000" and
            physics_entry[0]["field30"] == "0500" and
            physics_entry[0]["field32"] == "0400" and
            physics_entry[0]["field34"] == "0600" and
            physics_entry[0]["field36"] == "0500",
            "Coffee Shop obstacle physics initialization drift")
    physics_visible = [row for row in obstacle
                       if 2815 <= int(row["frame"]) <= 2818]
    require([(int(row["frame"]), row["state"], row["x_fp"], row["y_fp"],
              row["animation_record"]) for row in physics_visible] == [
                (2815, "0402", "04630000", "01430000", "0006e15a"),
                (2816, "0404", "04630000", "01730000", "0006e16e"),
                (2817, "0404", "04670000", "01480000", "0006e182"),
                (2818, "0404", "046d0000", "017e0000", "0006e16e"),
              ], "Coffee Shop obstacle alternating projection drift")
    scene_record = program[0x15C168:0x15C178]
    require(scene_record.hex() == "02b00463014300040a000000000e0000",
            "Coffee Shop obstacle scene record drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "capture_identity": {
            "completion_a": identity_a, "completion_b": identity_b,
            "byte_identical": True, "transition_suppression": identity_mutant,
        },
        "source_scene_record": {
            "address": "0x15c168", "bytes": scene_record.hex(),
            "sha256": hashlib.sha256(scene_record).hexdigest(),
            "camera_threshold_u16": 688, "x_s16": 1123,
            "y_s16": 323, "record_type_u16": 4,
            "class_u8": 10, "facing_u8": 0,
            "field_0c_u8": 0, "field_0e_u8": 14,
        },
        "spawn": {
            "source_routine": "0x01bece..0x01bf4e",
            "source_routine_sha256": hashlib.sha256(
                opcodes[0x01BECE:0x01BF4E]).hexdigest(),
            "guard": "nonnegative record threshold 688 <= unsigned camera bound A5+0x278, route/lane record filters pass, and the record-20 pool allocation succeeds",
            "writer_pcs": ["0x01bf1e", "0x01bf22", "0x01bf28",
                           "0x01bf2e", "0x01bf34", "0x01bf3a",
                           "0x01bf40"],
            "source_frame": 2245, "first_visible_frame": 2246,
            "slot": "0xffb380", "scheduler": "record type 20 at 0x01bc38",
            "camera_sample_order": {
                "source_rule": "scene-record guard samples A5+0x278 before the same source frame's player/camera controller write",
                "native_rule": "scheduler guard uses camera_x_previous; camera_x_position is the post-player sample for the next source frame",
                "mutation_control": "using post-player camera_x_position allocates 0xffb380 one frame early (native 2245 instead of source 2246)",
            },
        },
        "initializer": {
            "dispatch_entry": "0x06de92",
            "source_routine": "0x06de92..0x06e136",
            "source_routine_sha256": hashlib.sha256(
                opcodes[0x06DE92:0x06E136]).hexdigest(),
            "guard": "unsigned record-36 free count at 0xffee8f >= 4",
            "initial_free_count_u8": 64,
            "writes": {
                "state_u16": "0x0200", "table_set": "0x06e210",
                "object_priority_u16": "0x8000", "field64_u8": "0x1d",
                "z_s16": "copy y_s16", "health_s16": 0,
                "substate_u16": 0, "facing_u8": 0,
            },
            "child_allocation": {
                "record_type_u8": 36, "class_u8": 5,
                "count": 4, "variant_order_u8": [3, 2, 1, 0],
                "source_slots_in_allocation_order":
                    ["0xffe240", "0xffe200", "0xffe1c0", "0xffe180"],
                "parent_backlink_field": "child+0x26:u16",
                "parent_child_array": "parent+0x78..0x7e:u16",
                "free_count_before_after": [64, 60],
            },
            "animation_selector_u8": 0,
            "animation_record": "0x06e136",
        },
        "state_program": {
            "state_dispatch_table": "0x06de9e offsets for 0x0000,0x0200,0x0400,0x0600",
            "state_0200": {
                "calls_in_order": ["0x016536 animation", "0x01d87a collision",
                                   "0x06b2e2 class body", "0x0167ac submit"],
                "damage_guard": "current player attack record 0x11af76 subtracts 25 from signed health 0, clamps to -1, and writer 0x01d4aa sets state/substate 0x0400/0x0000",
                "player_trigger": {"source_slot": "0xff8380",
                                   "state_u16": "0x0200",
                                   "substate_u16": "0x0802",
                                   "animation_record": "0x15fd40",
                                   "attack_record": "0x11af76",
                                   "button1_button2_edge_frame": 2790,
                                   "edge_to_damage_ticks_u8": 14,
                                   "x_s16": 1091, "z_s16": 320,
                                   "damage_s16": 25},
                "source_frame": 2804,
            },
            "state_0400": {
                "entry": "increment low state byte to 0x0402, set timer high byte to 8, bind selector 1 record 0x06e14a, and submit",
                "presentation_rng_transaction": {
                    "caller": "0x06df3c", "callee": "0x0bc692",
                    "rng_entry": "0x017c5e", "rng_call_pc": "0x0bc6b4",
                    "calls_u8": 1, "seed_before_u16": "0x441b",
                    "seed_after_u16": "0xcce7", "selector_mask_u16": "0x001f",
                    "owner": "source-owned obstacle-break presentation transaction",
                },
                "audio_transaction": {
                    "caller": "0x06df42", "callee": "0x002630",
                    "shared_wrapper_return": "0x003a8e",
                    "command_u16": "0x0142",
                    "arguments_u32": ["0x00000142", "0x00001b00",
                                      "0x00000000"],
                    "semantic_sound_name": "UNKNOWN",
                },
                "side_effect_order": [
                    "write state 0x0402",
                    "0x0bc692 presentation transaction consumes one shared RNG value",
                    "0x002630 dispatches command 0x0142",
                    "write timer high byte 8",
                    "bind selector 1 record 0x06e14a",
                ],
                "timer_high_byte_u8": 8,
                "timer_guard": "decrement high byte of actor+0x2a while nonzero; after zero require negative animation branch",
                "next_state": "0x0404",
            },
            "state_0404": {
                "initialization": "selectors 2 and 3 seed two alternating animation/position records plus signed velocity and acceleration fields",
                "transition_initialization_order": {
                    "source_update_frame": 2815,
                    "first_visible_frame": 2816,
                    "rule": "after the state-0x0402 timer is zero and the animation branch is negative, increment substate to 0x0404, call 0x06e010 and 0x06e0b2 in the same actor update, then submit",
                    "fixed_frame_delay_forbidden": True,
                },
                "channel_seeds": {
                    "primary": {"animation_selector_u8": 2,
                                "animation_record": "0x06e16e",
                                "fp60_u32": "0x04630000",
                                "fp68_u32": "0x01730002"},
                    "alternate": {"animation_selector_u8": 3,
                                  "animation_record": "0x06e182",
                                  "fp64_u32": "0x04630000",
                                  "fp6c_u32": "0x01430000"},
                    "source_block": "0x06e010..0x06e0b0",
                },
                "position_select": "(u8(A5+0x19)+D7)&1 selects the first or second record",
                "visible_projection": "0x06e0b2 copies only the selected channel x/y high words plus its animation, assembly, timer, branch and selector identity into the visible actor fields",
                "selection_witness": [
                    {"frame": 2816, "channel": "primary", "x_s16": 1123,
                     "y_s16": 371, "animation_record": "0x06e16e"},
                    {"frame": 2817, "channel": "alternate", "x_s16": 1127,
                     "y_s16": 328, "animation_record": "0x06e182"},
                    {"frame": 2818, "channel": "primary", "x_s16": 1133,
                     "y_s16": 382, "animation_record": "0x06e16e"},
                ],
                "arithmetic": [
                    "when flag bit0 is clear: fp60 += s16(field30)<<8; fp68 += s16(field34)<<8; field34 += s16(field3c)",
                    "when flag bit1 is clear: fp64 += s16(field32)<<8; fp6c += s16(field36)<<8; field36 += s16(field3e)",
                    "set flag bit0 when u16(fp68.high) < u16(parent reference field18); set bit1 by the same guard for fp6c",
                ],
                "initial_fields_s16": {"field30": 1280, "field34": 1536,
                                       "field38": 0, "field3c": -128,
                                       "field32": 1024, "field36": 1280,
                                       "field3a": 0, "field3e": -128},
                "direction_control": {"field": "actor+0x4f:u8",
                                      "source_value_at_entry_u8": 1,
                                      "presentation_facing_field": "actor+0x0f:u8",
                                      "presentation_facing_at_entry_u8": 0,
                                      "rule": "only when actor+0x4f is zero negate field30, field38, field32, and field3a; actor+0x0f must not control trajectory sign"},
                "completion_guard": "both flag bits set",
                "next_state": "0x0604",
            },
            "state_0604": {"release": "0x017706 fixed-pool release"},
        },
        "collision_damage": {
            "player_attack_record": {
                "address": "0x11af76", "x_center_s8": 0,
                "y_center_s8": 48, "x_half_u8": 88, "y_half_u8": 48,
                "z_center_s8": 0, "z_half_u8": 40,
                "hit_value_u8": 3, "knockback_mode_s8": 1,
                "damage_s16": 25,
            },
            "obstacle_hurt_record": {
                "address": "0x06e21c", "x_center_s8": 0,
                "y_center_s8": 64, "x_half_u8": 16, "y_half_u8": 64,
                "z_center_s8": 0, "z_half_u8": 6,
            },
            "overlap": "strict per-axis rectangle overlap using the sum of player-attack and obstacle-hurt half extents",
            "health_arithmetic": "s16(0-25)=-25, then source KO clamp writes -1",
            "state_writer": "0x01d4aa writes 0x0400:0x0000",
        },
        "presentation": {
            "selector_table": "0x06e12c", "records": [animation_record(a)
                for a in (0x06E136, 0x06E14A, 0x06E15A,
                          0x06E16E, 0x06E182)],
            "observed_records": sorted({f"0x{row['animation_record']}"
                                        for row in obstacle}),
        },
        "child_presentation": {
            "class_u8": 5, "record_type_u8": 36,
            "dispatch_entry": "0x09bb66",
            "dispatch_table": {
                "address": "0x09bb72", "offsets_u16": [8, 48, 82, 82],
                "state_targets": ["0x09bb7a", "0x09bba2",
                                  "0x09bbc4", "0x09bbc4"],
                "source_sha256": hashlib.sha256(
                    opcodes[0x09BB66:0x09BBE4]).hexdigest(),
            },
            "variant_sequences": {
                "0": [animation_record(a) for a in
                      range(0x09BBF0, 0x09BC40, 0x10)],
                "1": [animation_record(a) for a in
                      range(0x09BC44, 0x09BCC4, 0x10)],
                "2": [animation_record(a) for a in
                      range(0x09BCC8, 0x09BD28, 0x10)],
                "3": [animation_record(a) for a in
                      range(0x09BD2C, 0x09BD8C, 0x10)],
            },
            "release_record": animation_record(0x09BD90),
            "state_program": {
                "state_0000": {
                    "routine": "0x09bb7a..0x09bba2",
                    "writes": ["state += 2", "object_priority=0x8000",
                               "x=parent.x", "y=parent.y"],
                    "variant_selector": "child+0x03:u8",
                    "animation_entry": "0x016518",
                },
                "state_0200": {
                    "routine": "0x09bba2..0x09bbc4",
                    "guard": "u8(parent+0x04) >= 4",
                    "guard_false": "advance current animation at 0x016536",
                    "guard_true": "state += 2 and bind selector 4 release record at 0x016518",
                },
                "state_0400": {
                    "routine": "0x09bbc4..0x09bbe4",
                    "guard": "current animation branch is negative",
                    "writes": "scan four parent+0x78..0x7e u16 child slots and clear the matching child pointer",
                    "release": "0x01788c fixed-pool release",
                },
                "state_0600_alias": "dispatch offset aliases state 0x0400 target 0x09bbc4",
            },
        },
        "lifetimes": {
            "parent": {"source_slot": "0xffb380", "first_frame": 2246,
                       "last_frame": 2848, "rows": 603},
            "children": {"first_frame": 2246, "last_frame": 2806,
                         "count": 4, "rows": 2244},
        },
        "transition_suppression": {
            "writer_pc": "0x01d4aa", "suppressed_writes": 18,
            "baseline_final_route": 2, "mutant_final_route": 4,
            "actor_population_difference": True,
            "route_difference": True, "audio_difference": True,
            "rng_difference": True,
        },
        "fixed_frame_substitute_forbidden": True,
    }


def compact_runs(samples: list[dict[str, str]]) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for row in samples:
        key = (int(row["route"]), int(row["bound_x"]), int(row["bound_z"]))
        frame = int(row["frame"])
        if runs and tuple(runs[-1][name] for name in
                          ("route", "bound_x", "bound_z")) == key and \
                runs[-1]["last_frame"] + 1 == frame:
            runs[-1]["last_frame"] = frame
            runs[-1]["frames"] += 1
        else:
            runs.append({"first_frame": frame, "last_frame": frame,
                         "frames": 1, "route": key[0],
                         "bound_x": key[1], "bound_z": key[2]})
    return runs


def terrain_records(write_sets: list[list[dict[str, str]]], program: bytes) -> list[dict[str, object]]:
    observed: dict[str, dict[str, object]] = {}
    for capture_index, capture in enumerate(write_sets):
        counts = Counter((row["a4"], row["a4_bytes"], row["pc"])
                         for row in capture
                         if row["pc"] in ("0b1c08", "0b1c68"))
        for (address, record_bytes, pc), count in counts.items():
            key = f"0x{address}"
            item = observed.setdefault(key, {
                "address": key, "record_bytes": record_bytes,
                "baseline_calls": {"0x0b1c08": 0, "0x0b1c68": 0},
                "perturbed_calls": {"0x0b1c08": 0, "0x0b1c68": 0},
            })
            target = "baseline_calls" if capture_index == 0 else "perturbed_calls"
            item[target][f"0x{pc}"] += count
    require(set(observed) == set(TERRAIN_RECORDS),
            "route-reachable terrain record set drift")
    for address, expected in TERRAIN_RECORDS.items():
        item = observed[address]
        require(item["record_bytes"] == expected,
                f"{address}: captured terrain bytes drift")
        offset = int(address, 16)
        require(program[offset:offset + 8].hex() == expected,
                f"{address}: source terrain bytes drift")
        item["source_program_match"] = True
        item["classification"] = "SOURCE_CLOSED"
    return [observed[key] for key in sorted(observed)]


def type20_instances(route: dict[str, object], body_sets: list[list[dict[str, str]]],
                     opcodes: bytes) -> list[dict[str, object]]:
    archetypes = {(item["class"], item["type"]): item
                  for item in route["actor_archetypes"]}
    output = []
    for class_name, (start, end) in TYPE20_ROUTINES.items():
        actor = archetypes[(class_name, 20)]
        instance = actor["actor_slots_and_classes"][0]
        first, last = instance["life"]
        slot = instance["slot"].replace("0x", "")
        writer_sets = []
        for capture in body_sets:
            pcs = Counter(f"0x{row['pc']}" for row in capture
                          if row["slot"] == slot and first <= int(row["frame"]) <= last)
            writer_sets.append(dict(sorted(pcs.items())))
        output.append({
            "class": class_name, "type": 20, "slot": instance["slot"],
            "source_frame_range": [first, last],
            "scheduler_pool_type": 20,
            "dispatch_entry": f"0x{start:06x}",
            "bounded_source_block": f"0x{start:06x}..0x{end:06x}",
            "source_block_sha256": hashlib.sha256(opcodes[start:end]).hexdigest(),
            "state_transitions": actor["state_transitions"],
            "animation_and_assembly_identities": actor["animation_and_assembly_identities"],
            "baseline_writer_pcs": writer_sets[0],
            "perturbed_writer_pcs": writer_sets[1],
            "navigation_role": "SOURCE_CLOSED",
            "complete_actor_authority": (
                "PARTIAL; damage, destruction, pickup, hazard and presentation edges "
                "remain assigned to their existing ORACLE-11 authority families"),
        })
    return output


def terrain_interpreter_contract(opcodes: bytes, program: bytes,
                                 terrain_map: bytes) -> dict[str, object]:
    require(len(terrain_map) == 0x4000,
            "Coffee Shop terrain-map capture size drift")
    selector_bytes = terrain_map[2::4]
    require(len(selector_bytes) == 0x1000,
            "Coffee Shop terrain selector projection size drift")
    map_selectors = sorted({value & 0xfc for value in selector_bytes})
    require(map_selectors == [0, 4, 20, 24, 56],
            "Coffee Shop full terrain selector set drift")
    def cell_offset(x: int, z: int) -> int:
        inverted_z = (~z) & 0xffff
        return (((inverted_z & 0x0300) << 4) +
                ((inverted_z & 0x00f0) >> 2) + ((x << 2) & 0x0fc0))
    first_segment_selectors = sorted({
        terrain_map[cell_offset(x, z) + 2] & 0xfc
        for x in range(640, 1361) for z in range(272, 401)
    })
    require(first_segment_selectors == [0, 24, 56],
            "Coffee Shop bounded terrain selector set drift")
    grid_x_min, grid_x_max = 640, 1360
    grid_z_min, grid_z_max = 272, 400
    grid_tile = 16
    grid_width = ((grid_x_max - grid_x_min) // grid_tile) + 1
    grid_height = ((grid_z_max - grid_z_min) // grid_tile) + 1
    selector_codes = {0: 0, 24: 1, 56: 2}
    grid_selectors = [
        terrain_map[cell_offset(x, z) + 2] & 0xfc
        for z in range(grid_z_min, grid_z_max + 1, grid_tile)
        for x in range(grid_x_min, grid_x_max + 1, grid_tile)
    ]
    require(len(grid_selectors) == grid_width * grid_height and
            sorted(set(grid_selectors)) == first_segment_selectors,
            "Coffee Shop bounded terrain grid drift")
    packed_grid = bytearray((len(grid_selectors) + 3) // 4)
    for index, selector in enumerate(grid_selectors):
        packed_grid[index >> 2] |= selector_codes[selector] << ((index & 3) * 2)
    implementation_selectors = sorted(set(map_selectors) |
                                      {0, 8, 56, 96, 100, 164})
    implementation_records = []
    for selector in implementation_selectors:
        address = 0x0B20C6 + 2 * selector
        implementation_records.append({
            "selector_u8": selector,
            "address": f"0x{address:06x}",
            "record_bytes": program[address:address + 8].hex(),
        })
    require([row["record_bytes"] for row in implementation_records] == [
        "0080808080808080", "0200808010100080",
        "0202808010100080", "020080801010ff80",
        "020280801010ff80", "0202808010080080",
        "0604020100008080", "0604020100088080",
        "0402020100088080"], "Coffee Shop implementation records drift")
    fields = [
        {"offset": 0, "name": "kind", "type": "u8",
         "rule": "even byte offset into 0x0b1c0a handler table"},
        {"offset": 1, "name": "branch_selector", "type": "u8",
         "rule": "byte offset into the selected kind table; bit index is selector >> 1 when nonnegative"},
        {"offset": 2, "name": "orientation", "type": "u8",
         "rule": "kind-4/kind-6 axis orientation selector; kind-2 does not read it"},
        {"offset": 3, "name": "shift", "type": "u8",
         "rule": "variable word shift count for kind-4/kind-6"},
        {"offset": 4, "name": "x_parameter", "type": "u8_or_s8_by_kind",
         "rule": "zero-extended for kind-2/kind-4; sign-extended for kind-6"},
        {"offset": 5, "name": "z_parameter", "type": "u8_or_s8_by_kind",
         "rule": "zero-extended for kind-2/kind-4; sign-extended for kind-6"},
    ]
    handlers = {
        0: {
            "entry": "0x0b1c14", "parameter_signedness": "none",
            "movement_rule": "no position write",
        },
        2: {
            "entry": "0x0b1c16",
            "selected_entries": {"0": "0x0b1c38", "2": "0x0b1c54"},
            "parameter_signedness": "fields 4 and 5 are u8",
            "movement_rule": (
                "branch 0 uses remainder=world_z&15 and adds positive "
                "u8(field5)-remainder to world_z; branch 2 uses "
                "remainder=(~world_z)&15 and subtracts positive "
                "u8(field5)-remainder from world_z; either response clears "
                "z_velocity and sets response=1"),
        },
        4: {
            "entry": "0x0b1cac", "selected_entry": "0x0b1d0e",
            "parameter_signedness": "fields 3, 4 and 5 are u8",
            "movement_rule": (
                "x_remainder=(orientation==2?world_x:~world_x)&15; "
                "candidate=(x_remainder>>shift)+u8(field5)+1; "
                "z_remainder=(~world_z)&15; penetration=candidate-z_remainder; "
                "if penetration>0 then world_z-=penetration, z_velocity=0, response=1"),
        },
        6: {
            "entry": "0x0b1dc0", "selected_entry": "0x0b1e9c",
            "parameter_signedness": "field 3 is u8; fields 4 and 5 are s8",
            "movement_rule": (
                "z_remainder=(orientation==1?world_z:~world_z)&15; "
                "slope=z_remainder-s8(field5); if slope<0 then "
                "world_x-=((world_x&15)+1), x_velocity=0, set retry selector 0xff, "
                "and restart selection; "
                "otherwise candidate=slope<<shift; x_remainder=world_x&15; "
                "if x_remainder>=candidate then world_x-=(x_remainder-candidate+1), "
                "x_velocity=0, response=1"),
        },
    }
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "six_fields": fields,
        "control_bytes": [
            {"offset": 6, "name": "retry_selector", "type": "u8",
             "rule": "copied to A5-0x6144; 0xff repeats record selection"},
            {"offset": 7, "name": "reserved", "type": "u8",
             "rule": "not read by 0x0b1baa..0x0b1c08 or the reachable handlers"},
        ],
        "selection": {
            "entry": "0x0b208c", "world_reads": ["actor+0x10:s16", "actor+0x18:s16"],
            "cell_address": (
                "0x904000 + (((~world_z)&0x0300)<<4) + "
                "(((~world_z)&0x00f0)>>2) + ((world_x<<2)&0x0fc0)"),
            "cell_selector": "u8(cell+2) & 0xfc",
            "record_address": "0x0b20c6 + 2 * (u8(cell+2) & 0xfc)",
            "collision_flags_clear_first": "actor+0x5d &= 0xf0",
            "captured_first_segment_map": {
                "base": "0x904000", "bytes": len(terrain_map),
                "sha256": hashlib.sha256(terrain_map).hexdigest(),
                "selector_bytes": len(selector_bytes),
                "selector_sha256": hashlib.sha256(selector_bytes).hexdigest(),
                "selector_bytes_hex": selector_bytes.hex(),
                "classification": "SOURCE_DERIVED_CONTENT_DATA",
            },
            "bounded_packed_grid": {
                "classification": "SOURCE_DERIVED_CONTENT_DATA",
                "world_x_inclusive": [grid_x_min, grid_x_max],
                "world_z_inclusive": [grid_z_min, grid_z_max],
                "tile_size": grid_tile,
                "width": grid_width,
                "height": grid_height,
                "cell_count": len(grid_selectors),
                "bits_per_cell": 2,
                "selector_code_u8": [0, 24, 56],
                "packed_bytes": len(packed_grid),
                "packed_sha256": hashlib.sha256(packed_grid).hexdigest(),
                "packed_bytes_hex": packed_grid.hex(),
                "derivation": (
                    "row-major source cells sampled at each 16-pixel tile origin; "
                    "four 2-bit selector codes packed least-significant code first"),
            },
        },
        "handlers": {str(key): value for key, value in handlers.items()},
        "implementation_records": implementation_records,
        "first_segment_geometry_universe": {
            "world_x_inclusive": [640, 1360],
            "world_z_inclusive": [272, 400],
            "selectors_u8": first_segment_selectors,
        },
        "scheduler_order": (
            "player movement -> global bounds -> actor/obstacle response -> "
            "terrain resolver -> camera/route controller -> world-to-plane submission"),
        "source_blocks": {
            "dispatcher_sha256": hashlib.sha256(
                opcodes[0x0B1BAA:0x0B1C16]).hexdigest(),
            "kind2_sha256": hashlib.sha256(
                opcodes[0x0B1C16:0x0B1CAC]).hexdigest(),
            "kind4_sha256": hashlib.sha256(
                opcodes[0x0B1CAC:0x0B1DC0]).hexdigest(),
            "kind6_sha256": hashlib.sha256(
                opcodes[0x0B1DC0:0x0B1F4C]).hexdigest(),
            "selector_sha256": hashlib.sha256(
                opcodes[0x0B208C:0x0B20C6]).hexdigest(),
            "cell_address_sha256": hashlib.sha256(
                opcodes[0x0B2672:0x0B269E]).hexdigest(),
        },
    }


def obstacle_implementation_contract(program: bytes, opcodes: bytes,
                                     resolve_rows: list[dict[str, str]]) -> dict[str, object]:
    animation = 0x06E136
    table_set = 0x06E210
    attack_relative = int.from_bytes(program[table_set + 2:table_set + 4],
                                     "big", signed=True)
    selector = program[animation + 9]
    box_address = table_set + attack_relative + selector * 8
    blob = program[box_address:box_address + 8]
    box = {
        "address": f"0x{box_address:06x}",
        "x_center_s8": int.from_bytes(blob[0:1], "big", signed=True),
        "y_center_s8": int.from_bytes(blob[1:2], "big", signed=True),
        "x_half_u8": blob[2], "y_half_u8": blob[3],
        "z_center_s8": int.from_bytes(blob[4:5], "big", signed=True),
        "z_half_u8": blob[5], "flags_u16": int.from_bytes(blob[6:8], "big"),
    }
    require(attack_relative == 0x14 and selector == 1 and box == {
        "address": "0x06e22c", "x_center_s8": 0, "y_center_s8": 0,
        "x_half_u8": 32, "y_half_u8": 127, "z_center_s8": 0,
        "z_half_u8": 6, "flags_u16": 0xff00,
    }, "Coffee Shop obstacle source box drift")
    relevant = [row for row in resolve_rows
                if row["pc"] == "01d986" and row["field"] == "x" and
                row["a1"] == "ff8380" and row["a6"] == "ffb380"]
    require(len(relevant) == 745 and
            {(int(row["half_x"]), int(row["half_z"]), int(row["sign_bits"]))
             for row in relevant} == {(32, 6, 0)} and
            {int(row["new_value"]) for row in relevant} == {1091},
            "Coffee Shop minimum-penetration operands drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "source_actor": {
            "slot": "0xffb380", "class": "0x0a", "type": 20,
            "state_u16": 0x0200, "substate_u16": 0,
            "position_s16": {"x": 1123, "y": 323, "z": 323},
            "facing_u8": 0,
            "animation_record": "0x06e136", "table_set": "0x06e210",
            "assembly": "0x06e196", "hurt_selector_u8": 1,
            "attack_selector_u8": selector,
        },
        "player_geometry": {
            "classification": "SOURCE_POINT_PROBE",
            "x": "player+0x10:s16", "z": "player+0x18:s16",
            "box": None,
            "rule": "0x01db8a reads no player rectangle; substituting a player hurt box is forbidden",
        },
        "obstacle_box": box,
        "overlap_guard": (
            "abs((obstacle_x + signed x_center)-player_x) < x_half AND "
            "abs((obstacle_z + signed z_center)-player_z) < z_half"),
        "minimum_penetration": {
            "x": "x_half-abs_x; negate when obstacle center delta was negative",
            "z": "z_half-abs_z; negate when obstacle center delta was negative",
            "axis_guard": "resolve z only when unsigned z_penetration < unsigned x_penetration; otherwise resolve x",
            "x_write": "player_x -= signed x_penetration at 0x01d980 (tap PC 0x01d986)",
            "z_write": "player_z -= signed z_penetration at 0x01d994 (tap PC 0x01d998)",
            "velocity_writes": ["player+0x12=0", "player+0x1a=0"],
            "contact_bits": "x sets bit 2/3; z sets bit 0/1 in player+0x5d from penetration sign",
        },
        "dynamic_control": {
            "rows": len(relevant), "half_x": 32, "half_z": 6,
            "right_edge": 1091,
            "capture_sha256": hashlib.sha256(canonical(relevant)).hexdigest(),
        },
        "source_blocks": {
            "overlap_sha256": hashlib.sha256(
                opcodes[0x01DB8A:0x01DC10]).hexdigest(),
            "response_sha256": hashlib.sha256(
                opcodes[0x01D930:0x01D99A]).hexdigest(),
        },
    }


def camera_implementation_contract(sample_rows: list[dict[str, str]],
                                   bound_rows: list[dict[str, str]],
                                   opcodes: bytes) -> dict[str, object]:
    coffee_frames = rows(OBSTACLE_A / "coffee_shop_scene_frames.tsv")
    require(digest(OBSTACLE_A / "coffee_shop_scene_frames.tsv") ==
            digest(OBSTACLE_B / "coffee_shop_scene_frames.tsv"),
            "Coffee Shop first-control camera captures differ")
    coffee_by_frame = {int(row["frame"]): row for row in coffee_frames}
    first_control = [{
        "source_frame_u16": frame,
        "route_state_s16": int(coffee_by_frame[frame]["route_state"]),
        "player_x_s16": int(coffee_by_frame[frame]["player_x_fp"], 16) >> 16,
        "camera_x_s16": int(coffee_by_frame[frame]["camera_x"]),
        "camera_target_x_s16": int(coffee_by_frame[frame]["camera_target_x"]),
    } for frame in (2237, 2238, 2239)]
    require(first_control == [
        {"source_frame_u16": 2237, "route_state_s16": 2,
         "player_x_s16": 944, "camera_x_s16": 640,
         "camera_target_x_s16": 640},
        {"source_frame_u16": 2238, "route_state_s16": 4,
         "player_x_s16": 944, "camera_x_s16": 648,
         "camera_target_x_s16": 648},
        {"source_frame_u16": 2239, "route_state_s16": 4,
         "player_x_s16": 944, "camera_x_s16": 655,
         "camera_target_x_s16": 655}],
        "Coffee Shop first-control camera chronology drift")
    by_frame = {int(row["frame"]): row for row in sample_rows}
    require(len(sample_rows) == 1801 and set(by_frame) == set(range(3400, 5201)),
            "corrective camera sample window drift")
    checkpoints = []
    for frame in (3572, 3714, 3792, 4992, 4993, 5016):
        row = by_frame[frame]
        checkpoints.append({
            "frame": frame, "route": int(row["route"]),
            "player_x": int(row["player_x"]), "player_z": int(row["player_z"]),
            "position_x": int(row["cam_x_position"]),
            "target_x": int(row["cam_x_target"]),
            "x_lower": int(row["cam_x_min"]),
            "x_upper": int(row["cam_x_max"]),
            "global_x": int(row["global_cam_x"]),
            "scroll2_x": int(row["scroll2_x"]),
        })
    required_writes = {
        (3792, "x_lower", "028942", 0x340),
        (3792, "x_upper", "028958", 0x340),
        (4992, "x_upper", "02898a", 0x3f0),
        (4993, "x_lower", "0289ae", 0x344),
    }
    observed = {(int(row["frame"]), row["field"], row["pc"],
                 int(row["write_data"], 16) & 0xffff)
                for row in bound_rows}
    require(required_writes <= observed, "Coffee Shop camera guard writers drift")
    guard_rows = {int(row["frame"]): row for row in sample_rows}
    require(all(int(guard_rows[frame]["guard_threshold_byte"]) == 1
                for frame in (3792, 3793, 4992, 4993)) and
            int(guard_rows[3792]["coffee_countdown"]) == 1200 and
            int(guard_rows[3793]["coffee_countdown"]) == 1199 and
            int(guard_rows[4992]["coffee_countdown"]) == 0 and
            int(guard_rows[4993]["coffee_phase"]) == 4,
            "Coffee Shop unlock guard operands drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "record": {
            "source_base": "0xff8268",
            "x_previous": "+0x08:s16", "x_position": "+0x10:s16",
            "z_position": "+0x14:s16", "x_target": "+0x20:s16",
            "z_target": "+0x24:s16", "x_target_previous": "+0x28:s16",
            "z_target_previous": "+0x2c:s16", "z_upper": "+0x30:s16",
            "z_lower": "+0x32:s16", "x_lower": "+0x34:s16",
            "x_upper": "+0x36:s16",
        },
        "initialization": {
            "entry": "0x0b04bc", "override_guard": "u8(A5+0x1b0) != 0",
            "override_reads": ["camera+0x10:s16", "camera+0x14:s16"],
            "writes": ["x position/target/history from D0", "z position/target/history from D1"],
            "route_table_bounds": "0x0b0526 indexes four signed bounds by u16(A5+0x1e8)<<2",
            "first_control_chronology": first_control,
            "handoff_rule": "the route-2 to route-4 handoff consumes the first source camera controller update before the first route-4 frame is presented",
            "mutation_control": "skipping the handoff camera update leaves source frame 2238 at x=640 instead of x=648",
        },
        "player_follow_guard": {
            "enabled": "u8(A5+0x1af) != 0",
            "players": "three 0x100-byte records at A5+0x380, ascending slot order",
            "eligible": "active byte nonzero and player+0x54 != 0xfe",
            "x_extrema": "0x0b0c22 returns unsigned max/min actor+0x10",
            "z_extrema": "0x0b0c5e returns unsigned max/min actor+0x18",
        },
        "x_target_arithmetic": {
            "spread_guard": "unsigned(max_x-min_x) >= 0x40",
            "wide_target_delta": "((max_x+min_x)>>1)-x_target-0x00c0",
            "narrow_right_delta": "max_x-x_target-0x00e0",
            "narrow_left_delta": "min_x-x_target-0x00a0",
            "speed_quantization": "index=((abs(delta)+7)&0x00f8)>>2; speed=u16(table+index)&0x000f",
            "speed_table_u16": [0, 1, 1, 2, 3, 4, 5, 6, 7, 7,
                                  8, 8, 9, 9, 10, 10, 11, 11, 11, 11],
            "clamp_order": "apply signed delta to target, clamp upper at +0x36, then lower at +0x34",
            "commit_order": "target +0x20 -> position +0x10 -> A5+0x278 global bound -> A5+0x32 camera position",
        },
        "z_target_arithmetic": {
            "spread_guard": "unsigned(max_z-min_z) >= 0x20",
            "wide_target_delta": "((max_z+min_z)>>1)-z_target-0x0050",
            "narrow_upper_delta": "max_z-z_target-0x0060",
            "narrow_lower_delta": "min_z-z_target-0x0040",
            "step": "clamp absolute delta to 1",
            "clamp_order": "apply signed delta, clamp upper at +0x30, then lower at +0x32",
            "commit_order": "target +0x24 -> position +0x14 -> A5+0x34 camera z",
        },
        "coffee_shop_guard": {
            "controller_slot": "0xffd180", "controller_dispatch": "0x028860",
            "phase_dispatch": "u8(controller+0x06) indexes 0x028908",
            "phase0_lock_guard": "u16(A5+0x278) >= 0x0340",
            "phase0_writes": ["x_lower=0x0340", "x_upper=0x0340",
                              "controller+0x44=u16(A5-0x65e6)"],
            "phase2_unlock_guard": (
                "unsigned(u16(A5-0x65e6)-u16(controller+0x44)) >= "
                "(u8(A5+0x020e)<<4), OR controller+0x46 countdown reaches zero"),
            "captured_first_segment_operands": {
                "counter_u16": 0, "snapshot_u16": 0,
                "threshold_byte_u8": 1, "threshold_ticks": 16,
                "countdown_initial_u16": 1200,
                "countdown_tick_rule": "decrement once per controller update while phase is 2",
            },
            "phase2_writes": ["x_upper=0x03f0", "controller+0x06 += 2"],
            "phase4_follow": "x_lower=u16(A5+0x278) each tick; clamp at 0x03f0 before the next phase",
            "fixed_frame_authority": False,
        },
        "world_to_plane_order": {
            "rule": (
                "finish player/navigation, encounter camera-bound writes, and camera controller; "
                "then translate source scroll2 through the accepted strip origin and derive scroll3 "
                "through the accepted measured scroll2-to-scroll3 bridge; submit both VDP2 planes last"),
            "scroll2_relation_at_locks": "CPS scroll2_x = camera position x - 0x40",
            "raw_pattern_name_offset_forbidden": True,
            "accepted_bridge": "data/repair11_live_background_presentation.json",
        },
        "dynamic_checkpoints": checkpoints,
        "source_blocks": {
            "initializer_sha256": hashlib.sha256(
                opcodes[0x0B04BC:0x0B0526]).hexdigest(),
            "x_controller_sha256": hashlib.sha256(
                opcodes[0x0B0680:0x0B0786]).hexdigest(),
            "z_controller_sha256": hashlib.sha256(
                opcodes[0x0B0786:0x0B085C]).hexdigest(),
            "player_extrema_sha256": hashlib.sha256(
                opcodes[0x0B0C22:0x0B0C9A]).hexdigest(),
            "coffee_guard_sha256": hashlib.sha256(
                opcodes[0x028910:0x0289C6]).hexdigest(),
        },
    }


def camera_authority(route: dict[str, object], samples: list[dict[str, str]],
                     camera_rows: list[dict[str, str]], opcodes: bytes) -> dict[str, object]:
    writers = Counter((row["pc"], row["return0"], row["return1"], row["return2"])
                      for row in camera_rows if row["kind"] == "camera_target")
    source_writers = [{
        "pc": f"0x{pc}",
        "return_chain": [f"0x{r0}", f"0x{r1}", f"0x{r2}"],
        "count": count,
    } for (pc, r0, r1, r2), count in sorted(writers.items())]
    sample_by_frame = {int(row["frame"]): row for row in samples}
    locks = []
    for lock in route["camera_lock_runs"]:
        first, last = lock["first_frame"], lock["last_frame"]
        if first not in sample_by_frame or last not in sample_by_frame:
            continue
        before = sample_by_frame.get(first - 1, sample_by_frame[first])
        entry = sample_by_frame[first]
        exit_row = sample_by_frame[last]
        provenance = sorted({f"0x{row['pc']}" for row in camera_rows
                             if first <= int(row["frame"]) <= last})
        locks.append({
            "first_frame": first, "last_frame": last, "frames": lock["frames"],
            "route": int(entry["route"]), "scroll2_x": lock["scroll2_x"],
            "camera_target_at_entry": int(entry["camera_target"]),
            "camera_target_at_exit": int(exit_row["camera_target"]),
            "player_x_at_entry": int(entry["player_x"]),
            "player_x_at_exit": int(exit_row["player_x"]),
            "prior_scroll2_x": int(before["scroll2_x"]),
            "owning_writer_pcs": provenance,
            "classification": "SOURCE_CLOSED",
        })
    require(len(locks) == len(route["camera_lock_runs"]),
            "camera lock/unlock route edge coverage drift")
    return {
        "classification": "SOURCE_CLOSED",
        "camera_target_field": "0xff8032:u16",
        "primary_writer": "0x0b0706",
        "bounded_controller_block": "0x0b04ce..0x0b0862",
        "controller_block_sha256": hashlib.sha256(
            opcodes[0x0B04CE:0x0B0862]).hexdigest(),
        "source_writers_and_callers": source_writers,
        "camera_lock_and_unlock_runs": locks,
        "edge_guard_rule": (
            "retain the exact source camera-target writer and route-state transition; "
            "no x-only, kill-count, or fixed-frame substitute is admitted"),
        "orphan_camera_edges": 0,
    }


def build_report() -> dict[str, object]:
    identity_a = capture_identity(BASE_A)
    identity_b = capture_identity(BASE_B)
    identity_p = capture_identity(PERTURBED)
    corrective_a = corrective_identity(CORRECTIVE_A)
    corrective_b = corrective_identity(CORRECTIVE_B)
    require(identity_a["files"] == identity_b["files"],
            "navigation baseline completion captures differ")
    require(identity_a["mame_sha256"] == identity_b["mame_sha256"] ==
            identity_p["mame_sha256"], "MAME identity differs across navigation captures")
    result_a, result_b, result_p = (parse_result(path)
                                    for path in (BASE_A, BASE_B, PERTURBED))
    require(result_a == result_b and result_a["final_route"] == 4,
            "baseline navigation completion drift")
    require(result_p["final_route"] == 4,
            "directional navigation perturbation did not complete Round 1")
    require(identity_p["files"]["navigation_samples.tsv"] !=
            identity_a["files"]["navigation_samples.tsv"],
            "navigation perturbation did not discriminate")
    require(corrective_a["files"] == corrective_b["files"] and
            corrective_a["mame_sha256"] == corrective_b["mame_sha256"] ==
            identity_a["mame_sha256"] and
            corrective_a["nvram_baseline_sha256"] ==
            corrective_b["nvram_baseline_sha256"] ==
            identity_a["nvram_baseline_sha256"],
            "corrective navigation captures differ")

    base_samples = rows(BASE_A / "navigation_samples.tsv")
    perturbed_samples = rows(PERTURBED / "navigation_samples.tsv")
    base_writes = rows(BASE_A / "navigation_writes.tsv")
    perturbed_writes = rows(PERTURBED / "navigation_writes.tsv")
    base_bodies = rows(BASE_A / "navigation_body_writes.tsv")
    perturbed_bodies = rows(PERTURBED / "navigation_body_writes.tsv")
    base_camera = rows(BASE_A / "camera_writes.tsv")
    corrective_samples = rows(CORRECTIVE_A / "navigation_fields.tsv")
    corrective_resolves = rows(CORRECTIVE_A / "navigation_resolves.tsv")
    corrective_bounds = rows(CORRECTIVE_A / "camera_bound_writes.tsv")
    route = json.loads(ORACLE10.read_text(encoding="utf-8"))
    oracle08 = json.loads(ORACLE08.read_text(encoding="utf-8"))
    scheduler = json.loads(SCHEDULER.read_text(encoding="ascii"))
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()

    terrain = terrain_records([base_writes, perturbed_writes], program)
    terrain_map = (CORRECTIVE_A / "terrain_map.bin").read_bytes()
    terrain_contract = terrain_interpreter_contract(opcodes, program,
                                                    terrain_map)
    handler_entry = {0: "0x0b1c14", 2: "0x0b1c54",
                     4: "0x0b1d0e", 6: "0x0b1e9c"}
    for item in terrain:
        blob = bytes.fromhex(item["record_bytes"])
        kind = blob[0]
        parameter_type = "s8" if kind == 6 else "u8"
        item["decoded_six_fields"] = {
            "kind_u8": kind, "branch_selector_u8": blob[1],
            "orientation_u8": blob[2], "shift_u8": blob[3],
            f"x_parameter_{parameter_type}":
                int.from_bytes(blob[4:5], "big", signed=kind == 6),
            f"z_parameter_{parameter_type}":
                int.from_bytes(blob[5:6], "big", signed=kind == 6),
        }
        item["control_bytes"] = {
            "retry_selector_u8": blob[6], "reserved_u8": blob[7]}
        item["selected_handler"] = handler_entry[kind]
    type20 = type20_instances(route, [base_bodies, perturbed_bodies], opcodes)
    camera = camera_authority(route, base_samples, base_camera, opcodes)
    obstacle_contract = obstacle_implementation_contract(
        program, opcodes, corrective_resolves)
    obstacle_lifecycle = coffee_shop_obstacle_lifecycle(opcodes, program)
    camera_contract = camera_implementation_contract(
        corrective_samples, corrective_bounds, opcodes)
    counterfactual = next(item for item in route["counterfactual_authority_coverage"]
                          if item["authority_family"] ==
                          "round1-navigation-terrain-camera")
    require(counterfactual["status"] == "PASS" and
            all(item["completed_round1"] for item in
                counterfactual["outcomes"].values()),
            "route-wide navigation counterfactual coverage drift")
    require(scheduler["status"] == "SOURCE_CLOSED" and
            any(item["record_type"] == 20 and item["routine"] == "0x01bc38"
                for item in scheduler["frame_scheduler"]["full_order"]),
            "type-20 scheduler ownership drift")

    bound_runs = compact_runs(base_samples)
    bound_tuples = sorted({(int(row["bound_x"]), int(row["bound_z"]))
                           for row in base_samples + perturbed_samples})
    clamp_pcs = Counter(f"0x{row['pc']}" for row in base_writes + perturbed_writes
                        if row["pc"].startswith("01b0"))
    require({"0x01b030", "0x01b042"}.issubset(clamp_pcs),
            "route-wide global-bound clamp writers not discriminated")
    report = {
        "schema": "oracle11-round1-navigation-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "Round 1 player navigation, terrain, obstacles and camera bounds",
        "capture_identity": {
            "completion_a": identity_a, "completion_b": identity_b,
            "byte_identical": True, "perturbed_completion": identity_p,
            "baseline_result": result_a, "perturbed_result": result_p,
            "perturbation_completed_round1": True,
            "perturbation_discriminated_navigation": True,
            "corrective_implementation_fields_a": corrective_a,
            "corrective_implementation_fields_b": corrective_b,
            "corrective_byte_identical": True,
        },
        "coordinate_contract": {
            "world_x": "actor+0x10:s16", "world_y": "actor+0x14:s16",
            "world_z": "actor+0x18:s16",
            "up_world_z_delta_sign": 1, "down_world_z_delta_sign": -1,
            "screen_projection_owned_here": False,
        },
        "global_bounds": {
            "classification": "SOURCE_CLOSED",
            "source_routine": "0x01b000..0x01b05e",
            "source_routine_sha256": hashlib.sha256(
                opcodes[0x01B000:0x01B05E]).hexdigest(),
            "bound_x_field": "A5+0x278:s16", "bound_z_field": "A5+0x27c:s16",
            "x_min": "bound_x + 0x20", "x_max": "bound_x + 0x160",
            "z_min": "bound_z + 0x10", "z_max": "bound_z + 0x90",
            "writer_pcs": dict(sorted(clamp_pcs.items())),
            "observed_bound_tuples": [[x, z] for x, z in bound_tuples],
            "baseline_bound_runs": bound_runs,
            "orphan_bound_runs": 0,
        },
        "terrain_resolver": {
            "classification": "SOURCE_CLOSED",
            "source_block": "0x0b1baa..0x0b1c70",
            "source_block_sha256": hashlib.sha256(
                opcodes[0x0B1BAA:0x0B1C70]).hexdigest(),
            "position_sync_writer": "0x0b1c08",
            "constraint_response_writer": "0x0b1c68",
            "records": terrain, "route_reachable_record_count": len(terrain),
            "orphan_route_reachable_records": 0,
            "implementation_contract": terrain_contract,
        },
        "navigation_bodies": {
            "classification": "SOURCE_CLOSED",
            "scheduler": "record type 20 at 0x01bc38, fixed-pool ascending-slot order",
            "instances": type20, "route_reachable_class_type_pairs": 4,
            "orphan_navigation_bodies": 0,
            "scope_boundary": (
                "this closes geometry/navigation ownership only; destructible damage, "
                "pickup/hazard and presentation authority stay in their declared families"),
        },
        "obstacle_response": {
            "classification": "SOURCE_CLOSED",
            "source_block": "0x01d930..0x01d99a",
            "source_block_sha256": hashlib.sha256(
                opcodes[0x01D930:0x01D99A]).hexdigest(),
            "minimum_penetration_x_writer": "0x01d986",
            "coffee_shop_actor": "class 0x0a/type 20 at 0xffb380",
            "accepted_oracle08_removal_control": True,
            "shared_player_enemy_rectangle_rejected": True,
            "implementation_contract": obstacle_contract,
            "lifecycle_contract": obstacle_lifecycle,
        },
        "camera": {**camera, "implementation_contract": camera_contract},
        "counterfactuals": {
            "oracle08_directional_and_obstacle_controls":
                oracle08["boundary_counterfactuals"],
            "oracle10_route_wide": counterfactual,
            "oracle11_directional_perturbation": {
                "schedule": "post-frame-4200 Up/Down pulses layered on the completion route",
                "completed_round1": True,
                "navigation_samples_changed": True,
                "constraint_response_writer_observed": True,
            },
        },
        "closure": {
            "required_unknown": 0, "orphan_bound_runs": 0,
            "orphan_terrain_records": 0, "orphan_navigation_bodies": 0,
            "orphan_camera_edges": 0, "guessed_camera_guards": 0,
            "authored_fallbacks": 0,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED",
            "global_audio_load_release": "SOURCE_CLOSED",
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-round1-navigation-v1" and
            report["status"] == "SOURCE_CLOSED", "navigation status drift")
    capture = report["capture_identity"]
    require(capture["byte_identical"] is True and
            capture["perturbation_completed_round1"] is True and
            capture["perturbation_discriminated_navigation"] is True and
            capture["corrective_byte_identical"] is True and
            capture["corrective_implementation_fields_a"]["files"] ==
            capture["corrective_implementation_fields_b"]["files"],
            "navigation capture contract drift")
    bounds = report["global_bounds"]
    opcodes = OPCODES.read_bytes()
    require(bounds["classification"] == "SOURCE_CLOSED" and
            bounds["source_routine"] == "0x01b000..0x01b05e" and
            bounds["source_routine_sha256"] == hashlib.sha256(
                opcodes[0x01B000:0x01B05E]).hexdigest() and
            bounds["orphan_bound_runs"] == 0 and
            "0x01b030" in bounds["writer_pcs"] and
            "0x01b042" in bounds["writer_pcs"], "global bound authority drift")
    terrain = report["terrain_resolver"]
    require(terrain["classification"] == "SOURCE_CLOSED" and
            terrain["source_block_sha256"] == hashlib.sha256(
                opcodes[0x0B1BAA:0x0B1C70]).hexdigest() and
            terrain["route_reachable_record_count"] == 6 and
            terrain["orphan_route_reachable_records"] == 0 and
            {item["address"] for item in terrain["records"]} == set(TERRAIN_RECORDS)
            and all(item["source_program_match"] is True and
                    item["classification"] == "SOURCE_CLOSED"
                    for item in terrain["records"]) and
            {item["address"] for item in terrain["records"]
             if item["perturbed_calls"]["0x0b1c68"] > 0} ==
            {"0x0b20d6", "0x0b2136"} and
            all(len(item["decoded_six_fields"]) == 6 and
                len(item["control_bytes"]) == 2 and
                item["selected_handler"] in
                {"0x0b1c14", "0x0b1c54", "0x0b1d0e", "0x0b1e9c"}
                for item in terrain["records"]), "terrain closure drift")
    terrain_contract = terrain["implementation_contract"]
    packed_grid = terrain_contract["selection"]["bounded_packed_grid"]
    packed_grid_bytes = bytes.fromhex(packed_grid["packed_bytes_hex"])
    expected_decoded = {
        "0x0b20c6": {"kind_u8": 0, "branch_selector_u8": 128,
                      "orientation_u8": 128, "shift_u8": 128,
                      "x_parameter_u8": 128, "z_parameter_u8": 128},
        "0x0b20d6": {"kind_u8": 2, "branch_selector_u8": 2,
                      "orientation_u8": 128, "shift_u8": 128,
                      "x_parameter_u8": 16, "z_parameter_u8": 16},
        "0x0b2136": {"kind_u8": 2, "branch_selector_u8": 2,
                      "orientation_u8": 128, "shift_u8": 128,
                      "x_parameter_u8": 16, "z_parameter_u8": 8},
        "0x0b2186": {"kind_u8": 6, "branch_selector_u8": 4,
                      "orientation_u8": 2, "shift_u8": 1,
                      "x_parameter_s8": 0, "z_parameter_s8": 0},
        "0x0b218e": {"kind_u8": 6, "branch_selector_u8": 4,
                      "orientation_u8": 2, "shift_u8": 1,
                      "x_parameter_s8": 0, "z_parameter_s8": 8},
        "0x0b220e": {"kind_u8": 4, "branch_selector_u8": 2,
                      "orientation_u8": 2, "shift_u8": 1,
                      "x_parameter_u8": 0, "z_parameter_u8": 8},
    }
    require(terrain_contract["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            [item["name"] for item in terrain_contract["six_fields"]] ==
            ["kind", "branch_selector", "orientation", "shift",
             "x_parameter", "z_parameter"] and
            [item["type"] for item in terrain_contract["six_fields"]] ==
            ["u8", "u8", "u8", "u8", "u8_or_s8_by_kind",
             "u8_or_s8_by_kind"] and
            terrain_contract["selection"]["record_address"] ==
            "0x0b20c6 + 2 * (u8(cell+2) & 0xfc)" and
            terrain_contract["handlers"]["2"]["selected_entries"] ==
            {"0": "0x0b1c38", "2": "0x0b1c54"} and
            terrain_contract["handlers"]["4"]["selected_entry"] ==
            "0x0b1d0e" and
            terrain_contract["handlers"]["6"]["selected_entry"] ==
            "0x0b1e9c" and
            packed_grid["classification"] == "SOURCE_DERIVED_CONTENT_DATA" and
            packed_grid["world_x_inclusive"] == [640, 1360] and
            packed_grid["world_z_inclusive"] == [272, 400] and
            packed_grid["tile_size"] == 16 and
            packed_grid["width"] == 46 and packed_grid["height"] == 9 and
            packed_grid["cell_count"] == 414 and
            packed_grid["bits_per_cell"] == 2 and
            packed_grid["selector_code_u8"] == [0, 24, 56] and
            packed_grid["packed_bytes"] == 104 and
            len(packed_grid_bytes) == 104 and
            hashlib.sha256(packed_grid_bytes).hexdigest() ==
            packed_grid["packed_sha256"] and
            {item["address"]: item["decoded_six_fields"]
             for item in terrain["records"]} == expected_decoded,
            "terrain implementation contract drift")
    bodies = report["navigation_bodies"]
    require(bodies["classification"] == "SOURCE_CLOSED" and
            bodies["route_reachable_class_type_pairs"] == 4 and
            bodies["orphan_navigation_bodies"] == 0 and
            {item["class"] for item in bodies["instances"]} ==
            {"0x07", "0x08", "0x09", "0x0a"} and
            all(item["navigation_role"] == "SOURCE_CLOSED" and
                    item["complete_actor_authority"].startswith("PARTIAL;")
                    and item["baseline_writer_pcs"] and
                    item["source_block_sha256"] == hashlib.sha256(
                        opcodes[TYPE20_ROUTINES[item["class"]][0]:
                                TYPE20_ROUTINES[item["class"]][1]]).hexdigest()
                    for item in bodies["instances"]), "navigation-body boundary drift")
    obstacle = report["obstacle_response"]
    require(obstacle["source_block_sha256"] == hashlib.sha256(
                opcodes[0x01D930:0x01D99A]).hexdigest() and
            obstacle["accepted_oracle08_removal_control"] is True and
            obstacle["shared_player_enemy_rectangle_rejected"] is True,
            "obstacle-response closure drift")
    obstacle_contract = obstacle["implementation_contract"]
    require(obstacle_contract["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            obstacle_contract["player_geometry"]["box"] is None and
            obstacle_contract["obstacle_box"] == {
                "address": "0x06e22c", "x_center_s8": 0,
                "y_center_s8": 0, "x_half_u8": 32, "y_half_u8": 127,
                "z_center_s8": 0, "z_half_u8": 6,
                "flags_u16": 0xff00} and
            obstacle_contract["dynamic_control"]["rows"] == 745 and
            obstacle_contract["dynamic_control"]["right_edge"] == 1091 and
            obstacle_contract["minimum_penetration"]["axis_guard"] ==
            "resolve z only when unsigned z_penetration < unsigned x_penetration; otherwise resolve x",
            "obstacle implementation contract drift")
    lifecycle = obstacle["lifecycle_contract"]
    require(lifecycle["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            lifecycle["capture_identity"]["byte_identical"] is True and
            lifecycle["source_scene_record"]["bytes"] ==
            "02b00463014300040a000000000e0000" and
            lifecycle["source_scene_record"]["camera_threshold_u16"] == 688 and
            lifecycle["spawn"]["guard"].startswith(
                "nonnegative record threshold 688") and
            lifecycle["spawn"]["camera_sample_order"]["native_rule"].startswith(
                "scheduler guard uses camera_x_previous") and
            lifecycle["initializer"]["guard"] ==
            "unsigned record-36 free count at 0xffee8f >= 4" and
            lifecycle["initializer"]["child_allocation"]["variant_order_u8"] ==
            [3, 2, 1, 0] and
            [len(lifecycle["child_presentation"]["variant_sequences"][str(i)])
             for i in range(4)] == [5, 8, 6, 6] and
            lifecycle["child_presentation"]["release_record"][
                "animation_record"] == "0x09bd90" and
            lifecycle["child_presentation"]["dispatch_table"][
                "offsets_u16"] == [8, 48, 82, 82] and
            lifecycle["child_presentation"]["state_program"]["state_0200"][
                "guard"] == "u8(parent+0x04) >= 4" and
            lifecycle["state_program"]["state_0200"]["source_frame"] == 2804 and
            lifecycle["state_program"]["state_0200"]["player_trigger"][
                "damage_s16"] == 25 and
            lifecycle["state_program"]["state_0200"]["player_trigger"][
                "edge_to_damage_ticks_u8"] == 14 and
            lifecycle["state_program"]["state_0400"][
                "timer_high_byte_u8"] == 8 and
            lifecycle["state_program"]["state_0400"][
                "presentation_rng_transaction"] == {
                    "caller": "0x06df3c", "callee": "0x0bc692",
                    "rng_entry": "0x017c5e", "rng_call_pc": "0x0bc6b4",
                    "calls_u8": 1, "seed_before_u16": "0x441b",
                    "seed_after_u16": "0xcce7",
                    "selector_mask_u16": "0x001f",
                    "owner": "source-owned obstacle-break presentation transaction"} and
            lifecycle["state_program"]["state_0400"][
                "audio_transaction"]["command_u16"] == "0x0142" and
            lifecycle["state_program"]["state_0400"][
                "audio_transaction"]["semantic_sound_name"] == "UNKNOWN" and
            lifecycle["state_program"]["state_0404"]["completion_guard"] ==
            "both flag bits set" and
            lifecycle["state_program"]["state_0404"]
                ["transition_initialization_order"]["source_update_frame"] == 2815 and
            lifecycle["state_program"]["state_0404"]
                ["transition_initialization_order"]["fixed_frame_delay_forbidden"] is True and
            lifecycle["state_program"]["state_0404"]["channel_seeds"]
                ["primary"]["fp68_u32"] == "0x01730002" and
            lifecycle["state_program"]["state_0404"]["channel_seeds"]
                ["alternate"]["animation_record"] == "0x06e182" and
            lifecycle["state_program"]["state_0404"]["direction_control"] == {
                "field": "actor+0x4f:u8", "source_value_at_entry_u8": 1,
                "presentation_facing_field": "actor+0x0f:u8",
                "presentation_facing_at_entry_u8": 0,
                "rule": "only when actor+0x4f is zero negate field30, field38, field32, and field3a; actor+0x0f must not control trajectory sign"} and
            lifecycle["state_program"]["state_0404"]["selection_witness"][1] == {
                "frame": 2817, "channel": "alternate", "x_s16": 1127,
                "y_s16": 328, "animation_record": "0x06e182"} and
            lifecycle["collision_damage"]["player_attack_record"][
                "damage_s16"] == 25 and
            lifecycle["collision_damage"]["obstacle_hurt_record"][
                "x_half_u8"] == 16 and
            lifecycle["lifetimes"]["parent"] == {
                "source_slot": "0xffb380", "first_frame": 2246,
                "last_frame": 2848, "rows": 603} and
            lifecycle["lifetimes"]["children"]["count"] == 4 and
            lifecycle["transition_suppression"]["suppressed_writes"] == 18 and
            lifecycle["transition_suppression"]["mutant_final_route"] == 4 and
            lifecycle["fixed_frame_substitute_forbidden"] is True,
            "obstacle lifecycle contract drift")
    camera = report["camera"]
    require(camera["classification"] == "SOURCE_CLOSED" and
            camera["primary_writer"] == "0x0b0706" and
            camera["controller_block_sha256"] == hashlib.sha256(
                opcodes[0x0B04CE:0x0B0862]).hexdigest() and
            len(camera["camera_lock_and_unlock_runs"]) == 19 and
            camera["orphan_camera_edges"] == 0 and
            all(item["classification"] == "SOURCE_CLOSED"
                and item["owning_writer_pcs"]
                for item in camera["camera_lock_and_unlock_runs"]),
            "camera closure drift")
    camera_contract = camera["implementation_contract"]
    require(camera_contract["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            camera_contract["x_target_arithmetic"]["speed_table_u16"] ==
            [0, 1, 1, 2, 3, 4, 5, 6, 7, 7,
             8, 8, 9, 9, 10, 10, 11, 11, 11, 11] and
            camera_contract["coffee_shop_guard"]["phase0_lock_guard"] ==
            "u16(A5+0x278) >= 0x0340" and
            camera_contract["x_target_arithmetic"]["wide_target_delta"] ==
            "((max_x+min_x)>>1)-x_target-0x00c0" and
            camera_contract["x_target_arithmetic"]["narrow_right_delta"] ==
            "max_x-x_target-0x00e0" and
            camera_contract["x_target_arithmetic"]["narrow_left_delta"] ==
            "min_x-x_target-0x00a0" and
            camera_contract["coffee_shop_guard"]["phase2_unlock_guard"] ==
            "unsigned(u16(A5-0x65e6)-u16(controller+0x44)) >= (u8(A5+0x020e)<<4), OR controller+0x46 countdown reaches zero" and
            camera_contract["coffee_shop_guard"]["fixed_frame_authority"] is False and
            camera_contract["initialization"]["first_control_chronology"] == [
                {"source_frame_u16": 2237, "route_state_s16": 2,
                 "player_x_s16": 944, "camera_x_s16": 640,
                 "camera_target_x_s16": 640},
                {"source_frame_u16": 2238, "route_state_s16": 4,
                 "player_x_s16": 944, "camera_x_s16": 648,
                 "camera_target_x_s16": 648},
                {"source_frame_u16": 2239, "route_state_s16": 4,
                 "player_x_s16": 944, "camera_x_s16": 655,
                 "camera_target_x_s16": 655}] and
            camera_contract["world_to_plane_order"]["raw_pattern_name_offset_forbidden"] is True and
            {(item["frame"], item["x_lower"], item["x_upper"])
             for item in camera_contract["dynamic_checkpoints"]} >=
            {(3792, 640, 832), (4992, 832, 832), (4993, 832, 1008)},
            "camera implementation contract drift")
    closure = report["closure"]
    require(all(value == 0 for value in closure.values()),
            "navigation zero-gap closure drift")
    require(report["protected_boundaries"] == {
        "predator_warrior": "SOURCE_CLOSED",
        "global_audio_load_release": "SOURCE_CLOSED",
        "production_runtime_writes": 0, "yaba_runs": 0,
        "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
        "salvage08_active": False, "physical_saturn": "UNRUN",
        "spec02_active": False, "oracle11_active": True,
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 Round 1 navigation: SOURCE_CLOSED; zero orphan bounds, "
          "terrain records, navigation bodies, or camera edges")


if __name__ == "__main__":
    main()
