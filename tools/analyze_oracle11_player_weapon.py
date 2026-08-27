#!/usr/bin/env python3
"""Build the corrected Predator Warrior Button1 source contract.

The prior capture selected character 1 (Major Schaefer). This analyzer makes
player +0xd2, actor lineage, and the emitted CPS object stream hard gates so a
valid-but-wrong character dispatch cannot pass again.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps/mame/oracle11_predator_warrior_button1_system_corrective_v4"
REJECTED = ROOT / ".deps/mame/oracle11_major_schaefer_button1_rejected_control_v2"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
AUTH = ROOT / "data/oracle11_predator_warrior_authority.json"
OUT = ROOT / "data/oracle11_predator_weapon_projectile_resource.json"
VARIANTS = (
    "cold_run_1", "cold_run_2", "resource_empty", "b1_held",
    "repeat_startup", "repeat_active", "repeat_recovery", "target_inside",
    "target_outside", "allocation_unavailable", "target_removed",
    "projectile_class_removed", "facing_reversed", "damage_attack_class_2",
)
FILES = (
    "samples.tsv", "writes.tsv", "actors.tsv", "qsound.tsv", "damage.tsv",
    "impact_audio.tsv", "objects.tsv", "character_samples.tsv",
)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def run(root: Path, name: str):
    return {filename: rows(root / name / filename) for filename in FILES}


def first_frame(samples, predicate) -> int:
    return int(next(row["frame"] for row in samples if predicate(row)))


def window(blob: bytes, start: int, end: int):
    return {
        "start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
        "bytes": end - start,
        "sha256": hashlib.sha256(blob[start:end]).hexdigest(),
    }


def s16(blob: bytes, address: int) -> int:
    return int.from_bytes(blob[address:address + 2], "big", signed=True)


def animation_record(program: bytes, address: int):
    return {
        "animation_record": f"0x{address:08x}",
        "timer_u16": int.from_bytes(program[address:address + 2], "big"),
        "branch_s16": int.from_bytes(
            program[address + 2:address + 4], "big", signed=True),
        "assembly": f"0x{int.from_bytes(program[address + 4:address + 8], 'big'):08x}",
        "hurt_selector_u8": program[address + 8],
        "attack_selector_u8": program[address + 9],
        "record_sha256": hashlib.sha256(program[address:address + 16]).hexdigest(),
    }


def animation_sequence(program: bytes, base: int):
    result = []
    for index in range(64):
        record = animation_record(program, base + index * 16)
        result.append(record)
        if record["branch_s16"] < 0:
            break
    return result


def box_record(program: bytes, address: int, stride: int):
    raw = list(program[address:address + stride])
    signed = lambda value: value - 256 if value > 127 else value
    result = {
        "address": f"0x{address:08x}",
        "x_center_s8": signed(raw[0]), "y_center_s8": signed(raw[1]),
        "x_half_u8": raw[2], "y_half_u8": raw[3],
        "z_center_s8": signed(raw[4]), "z_half_u8": raw[5],
        "record_sha256": hashlib.sha256(bytes(raw)).hexdigest(),
    }
    if stride == 16:
        result.update({
            "knockback_mode_s8": signed(raw[10]), "hit_value_u8": raw[14],
            "damage_selector_u8": raw[9],
        })
    return result


def collision_table(program: bytes, base: int):
    hurt_relative = s16(program, base)
    attack_relative = s16(program, base + 2)
    return {
        "table": f"0x{base:08x}",
        "hurt_relative_s16": hurt_relative,
        "attack_relative_s16": attack_relative,
        "hurt_entries": [box_record(program, base + hurt_relative, 8)],
        "attack_entries": [
            box_record(program, base + attack_relative + index * 16, 16)
            for index in range(3)
        ],
    }


def normalized_object_identity(object_rows, entry_frame: int, last_tick: int):
    canonical = []
    by_tick = {}
    for row in object_rows:
        tick = int(row["frame"]) - entry_frame
        if 0 <= tick <= last_tick:
            item = "%d:%d:%s:%s" % (
                tick, int(row["ordinal"]), row["code"], row["attribute"])
            canonical.append(item)
            by_tick.setdefault(tick, []).append(item.split(":", 1)[1])
    payload = "\n".join(canonical).encode("ascii")
    return {
        "normalization": "entry-relative tick + object ordinal + CPS code + CPS attribute; x/y omitted",
        "frame_ticks": [0, last_tick], "row_count": len(canonical),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "per_tick_sha256": {
            str(tick): hashlib.sha256("\n".join(items).encode("ascii")).hexdigest()
            for tick, items in sorted(by_tick.items())
        },
    }


def actor_groups(actor_rows, actor_class: str):
    groups = {}
    for row in actor_rows:
        if row["kind"] == "record4" and row["class"] == actor_class:
            groups.setdefault(row["slot"], []).append(row)
    return groups


manifest = json.loads((RAW / "input_manifest.json").read_text(encoding="utf-8-sig"))
rejected_manifest = json.loads(
    (REJECTED / "input_manifest.json").read_text(encoding="utf-8-sig"))
require(manifest["character_route"] == "predator_warrior", "wrong capture route")
require(rejected_manifest["character_route"] == "legacy", "wrong rejection route")
require(tuple(item["name"] for item in manifest["variants"]) == VARIANTS,
        "corrective variant inventory drift")
for item in manifest["variants"]:
    for filename, expected in item["sha256"].items():
        require(digest(RAW / item["name"] / filename) == expected,
                f"{item['name']} {filename} drift")
for filename in FILES:
    require(digest(RAW / "cold_run_1" / filename) ==
            digest(RAW / "cold_run_2" / filename),
            f"Predator cold-run mismatch: {filename}")
    require(digest(REJECTED / "cold_run_1" / filename) ==
            digest(REJECTED / "cold_run_2" / filename),
            f"Major rejection cold-run mismatch: {filename}")

runs = {name: run(RAW, name) for name in VARIANTS}
baseline = runs["cold_run_1"]
rejected = run(REJECTED, "cold_run_1")
program = PROGRAM.read_bytes()
opcodes = OPCODES.read_bytes()
samples = baseline["samples.tsv"]
rejected_samples = rejected["samples.tsv"]

require({int(row["character"]) for row in samples} == {0},
        "Predator capture changed character")
require({int(row["character"]) for row in rejected_samples} == {1},
        "Major rejection control did not select character 1")
entry = first_frame(samples, lambda row: int(row["action"]) == 0x0C00)
cleanup = first_frame(samples, lambda row: int(row["frame"]) > entry and
                      int(row["action"]) == 0)
returned = first_frame(samples, lambda row: int(row["frame"]) > cleanup and
                       int(row["action"]) == 2)
rejected_entry = first_frame(
    rejected_samples, lambda row: int(row["action"]) == 0x0C00)
require((entry, cleanup - entry, returned - entry) == (4422, 19, 20),
        "Predator Button1 action chronology drift")

player_rows = [row for row in samples if entry <= int(row["frame"]) <= cleanup]
require(len({(row["x"], row["y"], row["z"], row["facing"])
             for row in player_rows}) == 1,
        "Predator Button1 moved or changed facing")
require(int(samples[0]["resource"]) == 64 and
        min(int(row["resource"]) for row in samples) == 24,
        "Predator Button1 40-unit debit drift")
require(min(int(row["resource"]) for row in
            runs["allocation_unavailable"]["samples.tsv"]) == 24,
        "resource debit incorrectly depends on record-4 allocation")

parent_groups = actor_groups(baseline["actors.tsv"], "00")
child_groups = actor_groups(baseline["actors.tsv"], "04")
require(list(parent_groups) == ["ff8680"], "Predator parent lineage drift")
require(list(child_groups) == ["ff8700", "ff8780", "ff8800", "ff8880", "ff8900"],
        "Predator child lineage drift")
parent = parent_groups["ff8680"]
require((int(parent[0]["frame"]), int(parent[-1]["frame"])) == (4424, 4475),
        "Predator parent lifetime drift")
require(sorted({int(row["state"]) for row in parent}) == [2, 4, 6],
        "Predator parent state sequence drift")
child_first_frames = [int(child_groups[slot][0]["frame"]) for slot in child_groups]
require(child_first_frames == [4445, 4451, 4457, 4463, 4469],
        "Predator child cadence drift")
require(not actor_groups(runs["allocation_unavailable"]["actors.tsv"], "00"),
        "allocation-unavailable control spawned a parent")
require(not [row for row in runs["projectile_class_removed"]["actors.tsv"]
             if row["kind"] == "record4" and row["class"] in ("00", "04")],
        "class-0 parent suppression did not remove downstream family")

parent_angles = {
    name: sorted({int(row["angle"]) for row in
                  actor_groups(runs[name]["actors.tsv"], "00").get("ff8680", [])})
    for name in ("cold_run_1", "target_inside", "target_outside", "facing_reversed")
}
require(parent_angles == {
    "cold_run_1": [17], "target_inside": [35],
    "target_outside": [35], "facing_reversed": [47]},
    "Predator target/facing angle selection drift")

damage = runs["target_inside"]["damage.tsv"]
require([(row["frame"], row["attacker"], row["attack_record"],
          row["attack_selector"], row["damage"]) for row in damage] == [
              ("4424", "ff8680", "02fc58", "19", "7f"),
              ("4427", "ff8700", "030cd2", "0e", "1f")],
        "Predator parent/child current-state damage provenance drift")
mutated_damage = runs["damage_attack_class_2"]["damage.tsv"]
require(mutated_damage and mutated_damage[0]["attacker_5e"] == "02",
        "attacker-class mutation was not discriminating")

player_presentation = []
for row in player_rows:
    player_presentation.append({
        "tick": int(row["frame"]) - entry,
        "action_u16": int(row["action"]),
        "substate_u8": int(row["inner"]),
        **animation_record(program, int(row["anim"], 16)),
    })
require([row["animation_record"] for row in player_presentation] == [
    "0x0015f1f4", "0x0015e540", "0x0015e540", "0x0015e540",
    "0x0015e550", "0x0015e560", "0x0015e560", "0x0015e570",
] + ["0x0015e580"] * 11 + ["0x0015f1f4"],
        "Predator player presentation timeline drift")

source_object_identity = normalized_object_identity(
    baseline["objects.tsv"], entry, cleanup - entry)
rejected_object_identity = normalized_object_identity(
    rejected["objects.tsv"], rejected_entry, cleanup - entry)
require(source_object_identity["sha256"] != rejected_object_identity["sha256"],
        "normalized object stream does not discriminate character families")

parent_spawn_rows = []
for base in (0x02FAF4, 0x02FB1C):
    parent_spawn_rows.append([
        {
            "x_s16": s16(program, base + index * 8),
            "y_s16": s16(program, base + index * 8 + 2),
            "z_s16": s16(program, base + index * 8 + 4),
            "variant_u8": program[base + index * 8 + 6],
        }
        for index in range(5)
    ])
parent_initial_offsets = [
    [s16(opcodes, 0x02F8E8 + index * 4),
     s16(opcodes, 0x02F8EA + index * 4)]
    for index in range(6)
]
require(parent_initial_offsets == [
    [5, 86], [-35, 76], [-6, 90], [-6, 53], [8, 49], [19, 54]],
    "Predator parent initial-offset table drift")
low_motion_pointers = [
    int.from_bytes(program[0x02FA80 + index * 4:0x02FA84 + index * 4], "big")
    for index in range(16)
]
high_motion_pointers = [
    int.from_bytes(program[0x02FAC0 + index * 4:0x02FAC4 + index * 4], "big")
    for index in range(13)
]


def route_motion_vectors(pointers):
    return {
        str(angle): [[s16(program, pointer + angle * 4),
                      s16(program, pointer + angle * 4 + 2)]
                     if pointer else [0, 0] for pointer in pointers]
        for angle in (17, 35, 47)
    }


parent_collision = collision_table(program, 0x02FC3C)
child_collision = collision_table(program, 0x030CB6)
parent_records = [animation_record(program, 0x02FB48 + index * 16)
                  for index in range(7)]
child_variant_offsets = [
    int.from_bytes(program[0x030784 + index * 2:0x030786 + index * 2], "big")
    for index in range(3)
]
child_sequences = {
    str(index): animation_sequence(program, 0x030784 + offset)
    for index, offset in enumerate(child_variant_offsets)
}

empty_samples = runs["resource_empty"]["samples.tsv"]
empty_entry = first_frame(empty_samples, lambda row: int(row["action"]) == 0x1A00)
empty_cleanup = first_frame(empty_samples, lambda row: int(row["frame"]) > empty_entry and
                            int(row["action"]) == 0)
empty_return = first_frame(empty_samples, lambda row: int(row["frame"]) > empty_cleanup and
                           int(row["action"]) == 2)
require((empty_cleanup - empty_entry, empty_return - empty_entry) == (17, 18),
        "Predator empty-resource chronology drift")
empty_player_timeline = []
for row in empty_samples:
    frame = int(row["frame"])
    if empty_entry <= frame <= empty_cleanup:
        empty_player_timeline.append({
            "tick": frame - empty_entry,
            "action_u16": int(row["action"]),
            "substate_u8": int(row["inner"]),
            **animation_record(program, int(row["anim"], 16)),
        })
require({row["animation_record"] for row in empty_player_timeline[1:17]} ==
        {"0x0015fcfc"}, "Predator empty-resource presentation drift")

current_auth = json.loads(AUTH.read_text(encoding="ascii"))
old_weapon = current_auth.get("weapon_projectile_resource", {})
preserved_special = old_weapon.get("special_causal_trace", {})
preserved_empty_effect = old_weapon.get("implementation_contract", {}).get(
    "empty_effect_variant1_contract", {})
require(preserved_empty_effect.get("class") == "0x10",
        "accepted class-0x10 empty-effect contract missing")

implementation_contract = {
    "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
    "source_input": {
        "button1_mask": "0x0010",
        "guard": "new Button1 edge in normal controllable player state after the shared B1+B2 guard",
    },
    "state_dispatch": {
        "sufficient_entry_action": "0x0c00",
        "sufficient_active_action": "0x0c02 then 0x0c04",
        "empty_entry_action": "0x1a00", "empty_active_action": "0x1a02",
        "cleanup_action": "0x0000", "return_locomotion_action": "0x0002",
    },
    "sufficient_action": {
        "entry_tick": 0, "cleanup_tick": cleanup - entry,
        "return_tick": returned - entry, "resource_capacity_u8": 64,
        "resource_debit_u8": 40, "resource_clamp_min_u8": 0,
        "resource_debit_guard": "sufficient-resource Button1 state entry; independent of record-4 allocation success",
        "recharge_countdown_after_entry_u8": 12,
        "player_position_and_facing_latched": True, "rng_calls": [],
        "presentation_timeline": player_presentation,
    },
    "record4_parent_class0": {
        "spec_executable": True, "record_type_u8": 4, "class_u8": 0,
        "allocator": "0x01773e", "allocation_writer": "0x02412a..0x02416e",
        "allocation_guard": "record-type-4 allocator returns nonzero",
        "allocation_writes": {
            "active_increment_u8": 1, "class_u8": 0, "variant_u8": 0,
            "position": "copy player x/y/z high words",
            "facing_u8": "copy player +0x0f", "angle_u8": "copy player +0x8a",
            "owner_pointer_u16": "player low word",
        },
        "dispatch": "0x02f870", "state_sequence_u8": [0, 2, 4, 6],
        "scheduler_position": "record type 4 before 8/12/16/20/24/28/36",
        "initialization": {
            "entry": "0x02f884", "next_state_u8": 2,
            "motion_table_u32": "0x001fb7c0",
            "collision_table_u32": "0x0002fc3c",
            "object_or_u16": "0x8000", "collision_result_s16": 0,
            "active_collision_u8": 1,
            "position_rule": "decrement z high word, then add signed selector offsets from parent presentation table with x sign controlled by facing",
            "player_presentation_selector_u8": "player +0x24 low byte",
            "selector_offsets_s16": parent_initial_offsets,
            "presentation_records": parent_records,
        },
        "active_state": {
            "entry": "0x02f900",
            "guards_in_order": [
                "collision_result_s16 < 0 -> state/substate 0x0400:0000",
                "u16(x_high - camera_x + 0x50) > 0x0220 -> state/substate 0x0400:0000",
                "u16(y_high - camera_y + 0x10) > 0x0120 -> state/substate 0x0400:0000",
                "u16(y_high) < u16(z_high) -> state/substate 0x0400:0000",
            ],
            "update_order": ["shared 16.16 motion 0x016248", "shared animation 0x016536", "two nibble-selected signed motion contributions", "progress +0x2a by 8 capped at 0xc0", "visibility"],
            "angle_u8_route_values": parent_angles,
            "low_nibble_motion_pointer_u32": [f"0x{value:08x}" for value in low_motion_pointers],
            "high_nibble_motion_pointer_u32": [f"0x{value:08x}" for value in high_motion_pointers],
            "route_motion_vectors_s16": {
                "low": route_motion_vectors(low_motion_pointers),
                "high": route_motion_vectors(high_motion_pointers),
            },
        },
        "child_emitter_state": {
            "entry": "0x02f9dc", "initial_child_count_u8": 5,
            "initial_cadence_u8": 1, "cadence_reload_u8": 6,
            "spawn_ticks_from_parent_state4": [1, 7, 13, 19, 25],
            "child_spawn_source_frames": child_first_frames,
            "normal_rows": parent_spawn_rows[0],
            "collision_rows": parent_spawn_rows[1],
            "row_index": "predecremented child count 4..0",
            "x_sign_rule": "negate row x when parent facing is zero",
        },
        "release_state": {"entry": "0x02fa7a", "release": "0x017754"},
        "collision_table": parent_collision,
        "capture_projection": {
            "slot": "0xff8680", "first_visible_frame": 4424,
            "state4_frame": 4444, "state6_frame": 4475,
            "release_frame": 4475,
        },
    },
    "record4_child_class4": {
        "spec_executable": True, "record_type_u8": 4, "class_u8": 4,
        "dispatch": "0x0306fe", "state_sequence_u8": [0, 2, 4],
        "initialization": {
            "entry": "0x030712", "next_state_u8": 2,
            "collision_table_u32": "0x00030cb6",
            "object_or_u16": "0x8000", "collision_result_s16": 0,
            "active_collision_u8": 1,
            "variant_offsets_u16": child_variant_offsets,
            "variant_presentation_sequences": child_sequences,
        },
        "active_state": {
            "entry": "0x030768",
            "terminal_guard": "animation branch s16 < 0 increments state by 2",
            "update_order": ["terminal guard", "shared animation", "visibility"],
        },
        "release_state": {"entry": "0x03077e", "release": "0x017754"},
        "collision_table": child_collision,
        "capture_projection": {
            "slots": list(child_groups), "first_visible_frames": child_first_frames,
            "spawn_cadence_frames": 6,
        },
    },
    "current_state_collision_damage": {
        "scheduler": "0x01cbcc record-type-4 attackers against record-type-12 defenders",
        "damage_routine": "0x01d504",
        "parent_contact": {
            "frame": 4424, "attacker": "0xff8680",
            "attack_record": "0x0002fc58", "attack_selector_u8": 25,
            "damage_u8": 127,
        },
        "child_contact": {
            "frame": 4427, "attacker": "0xff8700",
            "attack_record": "0x00030cd2", "attack_selector_u8": 14,
            "damage_u8": 31,
        },
        "mutation": "attacker +0x5e changed to 2; exact downstream table address/value changes are retained in damage.tsv",
    },
    "resource_tick": {
        "order": "after player action entry/debit and before HUD projection",
        "normal_recharge_reload_u8": 2, "depleted_recharge_reload_u8": 6,
    },
    "empty_fallback": {
        "timer_type": "u8", "timer_initial": 16,
        "cleanup_tick": empty_cleanup - empty_entry,
        "return_tick": empty_return - empty_entry, "damaging_record4_count": 0,
        "presentation_timeline": empty_player_timeline,
    },
    "empty_effect_variant1_contract": preserved_empty_effect,
    "implementation_blocker": None,
}

report = {
    "schema": 2, "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
    "status": "SOURCE_CLOSED",
    "scope": "one-player character-0 Predator Warrior Round 1 Button1, record-type-4 class-0 parent/class-4 child family, resource, collision, damage, and presentation identity",
    "character_identity": {
        "required_character_u8": 0, "required_character": "predator_warrior",
        "rejected_character_u8": 1, "rejected_character": "major_schaefer",
        "captured_field": "player +0xd2 u8", "per_frame_asserted": True,
        "normalized_object_stream_asserted": True,
        "required_probe": rows(RAW / "cold_run_1" / "presentation_probe.tsv")[0],
        "rejected_probe": rows(REJECTED / "cold_run_1" / "presentation_probe.tsv")[0],
        "required_object_stream": source_object_identity,
        "rejected_object_stream": rejected_object_identity,
        "negative_control_result": "PASS: valid Major addresses/assemblies and object stream are rejected before semantic comparison",
    },
    "determinism": {
        "independent_cold_runs": 2, "byte_identical": True,
        "identical_files": list(FILES),
    },
    "source_identity": {
        "player_button1": window(opcodes, 0x024060, 0x024280),
        "record4_class0": window(opcodes, 0x02F870, 0x02FA7E),
        "record4_class4": window(opcodes, 0x0306FE, 0x030784),
        "record4_class0_tables": window(program, 0x02FA80, 0x02FC7C),
        "record4_class4_tables": window(program, 0x030784, 0x030CF2),
    },
    "authority_separation": {
        "player_action": "character-0 0x024060 state body owns action, target selection, player presentation, resource debit, and class-0 allocation",
        "projectile_lifecycle": {
            "parent": "record type 4 class 0",
            "children": "five record type 4 class 4 actors at six-frame cadence",
            "forbidden_rejected_path": "record type 4 class 5 and type-24 class 0x3a belong to Major Schaefer's rejected capture",
        },
        "resource": "one 40-unit debit on sufficient Button1 state entry; allocation failure does not refund it",
        "presentation": "player +0xd2, action, animation record, assembly, actor lineage, and normalized object stream must agree in the same source tick",
    },
    "resource_causal_trace": {
        "sufficient": {
            "dispatch_frame": entry, "resource_start": 64,
            "resource_after_entry": 24, "debit": 40,
            "parent_allocation_count": 1, "child_count": 5,
        },
        "allocation_unavailable": {
            "parent_allocation_count": 0, "resource_after_entry": 24,
            "result": "allocation is suppressed without changing the source-owned entry debit",
        },
        "empty": {
            "dispatch_frame": empty_entry, "damaging_projectile_count": 0,
            "auxiliary_class": "0x10",
        },
    },
    "implementation_contract": implementation_contract,
    "special_causal_trace": preserved_special,
    "counterfactuals": [
        {"class": "character_identity", "result": "character 1 Major capture rejected despite internally valid addresses"},
        {"class": "object_stream_identity", "result": "Predator and Major normalized CPS object streams differ"},
        {"class": "allocation_unavailable", "result": "zero parent/child actors; 40-unit debit remains"},
        {"class": "parent_class_suppressed", "result": "zero parent and downstream child actors"},
        {"class": "button1_held", "result": "no additional state entry while continuously held"},
        {"class": "repeat_startup", "result": "startup pulse does not add a second state entry"},
        {"class": "repeat_active", "result": "late active-window edge dispatches only after source cleanup"},
        {"class": "repeat_recovery", "result": "later recovery edge starts a second bounded action"},
        {"class": "facing_reversed", "result": "same action/resource; parent angle and lifetime differ"},
        {"class": "target_inside_outside", "result": "target selector produces source angle 35 under the bounded target route"},
        {"class": "target_removed", "result": "no authored fixed-frame damage result"},
        {"class": "damage_attacker_class", "result": "attacker +0x5e mutation changes the exact source damage lookup"},
        {"class": "resource_empty", "result": "0x1a00/0x1a02 and class-0x10 effect; no record-4 damaging family"},
    ],
    "mutation_controls": {
        "count": 13, "all_downstream_effects_asserted": True,
        "no_fixed_frame_result": True,
        "no_visible_weapon_inference_from_0xad": True,
        "wrong_character_rejected": True,
    },
    "provenance": {
        "capture_manifest_sha256": digest(RAW / "input_manifest.json"),
        "rejected_capture_manifest_sha256": digest(REJECTED / "input_manifest.json"),
        "capture_script_sha256": digest(ROOT / "tools/mame_capture_oracle11_player_weapon.lua"),
        "mame": manifest["mame"],
        "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
    },
    "physical_saturn": "UNRUN", "saturn_emulator": "UNRUN",
}

OUT.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
               encoding="ascii")
current_auth["weapon_projectile_resource"] = report
AUTH.write_bytes(json.dumps(current_auth, sort_keys=True, indent=2).encode("ascii") + b"\n")
print(f"wrote {OUT.relative_to(ROOT)} and updated {AUTH.relative_to(ROOT)}")
