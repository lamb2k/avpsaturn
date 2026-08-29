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
COFFEE = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs21a"
COLLISION_A = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs32a"
COLLISION_B = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs32b"
COLLISION_S = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs32s"
AIR_SPECIAL_A = ROOT / ".deps/mame/oracle11_player_air_a/air_special_combo"
AIR_SPECIAL_B = ROOT / ".deps/mame/oracle11_player_air_b/air_special_combo"
ORACLE07 = ROOT / "data/oracle07_predator_warrior_action_graph_equipment.json"
AUXILIARY = ROOT / "data/oracle11_round1_auxiliary_authority.json"
FULL_ROUTE = ROOT / ".deps/mame/full_route"
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
COLLISION_FILES = (
    "coffee_shop_record4_collision_guard.tsv",
    "coffee_shop_record12_guard6d_writes.tsv",
    "coffee_shop_collision_lists.tsv",
    "coffee_shop_collision_list_writes.tsv",
    "coffee_shop_collision_actor_flags.tsv",
    "coffee_shop_record4_collision_identity_writes.tsv",
    "coffee_shop_collision_identity_assignments.tsv",
    "coffee_shop_scene_health_writes.tsv",
    "coffee_shop_scene_actors.tsv",
    "coffee_shop_scene_frames.tsv",
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
            "impact_variant_u8": raw[8],
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

# The Button1 entry routine uses the nearest eligible record-12 target twice:
# once to derive the projectile angle and once to select one of four player
# presentation tracks.  The isolated corrective capture has no eligible target
# and therefore witnesses selector 4.  The accepted ORACLE-07/10 Coffee Shop
# route witnesses selector 5.  Bind every reachable selector directly from the
# accepted source table so native code cannot reuse selector 4 for all targets.
player_presentation_sequences = {
    str(selector): animation_sequence(program, 0x0015E540 +
                                      (selector - 4) * 0x54)
    for selector in range(4, 8)
}
require(all(len(sequence) == 5 for sequence in
            player_presentation_sequences.values()),
        "Predator Button1 presentation selector sequence drift")
require([[row["timer_u16"] for row in
          player_presentation_sequences[str(selector)]]
         for selector in range(4, 8)] ==
        [[2, 1, 2, 1, 4095]] * 4,
        "Predator Button1 selector timer drift")
player_presentation_variants = {}
for selector in range(4, 8):
    sequence = player_presentation_sequences[str(selector)]
    tick_records = ([None] + [sequence[0]] * 3 + [sequence[1]] +
                    [sequence[2]] * 2 + [sequence[3]] +
                    [sequence[4]] * 11 + [None])
    timeline = []
    for source_row, record in zip(player_presentation, tick_records):
        row = dict(source_row)
        if record is not None:
            row.update(record)
        timeline.append(row)
    player_presentation_variants[str(selector)] = timeline
require(player_presentation_variants["4"] == player_presentation,
        "selector-4 player presentation no longer matches cold capture")
require(player_presentation_variants["5"][1]["animation_record"] ==
        "0x0015e594" and
        player_presentation_variants["5"][4]["animation_record"] ==
        "0x0015e5a4" and
        player_presentation_variants["5"][7]["animation_record"] ==
        "0x0015e5c4",
        "Coffee Shop selector-5 player presentation drift")

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
target_distance_thresholds = [
    int.from_bytes(opcodes[0x024266 + index * 2:
                           0x024268 + index * 2], "big")
    for index in range(16)
]
target_presentation_selectors = list(opcodes[0x024100:0x024110])
require(target_distance_thresholds ==
        [0, 13, 16, 22, 30, 38, 48, 58, 70, 88, 103, 123, 153,
         192, 251, 352], "Predator target distance table drift")
require(target_presentation_selectors ==
        [7, 7, 7, 7, 6, 6, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4],
        "Predator target presentation selector table drift")
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
        for angle in range(17, 48)
    }


parent_collision = collision_table(program, 0x02FC3C)
child_collision = collision_table(program, 0x030CB6)
require(parent_collision["attack_entries"][1]["impact_variant_u8"] == 10 and
        [row["impact_variant_u8"] for row in
         child_collision["attack_entries"]] == [0, 1, 1],
        "Predator projectile impact-variant field drift")
parent_records = animation_sequence(program, 0x02FB48)
require(len(parent_records) == 8 and
        parent_records[-1]["animation_record"] == "0x0002fbb8" and
        parent_records[-1]["branch_s16"] < 0,
        "Predator parent terminal presentation drift")

coffee_actors = rows(COFFEE / "coffee_shop_scene_actors.tsv")
coffee_frames = rows(COFFEE / "coffee_shop_scene_frames.tsv")
full_route_samples = rows(FULL_ROUTE / "samples.tsv")
coffee_parent_rows = [row for row in coffee_actors
                      if row["type"] == "4" and row["class"] == "00" and
                      row["active"] == "1"]
coffee_parent_lifetimes = []
for slot in sorted({row["slot"] for row in coffee_parent_rows}):
    slot_rows = [row for row in coffee_parent_rows if row["slot"] == slot]
    lifetime = []
    prior_frame = None
    for row in slot_rows:
        frame = int(row["frame"])
        if prior_frame is not None and frame != prior_frame + 1:
            coffee_parent_lifetimes.append(lifetime)
            lifetime = []
        lifetime.append(row)
        prior_frame = frame
    if lifetime:
        coffee_parent_lifetimes.append(lifetime)
coffee_parent_projection = []
for lifetime in sorted(coffee_parent_lifetimes,
                       key=lambda group: int(group[0]["frame"])):
    first = lifetime[0]
    first_x = int(first["x_fp"], 16)
    first_y = int(first["y_fp"], 16)
    moved = next(row for row in lifetime[1:]
                 if int(row["x_fp"], 16) != first_x or
                 int(row["y_fp"], 16) != first_y)
    dx = (int(moved["x_fp"], 16) - first_x) & 0xffffffff
    dy = (int(moved["y_fp"], 16) - first_y) & 0xffffffff
    if dx & 0x80000000:
        dx -= 0x100000000
    if dy & 0x80000000:
        dy -= 0x100000000
    require(dx % 256 == 0 and dy % 256 == 0,
            "Coffee Shop parent base motion is not signed 8.8")
    vector = [dx // 256, dy // 256]
    angles = [angle for angle in range(64)
              if [s16(program, 0x001FB7C0 + angle * 4),
                  s16(program, 0x001FB7C2 + angle * 4)] == vector]
    require(len(angles) == 1, "Coffee Shop parent angle is ambiguous")
    coffee_parent_projection.append({
        "slot": "0x" + first["slot"],
        "first_visible_frame": int(first["frame"]),
        "last_visible_frame": int(lifetime[-1]["frame"]),
        "first_motion_frame": int(moved["frame"]),
        "facing_u8": int(first["facing"]),
        "angle_u8": angles[0],
        "base_motion_s16_8_8": vector,
    })
coffee_route_angles = sorted({row["angle_u8"]
                              for row in coffee_parent_projection})
require(coffee_route_angles == [17, 21, 42, 45, 46],
        "Coffee Shop source target angles drift")
coffee_input = {int(row["frame"]): int(row["input_word"])
                for row in full_route_samples}
coffee_player = {int(row["frame"]): int(row["player_substate"])
                 for row in coffee_frames}
require(coffee_input[2249] == 0 and coffee_input[2250] == 8 and
        coffee_player[2251] == 2 and coffee_player[2252] == 0x0c00 and
        coffee_parent_projection[0]["first_visible_frame"] == 2254,
        "Coffee Shop Button1 input/action/allocation chronology drift")
auxiliary = json.loads(AUXILIARY.read_text(encoding="ascii"))
class49 = next(row for row in auxiliary["archetypes"]
               if row["type"] == 24 and row["class"] == "0x49")
require(class49["classification"] == "SOURCE_CLOSED" and
        class49["dispatch_entry"] == "0x08f080" and
        class49["rng"]["calls"] == 0 and
        len(class49["presentation_and_collision"]["records"]) == 8,
        "accepted class-0x49 source authority drift")
class49_variant0_rows = [row for row in coffee_actors
                         if row["type"] == "24" and
                         row["class"] == "49" and
                         row["variant"] == "00"]
class49_variant0_lifetimes = []
active_class49_variant0 = {}
for row in class49_variant0_rows:
    frame = int(row["frame"])
    slot = row["slot"]
    prior = active_class49_variant0.get(slot)
    if prior is None or frame != prior["last_frame"] + 1:
        prior = {
            "source_slot": "0x00ff" + slot[2:],
            "first_frame": frame, "last_frame": frame,
            "animation_record": "0x" + row["animation_record"],
            "first_position_s16": [int(row["x_fp"], 16) >> 16,
                                     int(row["y_fp"], 16) >> 16,
                                     int(row["z"])],
        }
        class49_variant0_lifetimes.append(prior)
        active_class49_variant0[slot] = prior
    else:
        prior["last_frame"] = frame
require(len(class49_variant0_rows) == 793 and
        len(class49_variant0_lifetimes) == 113 and
        class49_variant0_lifetimes[:2] == [
            {"source_slot": "0x00ffc500", "first_frame": 2262,
             "last_frame": 2269, "animation_record": "0x0002fb58",
             "first_position_s16": [925, 397, 319]},
            {"source_slot": "0x00ffc480", "first_frame": 2264,
             "last_frame": 2271, "animation_record": "0x0002fb68",
             "first_position_s16": [914, 394, 319]}],
        "Coffee Shop parent class-0x49 population drift")
parent_class49_effect = {
    "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
    "guard": "global phase byte +0x19 bit0 is clear",
    "native_phase_projection": {
        "counter": "scheduler_frames before the record-4 update",
        "mask_u8": 1, "expected_u8": 1,
        "proof": "accepted Coffee Shop update cadence maps the first two visible lifetimes to source frames 2262 and 2264 from pre-update scheduler counts 193 and 195",
    },
    "caller": "0x02f94c sets D6=8 then calls 0x08f0c6",
    "helper": "0x08f0c6", "pool_allocator": "0x0177da",
    "record_type_u8": 24, "class_u8": 0x49, "variant_u8": 0,
    "timer_u8": 8,
    "writes": ["active += 1", "class = 0x49", "variant = 0",
               "copy parent x/y/z", "copy parent facing",
               "copy parent animation record", "timer = D6"],
    "allocation_failure_rule":
        "projectile continues; omit only this presentation actor",
    "state_sequence_u8": [0, 2, 4],
    "state0": {"next_state_u8": 2, "object_or_u16": "0x8000",
               "field_0x09_u8": 0,
               "collision_pointer_u32": "0x00000000",
               "falls_through_to_state2": True},
    "state2": {"timer_guard":
               "predecrement timer_u8; zero releases in the same dispatch",
               "variant0_movement": "x/y/z unchanged",
               "update_order": ["timer", "variant guard", "visibility"]},
    "state4": {"release": "0x0177f0"},
    "presentation_records": class49["presentation_and_collision"]["records"],
    "scene_actor_rows_u16": len(class49_variant0_rows),
    "scene_lifetime_count_u16": len(class49_variant0_lifetimes),
    "scene_lifetimes": class49_variant0_lifetimes,
    "rng_calls": [], "audio_commands": [],
    "source_bodies": {
        "caller": window(opcodes, 0x02F94C, 0x02F95C),
        "helper": window(opcodes, 0x08F0C6, 0x08F100),
        "dispatch": window(opcodes, 0x08F080, 0x08F0C6),
    },
    "mutation_controls": ["phase-bit guard", "variant", "timer",
                          "allocation", "presentation copy",
                          "state dispatch", "fixed-pool release"],
    "fixed_frame_substitute_forbidden": True,
    "retained_gameplay_authority": False,
}

for filename in COLLISION_FILES:
    require(digest(COLLISION_A / filename) == digest(COLLISION_B / filename),
            f"Coffee Shop collision registration A/B mismatch: {filename}")
collision_lists = rows(COLLISION_A / "coffee_shop_collision_lists.tsv")
collision_lists_s = rows(COLLISION_S / "coffee_shop_collision_lists.tsv")
collision_guard = rows(
    COLLISION_A / "coffee_shop_record4_collision_guard.tsv")
collision_health = rows(
    COLLISION_A / "coffee_shop_scene_health_writes.tsv")
collision_health_s = rows(
    COLLISION_S / "coffee_shop_scene_health_writes.tsv")
identity_assignments = rows(
    COLLISION_A / "coffee_shop_collision_identity_assignments.tsv")
suppressed_list_writes = [
    row for row in rows(
        COLLISION_S / "coffee_shop_collision_list_writes.tsv")
    if row["suppressed"] == "1"]

def collision_rows_at(source_rows, frame):
    return [row for row in source_rows if int(row["frame"]) == frame]

require(all("ffa180" not in row["defender_slots"]
            for row in collision_rows_at(collision_lists, 2295)),
        "Coffee Shop target registered before source visibility pass")
require(all("ffa180" in row["defender_slots"]
            for row in collision_rows_at(collision_lists, 2296)),
        "Coffee Shop target registration frame drift")
require(all("ffa180" not in row["defender_slots"]
            for row in collision_rows_at(collision_lists_s, 2306)),
        "defender-list suppression did not remove the target")
require(len(suppressed_list_writes) == 15 and
        {row["a6"] for row in suppressed_list_writes} == {"ffa180"} and
        {row["pc"] for row in suppressed_list_writes} == {"01686c"} and
        [int(row["frame"]) for row in suppressed_list_writes] ==
            list(range(2296, 2311)),
        "defender-list suppression transaction drift")
target_health = [row for row in collision_health
                 if row["target_slot"] == "ffa180" and
                 row["damage_writer"] == "1"]
target_health_s = [row for row in collision_health_s
                   if row["target_slot"] == "ffa180" and
                   row["damage_writer"] == "1"]
require(target_health and
        (target_health[0]["frame"], target_health[0]["attacker"],
         target_health[0]["attack_record"], target_health[0]["health_before"],
         target_health[0]["health_after"]) ==
        ("2306", "ff8880", "030cd2", "0057", "0038"),
        "registered source projectile contact drift")
require(target_health_s and
        (target_health_s[0]["frame"], target_health_s[0]["attacker"],
         target_health_s[0]["attack_record"],
         target_health_s[0]["health_before"], target_health_s[0]["health_after"]) ==
        ("2311", "ff8880", "030ce2", "0057", "0038"),
        "defender-list suppression did not shift the causal contact")
for filename in ("coffee_shop_scene_actors.tsv",
                 "coffee_shop_scene_frames.tsv"):
    baseline_prefix = [row for row in rows(COLLISION_A / filename)
                       if int(row["frame"]) <= 2305]
    mutant_prefix = [row for row in rows(COLLISION_S / filename)
                     if int(row["frame"]) <= 2305]
    require(baseline_prefix == mutant_prefix,
            f"collision-list suppression changed pre-contact {filename}")
identity_projection = [
    row for row in identity_assignments
    if row["event"] == "exit" and 2253 <= int(row["frame"]) <= 2311]
require([(int(row["frame"]), row["slot"], int(row["global_id820b"], 16))
         for row in identity_projection] == [
             (2253, "ff8680", 0x26), (2287, "ff8700", 0x27),
             (2293, "ff8780", 0x28), (2299, "ff8800", 0x29),
             (2305, "ff8880", 0x2a), (2311, "ff8900", 0x2b)],
        "record-4 collision identity sequence drift")
identity_entries = [
    row for row in identity_assignments
    if row["event"] == "entry" and 2253 <= int(row["frame"]) <= 2311]
require([int(row["global_id820b"], 16) for row in identity_entries] ==
        [0x25, 0x26, 0x27, 0x28, 0x29, 0x2a],
        "record-4 collision identity preincrement drift")
source_contact = next(row for row in collision_guard
                      if row["event"] == "collision_true" and
                      row["frame"] == "2306" and
                      row["defender"] == "ffa180")
require((source_contact["attacker"], source_contact["attacker_latch_index65"],
         source_contact["attacker_id67"], source_contact["defender_guard6d"],
         source_contact["defender_latch_value"],
         source_contact["defender_suppress70"]) ==
        ("ff8880", "00", "2a", "00", "2a", "00"),
        "record-4 collision pair guard/latch drift")
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

# The old summary named 0x024f04 for the special.  That body belongs to a
# different character.  Character 0 writes the action at 0x01a89a and then
# dispatches the route-reachable 0x0800 body at 0x023132/0x02314e.
special_files = ("samples.tsv", "player_writes.tsv", "player_global_writes.tsv")
for filename in special_files:
    require(digest(AIR_SPECIAL_A / filename) ==
            digest(AIR_SPECIAL_B / filename),
            f"Predator special independent capture mismatch: {filename}")
special_samples = rows(AIR_SPECIAL_A / "samples.tsv")
special_entry_index = next(index for index, row in enumerate(special_samples)
                           if int(row["p_action"]) == 0x0800)
special_action_rows = []
for row in special_samples[special_entry_index:]:
    if not (0x0800 <= int(row["p_action"]) <= 0x0804):
        break
    special_action_rows.append(row)
special_entry = int(special_action_rows[0]["frame"])
special_last = int(special_action_rows[-1]["frame"])
special_cleanup = first_frame(
    special_samples, lambda row: int(row["frame"]) > special_last and
    int(row["p_action"]) == 0)
special_return = first_frame(
    special_samples, lambda row: int(row["frame"]) > special_cleanup and
    int(row["p_action"]) == 0x0200)
require((special_entry, special_last, special_cleanup, special_return) ==
        (2792, 2868, 2869, 2870),
        "Predator special route chronology drift")
require({(int(row["p_x"]), int(row["p_y"]), int(row["p_z"]),
          int(row["p_facing"])) for row in special_action_rows} ==
        {(1091, 320, 320, 1)},
        "Predator special changed position or facing")
special_phase_runs = []
for row in special_action_rows:
    phase = int(row["p_action"])
    frame = int(row["frame"])
    if not special_phase_runs or special_phase_runs[-1]["action_u16"] != phase:
        special_phase_runs.append({"action_u16": phase,
                                   "first_frame": frame,
                                   "last_frame": frame})
    else:
        special_phase_runs[-1]["last_frame"] = frame
require(special_phase_runs == [
    {"action_u16": 0x0800, "first_frame": 2792, "last_frame": 2792},
    {"action_u16": 0x0802, "first_frame": 2793, "last_frame": 2804},
    {"action_u16": 0x0804, "first_frame": 2805, "last_frame": 2868},
], "Predator special state sequence drift")
special_records = animation_sequence(program, 0x0015FD10)
require(len(special_records) == 17 and
        special_records[-1]["animation_record"] == "0x0015fe10" and
        special_records[-1]["branch_s16"] == -32768 and
        {row["attack_selector_u8"] for row in special_records} == {0, 11},
        "Predator special presentation sequence drift")
special_visible_runs = []
for row in special_action_rows:
    animation = f"0x{int(row['p_anim'], 16):08x}"
    if animation not in {record["animation_record"]
                         for record in special_records}:
        continue
    frame = int(row["frame"])
    if (not special_visible_runs or
            special_visible_runs[-1]["animation_record"] != animation):
        special_visible_runs.append({
            "animation_record": animation, "first_frame": frame,
            "last_frame": frame, "visible_duration_u16": 1})
    else:
        special_visible_runs[-1]["last_frame"] = frame
        special_visible_runs[-1]["visible_duration_u16"] += 1
require([row["animation_record"] for row in special_visible_runs] ==
        [row["animation_record"] for row in special_records] and
        [row["visible_duration_u16"] for row in special_visible_runs] ==
        [4, 4, 3, 1, 5, 4, 4, 4, 4, 4, 6, 4, 4, 4, 4, 16, 1],
        "Predator special visible presentation cadence drift")
special_coffee_class4b = [row for row in coffee_actors
                          if row["type"] == "24" and row["class"] == "4b" and
                          int(row["frame"]) <= 2840]
require(special_coffee_class4b and
        (int(special_coffee_class4b[0]["frame"]),
         int(special_coffee_class4b[-1]["frame"]),
         special_coffee_class4b[0]["slot"]) == (2805, 2840, "ffc300"),
        "Predator special class-0x4b child drift")
oracle07 = json.loads(ORACLE07.read_text(encoding="ascii"))
require(oracle07["source_routines"]["dispatch"]["special"] ==
        ["0x01a89a", "0x023154", "0x0231f8"] and
        oracle07["action_graph"]["special"]["health_cost"] == 6,
        "accepted ORACLE-07 special provenance drift")

special_implementation_contract = {
    "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
    "spec_executable": True,
    "source_input": {
        "current_buttons_u8": "player+0xee",
        "previous_buttons_u8": "player+0xef",
        "button_mask_u8": "0x70",
        "physical_combo_frame": 2790,
        "visible_action_entry_frame": special_entry,
        "pipeline_delay_frames_u8": 2,
        "guard_routine": "0x01a7e6",
        "guard_order": [
            "reject state 0x0200 action 0x0800 re-entry",
            "character 3 alone requires player+0x8b == 0",
            "require player health s16 at +0x40 != 0",
            "require player contact byte +0x5c == 0",
            "accept at least two new B1/B2/B3 edges",
            "or accept held B1 plus a new B2/B3 edge",
            "or accept held B3 plus a new B1 edge",
        ],
        "action_writer": "0x01a89a",
        "action_write": "player+0x04:u32 = 0x02000800; player+0x07:u8 = 0",
    },
    "state_dispatch": {
        "entry": "0x023132",
        "state_byte": "player+0x07:u8",
        "route_state_sequence_u16": [0x0800, 0x0802, 0x0804],
        "route_phase_runs": special_phase_runs,
        "handlers": {"0x00": "0x02314e", "0x02": "0x0231a4",
                     "0x04": "0x023202"},
        "alternate_handlers_not_selected_in_coffee_shop": {
            "0x06": "0x023270", "0x08": "0x023280",
            "0x0a": "0x0232ee", "0x0c": "0x023300"},
    },
    "initialization": {
        "action_local_flag_write": "player+0xad:u8 = 1 at 0x023158",
        "event_count_write": "player+0x9e:u8 = 1; player+0x9f:u8 = 0",
        "event_identity_writer": "0x01d768",
        "linked_actor_update": "0x0210c2 with d1=0x10",
        "standard_branch_guard": "player+0x5a pointer is nonzero and pointed actor class +0x02 is zero",
        "standard_branch_routine": "0x02404a",
        "presentation_selector_u8": 47,
        "presentation_records": special_records,
        "visible_presentation_runs": special_visible_runs,
        "rng_calls": [],
    },
    "active_state": {
        "class4b_allocation_guard": "animation event byte player+0x25 becomes zero and type-24 allocation succeeds",
        "class4b_allocation_writer": "0x0231c2..0x0231f2",
        "class4b_record_type_u8": 24,
        "class4b_class_u8": "0x4b",
        "class4b_variant_u8": 0,
        "class4b_position": "copy player x/y/z and facing; cross-link low-word pointers through +0x26",
        "class4b_first_visible": {"frame": 2805, "slot": "0x00ffc300"},
        "class3d_allocation_guard": "linked class-0x4b animation event +0x25 differs from player+0x66",
        "class3d_allocation_writer": "0x023220..0x023246",
        "class3d_record_type_u8": 24,
        "class3d_class_u8": "0x3d",
        "class3d_variant": "copy linked class-0x4b animation event +0x25",
        "class3d_position": "copy linked class-0x4b x/z and player facing into child+0x0c",
        "contact_attack_selector_u8": 11,
        "source_contact_frame": 2804,
        "source_audio_commands": ["0x0091", "0x0096"],
        "audio_command_frame": 2804,
    },
    "completion": {
        "terminal_guard": "signed animation branch player+0x24 < 0",
        "health_cost_routine": "0x01b492",
        "health_cost_s16": 6,
        "health_rule": "subtract six selected by player+0x9f; clamp negative or values below six to zero; copy health to +0x42",
        "action_local_flag_clear": "player+0x9e:u8 = 0 at 0x023260",
        "cleanup_frame": special_cleanup,
        "return_locomotion_frame": special_return,
    },
    "capture_identity": {
        "independent_captures": 2,
        "byte_identical": True,
        "files": {filename: digest(AIR_SPECIAL_A / filename)
                  for filename in special_files},
        "accepted_oracle07_sha256": digest(ORACLE07),
    },
    "mutation_controls": [
        "reject 0x024f04 as Predator Warrior ownership",
        "zero health rejects the special while Button1 remains independently eligible",
        "fewer than two qualifying new/current B1/B2/B3 bits rejects the special",
        "wrong character, state, contact latch, selector, class-0x4b writer, health cost, or fixed-frame completion changes the causal route",
    ],
    "fixed_frame_substitute_forbidden": True,
}

current_auth = json.loads(AUTH.read_text(encoding="ascii"))
old_weapon = current_auth.get("weapon_projectile_resource", {})
preserved_empty_effect = old_weapon.get("implementation_contract", {}).get(
    "empty_effect_variant1_contract", {})
require(preserved_empty_effect.get("class") == "0x10",
        "accepted class-0x10 empty-effect contract missing")

implementation_contract = {
    "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
    "source_input": {
        "button1_mask": "0x0010",
        "guard": "new Button1 edge in normal controllable player state after the shared B1+B2 guard",
        "physical_to_action_visible_frames_u8": 2,
        "native_input_pipeline_updates_u8": 1,
        "coffee_shop_control": {
            "physical_edge_frame": 2250,
            "action_entry_visible_frame": 2252,
            "parent_first_visible_frame": 2254,
        },
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
        "resource_debit_tick": 1,
        "parent_allocation_tick": 2,
        "presentation_timeline": player_presentation,
        "presentation_selector_contract": {
            "entry": "0x0241f0 then 0x0240e0..0x0240fa",
            "selection_tick": 0,
            "selector_range_u8": [4, 7],
            "selector_source": "nearest eligible record-12 distance bucket through table 0x024100",
            "animation_table_u32": "0x0015e32c",
            "selector_timelines": player_presentation_variants,
            "projectile_angle_and_player_presentation_share_scan": True,
            "coffee_shop_source_witness": {
                "frame": 2343,
                "selector_u8": 5,
                "animation_record": "0x0015e594",
            },
            "mutation_control": "selector 5 must not reuse selector-4 animation or assembly identity",
        },
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
            "position_rule": "decrement z high word, then add signed selector offsets from parent presentation table; negate x only when facing is nonzero",
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
            "coffee_shop_capture_projection": coffee_parent_projection,
            "coffee_shop_route_angles_u8": coffee_route_angles,
            "target_selection": {
                "entry": "0x0241f0",
                "source_window": window(opcodes, 0x0241F0, 0x024286),
                "record_type_u8": 12,
                "pool_base": "0xff9580",
                "pool_count_u8": 20,
                "pool_stride_u16": 192,
                "eligible_guard": "active != 0 AND u8(actor+0x04) < 4 AND u16(target_z-player_z+16) < 32 AND target is ahead for facing",
                "nearest_rule": "scan ascending slots; retain distance <= current unsigned u8 maximum 255, so equal distance selects the later slot",
                "distance_thresholds_u16": target_distance_thresholds,
                "presentation_selectors_u8": target_presentation_selectors,
                "selector_rule": "largest threshold <= nearest distance; no target returns 15",
                "angle_rule": "angle = 32-selector; facing zero negates modulo 64",
            },
            "base_motion_table_u32": "0x001fb7c0",
            "base_motion_vectors_s16": {
                str(angle): [s16(program, 0x001FB7C0 + angle * 4),
                             s16(program, 0x001FB7C2 + angle * 4)]
                for angle in range(17, 48)
            },
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
            "position_rule": "child x uses parent x plus facing-adjusted row x; child y and z both use parent z plus their signed row field",
        },
        "effect_allocation": parent_class49_effect,
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
        "registration_and_pair_eligibility": {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "spec_executable": True,
            "source_blocks": {
                "visibility_and_dispatch": window(opcodes, 0x0167ac, 0x016818),
                "record4_registration": window(opcodes, 0x016818, 0x016830),
                "record12_registration": window(opcodes, 0x01685e, 0x016896),
                "record4_record12_scheduler": window(opcodes, 0x01cbcc, 0x01cc3e),
                "pair_eligibility_and_contact": window(opcodes, 0x01d116, 0x01d1f8),
                "collision_identity_writer": window(opcodes, 0x01d768, 0x01d77a),
            },
            "types_and_signedness": {
                "actor_active": "actor+0x00:u8",
                "visibility_flag": "actor+0x01:u8",
                "world_x_high": "actor+0x10:u16 wrap arithmetic",
                "world_y_high": "actor+0x14:u16 wrap arithmetic",
                "camera_x": "global+0x0278:u16 wrap arithmetic",
                "camera_z": "global+0x027c:u16 wrap arithmetic",
                "defender_guard": "defender+0x6d:u8",
                "attacker_latch_index": "attacker+0x65:s8 branch then u8 index",
                "attacker_identity": "attacker+0x67:u8 nonzero wrapping sequence",
                "defender_latches": "defender+0x68:u8[8]",
                "defender_suppress": "defender+0x70:u8",
            },
            "visibility": {
                "x_guard": "u16(actor_x - camera_x + 0x0040) <= 0x0200",
                "y_guard": "u16(actor_y - camera_z + 0x0020) <= 0x0140",
                "pass_write": "actor+0x01:u8 = 1 at 0x0167d0",
                "fail_write": "actor+0x01:u8 = 0 at 0x0167e6",
                "update_order": [
                    "actor state/action/movement/animation",
                    "visibility guard and actor+0x01 write",
                    "record-type collision-list registration",
                    "record4-v-record12 collision scheduler",
                ],
            },
            "registration": {
                "record4": {
                    "guard": "actor+0x00:u8 == 1 after visibility pass",
                    "writer": "0x01681e..0x016828",
                    "list_pointer": "global+0x6e52:u16",
                    "count": "global+0x6e7d:u8",
                },
                "record12": {
                    "guard": "actor+0x00:u8 == 1 after visibility pass",
                    "writer": "0x016864..0x01686e",
                    "list_pointer": "global+0x6e5a:u16",
                    "count": "global+0x6e81:u8",
                },
            },
            "identity_writer": {
                "entry": "0x01d768",
                "rule": "clear actor+0x6e; preincrement global+0x020b:u8 until nonzero; copy to actor+0x67:u8",
                "coffee_shop_counter_before_parent_u8": 0x25,
                "assignments": [
                    {"frame": int(row["frame"]), "slot": "0x" + row["slot"],
                     "identity_u8": int(row["global_id820b"], 16)}
                    for row in identity_projection
                ],
            },
            "pair_guards": [
                "defender+0x6d:u8 < 4 in scheduler",
                "defender+0x00:u8 == 1",
                "defender+0x70:u8 == 0",
                "if attacker+0x65:s8 >= 0 then defender+0x68[index] != attacker+0x67",
                "attacker animation record byte +9 attack selector != 0",
                "defender animation record byte +8 hurt selector != 0",
                "current attack and hurt boxes overlap",
            ],
            "contact_writes": {
                "latch": "defender+0x68[attacker+0x65] = attacker+0x67 when index is nonnegative",
                "projectile": "scheduler writes attacker health -1 and actor+0x6e = 1 after a true pair result",
                "damage": "0x01d504 applies current attack-record damage before HIT/KO ownership",
            },
            "coffee_shop_projection": {
                "target_slot": "0xffa180",
                "absent_through_frame": 2295,
                "first_registered_frame": 2296,
                "first_contact_frame": 2306,
                "contact_attacker": "0xff8880",
                "contact_identity_u8": 0x2a,
                "health_s16": [87, 56],
            },
            "mutation_control": {
                "kind": "redirect only target 0xffa180 record12 list writes to 0xffa240",
                "writer": "0x01686c",
                "suppressed_writes": len(suppressed_list_writes),
                "frames": [2296, 2310],
                "list_count_unchanged_u8": 7,
                "target_first_contact_frame_before": 2306,
                "target_first_contact_frame_after": 2311,
                "actor_and_route_projection_unchanged_through_frame": 2305,
            },
            "rng_calls": [],
        },
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
    "special_causal_trace": {
        "action": "0x0800",
        "player_routine": "0x023132",
        "correction": "0x024f04 is a different-character body and is rejected",
        "guard": special_implementation_contract["source_input"]["guard_order"],
        "health_cost": "six via +0x9f event count and 0x01b492; values 1..5 clamp to zero",
        "actors": ["type24 class0x4b", "type24 class0x3d"],
        "rng": "no player, class-0x4b, or class-0x3d RNG calls",
        "zero_health": "special rejected; Button1 independently falls through to 0x0c00",
    },
    "special_implementation_contract": special_implementation_contract,
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
        {"class": "collision_registration", "result": "redirecting only target 0xffa180 out of the source record12 defender list preserves the actor/route prefix and shifts its first projectile damage from frame 2306 to 2311"},
        {"class": "resource_empty", "result": "0x1a00/0x1a02 and class-0x10 effect; no record-4 damaging family"},
    ],
    "mutation_controls": {
        "count": 14, "all_downstream_effects_asserted": True,
        "no_fixed_frame_result": True,
        "no_visible_weapon_inference_from_0xad": True,
        "wrong_character_rejected": True,
    },
    "provenance": {
        "capture_manifest_sha256": digest(RAW / "input_manifest.json"),
        "rejected_capture_manifest_sha256": digest(REJECTED / "input_manifest.json"),
        "capture_script_sha256": digest(ROOT / "tools/mame_capture_oracle11_player_weapon.lua"),
        "collision_registration_capture_script_sha256": digest(
            ROOT / "tools/mame_capture_oracle11_first_segment_progression.lua"),
        "collision_registration_evidence": {
            filename: digest(COLLISION_A / filename)
            for filename in COLLISION_FILES
        },
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
