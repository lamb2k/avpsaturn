#!/usr/bin/env python3
"""Close all route-reachable Round 1 type-12 enemy archetype authority."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from census_full_route import RouteState  # noqa: E402

BASE_A = ROOT / ".deps" / "mame" / "oracle11_round1_enemies_a"
BASE_B = ROOT / ".deps" / "mame" / "oracle11_round1_enemies_b"
FULL_ROUTE = ROOT / ".deps" / "mame" / "full_route"
ROUTE = ROOT / "data" / "oracle10_round1_route.json"
SCHEDULER = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"
ORACLE09 = ROOT / "data" / "oracle09_street_alien_state_facing_presentation.json"
ENCOUNTERS = ROOT / "data" / "oracle11_round1_encounter_route_authority.json"
AUDIO = ROOT / "data" / "oracle11_global_audio_trigger_owners.json"
HIT_KO_CONTRACT = ROOT / "tests" / "port_v2" / "combat" / "hit_ko" / "approved_contract.json"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
FIRST_SEGMENT_ACTION_A = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_t2a"
FIRST_SEGMENT_ACTION_B = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_t2b"
FIRST_SEGMENT_ACTION_SUPPRESS = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_t2s"
COFFEE_SHOP_SCENE_A = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs3a"
COFFEE_SHOP_SCENE_B = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs3b"
COFFEE_SHOP_SCENE_TIMER_SUPPRESS = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs3s"
COFFEE_SHOP_BOUNDS_A = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs14a"
COFFEE_SHOP_BOUNDS_B = ROOT / ".deps" / "mame" / "oracle11_progression_lifecycle_cs14b"
OUT = ROOT / "data" / "oracle11_round1_enemy_archetypes.json"
FILES = ("enemy_samples.tsv", "enemy_entries.tsv", "enemy_writes.tsv",
         "enemy_rng.tsv", "player_damage.tsv", "samples.tsv", "dispatches.tsv",
         "projectiles.tsv", "score_writes.tsv", "result.tsv")
CLASSES = {"0x00": 0x03F09C, "0x01": 0x0407B0,
           "0x06": 0x04956C, "0x1f": 0x060532}
EXPECTED = {
    "0x00": {"samples": 6397, "entries": 5821, "writes": 40876,
             "rng": 194, "damage": 2},
    "0x01": {"samples": 3796, "entries": 3304, "writes": 30904,
             "rng": 131, "damage": 1},
    "0x06": {"samples": 9482, "entries": 8855, "writes": 101686,
             "rng": 216, "damage": 13},
    "0x1f": {"samples": 28481, "entries": 29361, "writes": 153166,
             "rng": 352, "damage": 3},
}
CLASS1F_HIT_KO_RECORDS = (
    0x12DD50, 0x12D2F8, 0x12E214, 0x12E224,
    0x12E234, 0x12E244, 0x12E254, 0x12E268,
)
FIRST_SEGMENT_ACTION_FILES = (
    "progression_class1f_transitions.tsv", "progression_lifecycle_writes.tsv",
    "progression_result.tsv",
)
COFFEE_SHOP_SCENE_FILES = (
    "coffee_shop_scene_actors.tsv", "coffee_shop_scene_frames.tsv",
    "progression_class1f_action4_timers.tsv", "progression_result.tsv",
    "dispatches.tsv", "samples.tsv", "score_writes.tsv",
)
CLASS1F_ROUTE_SELECTORS = (0, 1, 34, 35, 36, 43, 52, 53, 54, 55, 56, 60, 62,
                            68, 69, 70, 71, 72, 73, 74, 76, 77)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def identity(path: Path) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    require(manifest["authority_family"] == "round1-enemy-archetypes",
            f"{path.name}: family identity drift")
    for filename in FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {"manifest_sha256": digest(manifest_path),
            "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def source_window(opcodes: bytes, pc: int) -> dict[str, object]:
    first = max(0, pc - 8)
    last = min(len(opcodes), pc + 16)
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(opcodes[first:last]).hexdigest()}


def aggregate_writers(capture: list[dict[str, str]], class_id: str,
                      opcodes: bytes) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in capture:
        if f"0x{row['class']}" == class_id:
            grouped[row["pc"]].append(row)
    result = []
    for pc, observed in sorted(grouped.items()):
        result.append({
            "pc": f"0x{pc}", "count": len(observed),
            "offsets": sorted({f"0x{row['offset']}" for row in observed}),
            "state_phase_contexts": sorted({
                f"{int(row['state']):04x}:{int(row['phase']):04x}"
                for row in observed}),
            "source_window": source_window(opcodes, int(pc, 16)),
        })
    return result


def animation_records(capture: list[dict[str, str]], class_id: str,
                      program: bytes) -> list[dict[str, object]]:
    observed = {}
    for row in capture:
        if f"0x{row['class']}" != class_id or int(row["anim"], 16) == 0:
            continue
        address = int(row["anim"], 16)
        assembly = int(row["assembly"], 16)
        hurt, attack = int(row["hurt"]), int(row["attack"])
        require(int.from_bytes(program[address + 4:address + 8], "big") == assembly
                and program[address + 8] == hurt and program[address + 9] == attack,
                f"{class_id}: animation record/source data drift at {address:08x}")
        observed[address] = {
            "animation_record": f"0x{address:08x}",
            "assembly": f"0x{assembly:08x}", "hurt_selector": hurt,
            "attack_selector": attack,
            "record_sha256": hashlib.sha256(program[address:address + 16]).hexdigest(),
            "classification": "SOURCE_CLOSED",
        }
    return [observed[key] for key in sorted(observed)]


def animation_record(program: bytes, address: int) -> dict[str, object]:
    record = program[address:address + 16]
    require(len(record) == 16, f"animation record {address:08x} outside program")
    return {
        "animation_record": f"0x{address:08x}",
        "timer_u16": int.from_bytes(record[0:2], "big"),
        "branch_s16": int.from_bytes(record[2:4], "big", signed=True),
        "assembly": f"0x{int.from_bytes(record[4:8], 'big'):08x}",
        "hurt_selector_u8": record[8], "attack_selector_u8": record[9],
        "record_sha256": hashlib.sha256(record).hexdigest(),
    }


def class1f_selector_sequence(program: bytes, selector: int) -> dict[str, object]:
    table = 0x12D152
    offset = int.from_bytes(program[table + selector * 2:
                                    table + selector * 2 + 2], "big",
                            signed=True)
    address = table + offset
    seen: set[int] = set()
    records = []
    for _ in range(64):
        require(address not in seen, f"selector {selector}: premature loop")
        seen.add(address)
        record = animation_record(program, address)
        record["movement_table_index_u8"] = program[address + 3] & 0x3f
        branch = record["branch_s16"]
        next_address = (int.from_bytes(program[address + 16:address + 20],
                                       "big") if branch < 0 else address + 16)
        record["next_animation_record"] = f"0x{next_address:08x}"
        records.append(record)
        if next_address in seen:
            return {"selector_u8": selector,
                    "start_animation_record": f"0x{records[0]['animation_record'][2:]}",
                    "terminal": "source pointer loop",
                    "records": records}
        address = next_address
    raise ValueError(f"selector {selector}: animation chain did not close")


def class1f_first_segment_action_contract(program: bytes,
                                           opcodes: bytes) -> dict[str, object]:
    def capture_identity(path: Path) -> dict[str, str]:
        return {name: digest(path / name) for name in FIRST_SEGMENT_ACTION_FILES}

    identity_a = capture_identity(FIRST_SEGMENT_ACTION_A)
    identity_b = capture_identity(FIRST_SEGMENT_ACTION_B)
    identity_s = capture_identity(FIRST_SEGMENT_ACTION_SUPPRESS)
    require(identity_a == identity_b,
            "class-0x1f first-segment action captures differ")
    scene_identity_a = {name: digest(COFFEE_SHOP_SCENE_A / name)
                        for name in COFFEE_SHOP_SCENE_FILES}
    scene_identity_b = {name: digest(COFFEE_SHOP_SCENE_B / name)
                        for name in COFFEE_SHOP_SCENE_FILES}
    scene_identity_s = {name: digest(COFFEE_SHOP_SCENE_TIMER_SUPPRESS / name)
                        for name in COFFEE_SHOP_SCENE_FILES}
    require(scene_identity_a == scene_identity_b,
            "Coffee Shop full-pool scene captures differ")
    bounds_name = "coffee_shop_class1f_source_bounds.tsv"
    bounds_identity_a = digest(COFFEE_SHOP_BOUNDS_A / bounds_name)
    bounds_identity_b = digest(COFFEE_SHOP_BOUNDS_B / bounds_name)
    require(bounds_identity_a == bounds_identity_b,
            "Coffee Shop class-0x1f bounds captures differ")
    bounds_rows = rows(COFFEE_SHOP_BOUNDS_A / bounds_name)
    first_a000 = [row for row in bounds_rows
                  if row["slot"] == "ffa000" and row["frame"] == "2310"]
    require([row["pc"] for row in first_a000] ==
                ["060c2e", "060c34", "060c3e", "060c70"] and
            all(row["actor_x_u16"] == "0258" and
                row["operand_address"] == "ff8278" and
                row["operand_u16"] == "02d0" and
                row["field01"] == "00" and row["fielda2"] == "00"
                for row in first_a000) and
            all(row["opcode_window_bytes"] ==
                opcodes[0x060C2E:0x060C68].hex() for row in first_a000),
            "Coffee Shop class-0x1f source-bounds operand/guard drift")
    baseline = rows(FIRST_SEGMENT_ACTION_A /
                    "progression_class1f_transitions.tsv")
    suppressed = rows(FIRST_SEGMENT_ACTION_SUPPRESS /
                      "progression_class1f_transitions.tsv")
    lifecycle = rows(FIRST_SEGMENT_ACTION_A /
                     "progression_lifecycle_writes.tsv")
    lifecycle_s = rows(FIRST_SEGMENT_ACTION_SUPPRESS /
                       "progression_lifecycle_writes.tsv")
    result = rows(FIRST_SEGMENT_ACTION_A / "progression_result.tsv")[0]
    result_s = rows(FIRST_SEGMENT_ACTION_SUPPRESS /
                    "progression_result.tsv")[0]
    require(len(baseline) == 337 and len(suppressed) == 627 and
            sum(row["suppressed"] == "1" for row in suppressed) == 179 and
            sum(row["pc"] == "061152" for row in lifecycle) == 22 and
            sum(row["pc"] == "061152" for row in lifecycle_s) == 23 and
            [int(result[key]) for key in
             ("main_spawn_transactions", "aux_spawn_transactions",
              "final_route")] == [15, 3, 4] and
            [int(result_s[key]) for key in
             ("main_spawn_transactions", "aux_spawn_transactions",
              "final_route")] == [16, 3, 4],
            "class-0x1f first-segment transition suppression drift")

    variants = [
        {"variant_u8": 0, "writes": {"a5_u8": 0, "a4_u8": 2}},
        {"variant_u8": 1, "writes": {"a5_u8": 0, "a4_u8": 2,
                                      "action_u8": 0x0c}},
        {"variant_u8": 2, "writes": {"a5_u8": 0, "a4_u8": 2,
                                      "action_u8": 0x0e, "airborne_u8": 1}},
        {"variant_u8": 3, "writes": {"a5_u8": 1, "a6_u8": 1,
                                      "a4_u8": 1, "style85_u8": 1}},
        {"variant_u8": 4, "writes": {"a5_u8": 1, "a6_u8": 1,
                                      "a4_u8": 1, "action_u8": 0x0c}},
        {"variant_u8": 5, "writes": {"a5_u8": 1, "a6_u8": 1,
                                      "a4_u8": 1, "action_u8": 0x0e,
                                      "airborne_u8": 1}},
        {"variant_u8": 6, "writes": {"a5_u8": 1, "action_u8": 0x10,
                                      "timer_aa_u8": 216, "a6_u8": 1,
                                      "a4_u8": 1, "style85_u8": 1,
                                      "animation_selector_u8": 1}},
        {"variant_u8": 7, "writes": {"a5_u8": 1, "action_u8": 0x12,
                                      "timer_aa_u8": 216, "a6_u8": 1,
                                      "a4_u8": 1, "style85_u8": 0,
                                      "animation_selector_u8": 0}},
        {"variant_u8": 8, "writes": {"a5_u8": 1, "action_u8": 0x14,
                                      "timer_aa_u8": "entry_delay_u8",
                                      "a6_u8": 1, "a4_u8": 1,
                                      "style85_u8": 1,
                                      "animation_selector_u8": 1}},
        {"variant_u8": 9, "writes": {"a5_u8": 1, "action_u8": 0x1c,
                                      "bound_b2_u16": "0x0420 + (rng&0x007f)",
                                      "a6_u8": 1, "a4_u8": 1,
                                      "style85_u8": "rng_bit2",
                                      "animation_selector_rule":
                                          "0x44/0x48 plus a4_u8"}},
    ]
    action_targets = [0x0607B8, 0x06084E, 0x0608B0, 0x0609F6,
                      0x060A08, 0x060A1C, 0x060A2A, 0x060A86,
                      0x060B1A, 0x060B28, 0x060B36, 0x060C2E,
                      0x060D6A, 0x060D7E, 0x060D88, 0x060DE0]
    sequences = [class1f_selector_sequence(program, selector)
                 for selector in CLASS1F_ROUTE_SELECTORS]
    movement_ids = sorted({record["movement_table_index_u8"]
                           for sequence in sequences
                           for record in sequence["records"] if
                           record["movement_table_index_u8"] != 0})
    movement_tables = []
    for table_id in movement_ids:
        pointer = int.from_bytes(program[0x17188 + table_id * 4:
                                         0x1718C + table_id * 4], "big")
        vectors = []
        for direction in range(32):
            first = pointer + direction * 4
            vectors.append({
                "direction_u8": direction,
                "x_delta_s16": int.from_bytes(program[first:first + 2],
                                                "big", signed=True),
                "y_delta_s16": int.from_bytes(program[first + 2:first + 4],
                                                "big", signed=True),
            })
        movement_tables.append({"table_index_u8": table_id,
                                "source_address": f"0x{pointer:06x}",
                                "fixed_point_scale": "signed s16 << 8",
                                "vectors": vectors})
    writer_counts = Counter(row["pc"] for row in baseline)
    require(opcodes[0x06083A:0x06084E].hex() ==
            "600008fe1d7c00080006422e00077034600008ee",
            "class-0x1f action-0 selector body drift")
    require(opcodes[0x06084E:0x0608B0].hex() ==
            "4a2e00a266140c6e05f0001062464a2e0001672a1d7c000100a2082d000000196614302e0010906d0278064000700c400260622060086100060e6600064e610006a8610007a04eb9000165c43d6e001400184e751cbc00022d7c0600000000044e75",
            "class-0x1f action-2 body drift")
    require(opcodes[0x0165C4:0x016620].hex() ==
            "536e000a6654206e001c41e800104a6e00246a0220502d48001c3d50000a3d6800020024102e00250240003f672ce54841fa0b9220700000102e000c0240001fe54841f00000301848c0e180d1ae0010301048c0e180d1ae00144e75",
            "class-0x1f animation/movement helper drift")
    jump_vectors = [int.from_bytes(opcodes[address:address + 4], "big",
                                  signed=True)
                    for address in range(0x060AC8, 0x060AD8, 4)]
    require(jump_vectors == [-0x00010000, -0x00014000,
                             -0x00018000, -0x00020000],
            "class-0x1f action-0x0e jump table drift")
    action4_random_groups = [int.from_bytes(opcodes[address:address + 2],
                                             "big")
                             for address in range(0x0608F0, 0x060930, 2)]
    action4_group_offsets = [int.from_bytes(program[0x06099C + index:
                                                     0x06099E + index], "big")
                             for index in range(0, 8, 2)]
    action4_selector_groups = []
    for offset in action4_group_offsets:
        address = 0x06099C + offset
        selectors = []
        while True:
            value = int.from_bytes(program[address:address + 2], "big")
            address += 2
            if value == 0xffff:
                break
            selectors.append(value)
        action4_selector_groups.append(selectors)
    require(action4_random_groups ==
                [0] * 6 + [2] * 6 + [4] * 12 + [6] * 8 and
            action4_group_offsets == [12, 16, 20, 30] and
            action4_selector_groups == [[55], [56], [43, 43, 43, 55],
                                        [43, 43, 56]],
            "class-0x1f action-0x04 selector program drift")
    stage_offsets = list(program[0x0BC53A:0x0BC55A])
    timer_rows = [list(program[0x0BC55A + offset:
                               0x0BC55A + offset + 32])
                  for offset in sorted(set(stage_offsets))]
    timer_baseline = rows(COFFEE_SHOP_SCENE_A /
                          "progression_class1f_action4_timers.tsv")
    timer_mutant = rows(COFFEE_SHOP_SCENE_TIMER_SUPPRESS /
                        "progression_class1f_action4_timers.tsv")
    timer_events = [row["event"] for row in timer_baseline]
    caller = next(row for row in timer_baseline
                  if row["event"] == "caller_write")
    timer_write = next(row for row in timer_baseline
                       if row["event"] == "write" and row["pc"] == "060944")
    suppressed_write = next(row for row in timer_mutant
                            if row["event"] == "write" and
                            row["pc"] == "060944")
    baseline_scene_rows = rows(COFFEE_SHOP_SCENE_A /
                               "coffee_shop_scene_actors.tsv")
    mutant_scene_rows = rows(COFFEE_SHOP_SCENE_TIMER_SUPPRESS /
                             "coffee_shop_scene_actors.tsv")
    first_scene_difference = next(
        (index, before, after) for index, (before, after) in
        enumerate(zip(baseline_scene_rows, mutant_scene_rows))
        if before != after)
    require(stage_offsets ==
                [0] * 5 + [32] * 8 + [64] * 6 + [96] * 5 + [128] * 8 and
            len(timer_rows) == 5 and all(len(row) == 32 for row in timer_rows) and
            timer_events[:8] == ["entry", "rng_masked", "stage_read",
                                 "table_lookup", "result", "caller_write",
                                 "caller_after_write", "write"] and
            caller["frame"] == "2797" and caller["slot"] == "ffa240" and
            caller["stage_parameter"] == "0009" and caller["rng"] == "5cc1" and
            int(caller["d0"], 16) == 6 and timer_write["data"] == "00000606" and
            suppressed_write["suppressed"] == "1" and
            scene_identity_a["score_writes.tsv"] ==
                scene_identity_s["score_writes.tsv"] and
            scene_identity_a["dispatches.tsv"] ==
                scene_identity_s["dispatches.tsv"] and
            first_scene_difference[1]["frame"] == "2798" and
            first_scene_difference[1]["slot"] == "ffa240" and
            first_scene_difference[1]["action_timer"] == "0600" and
            first_scene_difference[2]["action_timer"] == "0000",
            "class-0x1f action-0x04 timer capture drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": ("all route-reachable class-0x1f action dispatch required "
                  "by the first Round 1 segment"),
        "capture_identity": {"completion_a": identity_a,
                             "completion_b": identity_b,
                             "byte_identical": True,
                             "writer_0x0607e8_suppression": identity_s,
                             "coffee_shop_scene_a": scene_identity_a,
                             "coffee_shop_scene_b": scene_identity_b,
                             "coffee_shop_scene_byte_identical": True,
                             "action4_timer_suppression": scene_identity_s,
                             "source_bounds_a": {bounds_name:
                                                  bounds_identity_a},
                             "source_bounds_b": {bounds_name:
                                                  bounds_identity_b},
                             "source_bounds_byte_identical": True},
        "record_layout": {"state_inner_u16": "actor+0x04",
                          "action_substate_u16": "actor+0x06",
                          "facing_u8": "actor+0x0f",
                          "x_fp_s32_16_16": "actor+0x10",
                          "y_fp_s32_16_16": "actor+0x14",
                          "z_s16": "actor+0x18",
                          "animation_timer_u16": "actor+0x0a",
                          "animation_record_u32": "actor+0x1c",
                          "animation_branch_s16": "actor+0x24",
                          "target_low_word_u16": "actor+0x28",
                          "action_timer_u8": "actor+0x2a",
                          "health_s16": "actor+0x40"},
        "initializer": {"entry": "0x060546", "rng_entry": "0x017c5e",
                        "rng_calls_per_actor": 1,
                        "variant_dispatch_table": "0x060606",
                        "variants": variants,
                        "source_window": source_window(opcodes, 0x060546)},
        "current_dispatch": {
            "entry": "0x060772", "action_table": "0x060798",
            "action_targets": [{"action_u8": index * 2,
                                "target": f"0x{target:06x}"}
                               for index, target in enumerate(action_targets)],
            "action_0_branch_order": [
                "if s16(0xff9a1c)==0 enter source special state 0x0a",
                "if an active P1 is within x [-32,+32] and z [-12,+12] and P1+0x96==0 enter action 0x04",
                "if a5_u8 != facing_u8 enter action 0x0a and toggle facing",
                "if a3_u8 == style85_u8 enter action 0x02; a6_u8!=0 promotes it to action 0x16 and b0_u8=2",
                "otherwise a3_u8!=0 enters action 0x08; zero enters action 0x06"],
            "movement_action_0x16_order": [
                "enforce x/camera visibility guard and release through outer state 0x0600 when outside",
                "apply source actor-separation helper 0x060f36",
                "derive direction_u8 at actor+0x0c through 0x061032",
                "advance animation and movement through 0x0165c4",
                "copy y high word to z",
                "on negative animation branch with timer_u16==1 decrement b0_u8",
                "when b0_u8 reaches zero evaluate target-side guard, then consume exactly one RNG call for branch selection or attack timing"],
            "release_guard": ("outer state 0x0600:0000 decrements "
                              "living_enemy_count_u16 then tail-calls 0x0176b4"),
            "required_state_contexts": [
                "0x0200:0000", "0x0200:0200", "0x0200:0400",
                "0x0200:0402", "0x0200:0404", "0x0200:0406",
                "0x0200:0408", "0x0200:0600", "0x0200:0800",
                "0x0200:0a00", "0x0200:0c00", "0x0200:0c02",
                "0x0200:0c04", "0x0200:0e00", "0x0200:0e02",
                "0x0200:0e04", "0x0200:1000", "0x0200:1200",
                "0x0200:1400", "0x0200:1402", "0x0200:1404",
                "0x0200:1406", "0x0200:1408", "0x0200:1600",
                "0x0200:1800", "0x0200:1a00", "0x0200:1c00",
                "0x0200:1e00"],
            "source_windows": {f"0x{target:06x}":
                               source_window(opcodes, target)
                               for target in action_targets},
        },
        "animation_selector_table": {"address": "0x12d152",
                                     "selectors": sequences},
        "movement_tables": movement_tables,
        "attack_timer_table_u8": list(opcodes[0x060D3C:0x060D4C]),
        "action_programs": {
            "source_bounds": {
                "entry_pc": "0x060c2e",
                "activation_field_u8": "actor+0x01",
                "latched_field_u8": "actor+0xa2",
                "initial_branch_order": [
                    "if actor+0xa2_u8 != 0 skip the x_max and activation tests",
                    "compare actor+0x10_u16 to x_max_u16; unsigned above releases",
                    "if actor+0x01_u8 == 0 pass without the camera-relative test",
                    "otherwise write 1 to actor+0xa2_u8 and continue"],
                "phase_guard_field_u8": "0xff8019",
                "phase_guard_mask_u8": 1,
                "phase_guard_zero_path": "camera-relative unsigned comparison",
                "phase_guard_nonzero_path": "player proximity helper 0x060e94; nonzero enters 0x060ed8 rather than release",
                "camera_operand_u16": "0xff8278",
                "x_max_u16": 0x05f0,
                "camera_relative_bias_u16": 0x0070,
                "camera_relative_span_u16": 0x0260,
                "failure_outer_state_u16": 0x0600,
                "comparison": "unsigned word",
                "coffee_shop_observation": {
                    "source_frame": 2310,
                    "source_slot": "0x00ffa000",
                    "actor_x_u16": "0x0258",
                    "camera_operand_u16": "0x02d0",
                    "activation_field_u8": 0,
                    "latched_field_u8": 0,
                    "result": "pass after x_max; camera-relative test skipped"}},
            "animation_movement_helper_0x0165c4": {
                "entry_pc": "0x0165c4",
                "source_window": source_window(opcodes, 0x0165C4),
                "source_body_sha256":
                    hashlib.sha256(opcodes[0x0165C4:0x016620]).hexdigest(),
                "timer_field_u16": "actor+0x0a",
                "record_field_u32": "actor+0x1c",
                "branch_field_s16": "actor+0x24",
                "direction_field_u8": "actor+0x0c",
                "x_field_s32_16_16": "actor+0x10",
                "y_field_s32_16_16": "actor+0x14",
                "branch_order": [
                    "decrement timer_u16 once",
                    "if timer_u16 remains nonzero return without record advance or movement",
                    "advance record pointer by 16 bytes",
                    "if prior branch_s16 was negative replace the advanced pointer with its u32 jump target",
                    "write the next record pointer, timer_u16, and branch_s16",
                    "movement_table_u8 = low 6 bits of next record byte +3",
                    "if movement_table_u8 is zero return",
                    "direction_u8 = low 5 bits of actor+0x0c",
                    "read signed x/y deltas from movement_table[direction_u8]",
                    "add each signed delta shifted left 8 to actor x/y s32 16.16"],
                "movement_cadence":
                    "only on timer expiry after binding the next animation record",
                "movement_record": "newly bound next animation record",
                "movement_scale": "signed s16 << 8",
                "return_path_without_movement":
                    "timer remains nonzero or next record movement_table_u8 is zero"},
            "direction_helper_0x061032": {
                "upper_lane_u16": 0x0140,
                "lower_lane_u16": 0x00e8,
                "upper_directions_by_a5_u8": [0x16, 0x0a],
                "lower_directions_by_a5_u8": [0x1a, 0x06],
                "middle_band_preserves_direction": True},
            "action_0x00": {
                "near_player_x_bias_u16": 0x20,
                "near_player_x_span_u16": 0x40,
                "near_player_z_bias_u16": 0x0c,
                "near_player_z_span_u16": 0x18,
                "turn_selectors_by_style_u8": [34, 35],
                "idle_selectors_by_a3_u8": [36, 52],
                "movement_selector_base_by_style_u8": [0x44, 0x48],
                "movement_selector_addend": "a4_u8",
                "movement_action_u8": 0x16,
                "movement_loops_u8": 2},
            "action_0x02": {
                "source_bounds": True, "actor_separation_helper": "0x060f36",
                "direction_helper": "0x061032",
                "animation_movement_helper": "0x0165c4",
                "copy_y_high_word_to_z": True},
            "action_0x04": {
                "substates_u8": [0, 2, 4, 6, 8],
                "rng_group_mask_u16": 0x003e,
                "rng_group_table_u16": action4_random_groups,
                "group_offsets_u16": action4_group_offsets,
                "selector_groups_u16": action4_selector_groups,
                "timer_helper": "0x0bc416",
                "timer_stage_parameter_field": "0xff81ea:u16",
                "timer_stage_offset_table_address": "0x0bc53a",
                "timer_stage_offsets_u8": stage_offsets,
                "timer_table_address": "0x0bc55a",
                "timer_rows_u8": timer_rows,
                "timer_rng_mask_u16": 0x001f,
                "timer_rng_calls": 1,
                "coffee_shop_observation": {
                    "source_frame": 2797,
                    "source_slot": "0x00ffa240",
                    "stage_parameter_u16": 9,
                    "stage_offset_u8": 32,
                    "rng_seed_before_u16": "0xc965",
                    "rng_seed_after_u16": "0x5cc1",
                    "rng_index_u8": 1,
                    "timer_result_u8": 6,
                    "writer_pc": "0x060944"},
                "terminal_actions": {
                    "phase_0_player_guard_clear": "next action 0",
                    "phase_6": "next phase 0",
                    "phase_8": "next action 0 and style85_u8=0"}},
            "actions_0x06_0x08_0x0a": {
                "terminal_guard": "animation_branch_s16 < 0",
                "next_action_u8": 0,
                "style85_result_by_action": {"0x06": 0, "0x08": 1,
                                               "0x0a": "unchanged"}},
            "action_0x0c": {
                "substates_u8": [0, 2, 4], "initial_selector_u8": 35,
                "middle_selector_u8": 36, "y_delta_s32_16_16": -0x2000,
                "terminal_next_action_u8": 0},
            "action_0x0e": {
                "substates_u8": [0, 2, 4], "initial_selector_u8": 77,
                "landing_selector_u8": 62,
                "z_velocity_table_s32_16_16": jump_vectors,
                "y_velocity_s32_16_16": 0x00038000,
                "y_acceleration_s32_16_16": -0x00008000,
                "initial_y_add_s16": 0x20,
                "rng_index": "(rng_u16 & 0x000c) selects one signed 16.16 long",
                "velocity_axis": "actor+0x18 signed 16.16 lane/z; actor+0x10 x is unchanged",
                "airborne_step": "z_fp += z_velocity; y_fp += y_velocity; y_velocity += y_acceleration; continue while u16(z_high) < u16(y_high)",
                "landing_writes": ["y_high = z_high", "coordinate_mode_u8 = 0", "substate_low_u8 += 2", "bind selector 62"],
                "terminal_style85_u8": 1,
                "terminal_next_action_u8": 0,
                "rng_calls": 1},
            "actions_0x10_0x12": {
                "timer_field": "timer_aa_u8",
                "decrement": 1, "zero_next_action_u8": 0},
            "action_0x16": {
                "source_bounds": True, "actor_separation_helper": "0x060f36",
                "direction_helper": "0x061032",
                "animation_movement_helper": "0x0165c4",
                "copy_y_high_word_to_z": True,
                "loop_guard": "animation_branch_s16 < 0 and animation_timer_u16 == 1",
                "loop_counter": "b0_u8", "target_compare_helper": "0x060cd2",
                "rng_mask_branch_u16": 3, "rng_mask_timer_u16": 15,
                "attack_action_u8": 0x18,
                "attack_selectors_by_style_u8": [0, 1]},
            "action_0x18": {
                "timer_field": "action_timer_u8", "decrement": 1,
                "nonzero_helper": "0x016536", "zero_next_action_u8": 0},
            "action_0x1a": {
                "terminal_guard": "animation_branch_s16 < 0",
                "next_action_u8": 0x18,
                "selectors_by_style_u8": [0, 1]},
            "action_0x1c": {
                "source_bounds": True,
                "animation_movement_helper": "0x0165c4",
                "copy_y_high_word_to_z": True,
                "terminal_guard": "animation_branch_s16 < 0 and animation_timer_u16 == 1 and bound_b2_u16 <= x_high_word_u16",
                "next_action_u8": 0x1e,
                "selectors_by_style_u8": [0, 1]},
            "action_0x1e": {"animation_helper": "0x016536"},
        },
        "observed_state_writer_counts": dict(sorted(writer_counts.items())),
        "suppression_control": {
            "writer_pc": "0x0607e8", "suppressed_writes": 179,
            "baseline_transition_rows": 337,
            "mutant_transition_rows": 627,
            "baseline_lifecycle_releases": 22,
            "mutant_lifecycle_releases": 23,
            "baseline_main_aux_spawns": [15, 3],
            "mutant_main_aux_spawns": [16, 3],
            "baseline_final_route": 4, "mutant_final_route": 4,
            "fixed_frame_substitute": False,
            "action4_timer": {
                "writer_pc": "0x060944",
                "suppressed_writes": 1,
                "baseline_timer_u8": 6,
                "mutant_timer_u8": 0,
                "first_difference_frame": 2798,
                "first_difference_slot": "0x00ffa240",
                "score_unchanged": True,
                "audio_dispatch_unchanged": True,
                "route_exit_unchanged": True},
        },
        "mutation_controls": ["wrong variant initializer", "wrong action target",
                              "wrong action-0 branch order", "wrong selector start",
                              "wrong record timer", "wrong record branch",
                              "wrong movement table", "wrong movement scale",
                              "wrong attack timer table", "fixed-frame release",
                              "single synthetic current actor",
                              "wrong action-4 stage parameter",
                              "wrong action-4 timer row",
                              "wrong action-4 RNG index",
                              "suppressed action-4 timer write",
                              "wrong source-bounds activation guard",
                              "wrong animation movement cadence"],
    }


def accepted_class1f_hit_ko_records(program: bytes) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Bind accepted Port V2 HIT/KO records to exact source record fields."""
    contract = json.loads(HIT_KO_CONTRACT.read_text(encoding="ascii"))
    manifest_path = ROOT / contract["source_manifest"]
    require(contract["source_manifest_schema"] == 4 and
            digest(manifest_path) == contract["source_manifest_sha256"] and
            contract["target"] == {"set": "avspu", "revision": "USA 940520",
                                   "type": 12, "class": 31} and
            contract["hit"]["anim_record"] == CLASS1F_HIT_KO_RECORDS[0] and
            contract["ko"]["anim_record"] == CLASS1F_HIT_KO_RECORDS[2],
            "accepted class-0x1f HIT/KO interface drift")
    records = []
    for address in CLASS1F_HIT_KO_RECORDS:
        source = animation_record(program, address)
        records.append({
            "animation_record": source["animation_record"],
            "assembly": source["assembly"],
            "hurt_selector": source["hurt_selector_u8"],
            "attack_selector": source["attack_selector_u8"],
            "record_sha256": source["record_sha256"],
            "classification": "SOURCE_CLOSED",
        })
    return records, {
        "accepted_port_v2_contract": HIT_KO_CONTRACT.relative_to(ROOT).as_posix(),
        "accepted_port_v2_contract_sha256": digest(HIT_KO_CONTRACT),
        "accepted_writer_manifest": contract["source_manifest"],
        "accepted_writer_manifest_sha256": contract["source_manifest_sha256"],
        "record_addresses": [row["animation_record"] for row in records],
        "implementation_fields": ["assembly", "hurt_selector", "attack_selector"],
        "fixed_frame_presentation_forbidden": True,
    }


def initial_class1f_presentation_fields(
        slots: tuple[tuple[str, int, int, int, int], ...]
) -> dict[str, dict[str, object]]:
    """Read implementation fields from the accepted cadence-1 route capture."""
    state = RouteState(FULL_ROUTE)
    workram = None
    try:
        for record in state.frames():
            if record["frame"] == 2092:
                workram = state.current["workram"]
                break
    finally:
        state.close()
    require(workram is not None, "accepted class-0x1f presentation frame missing")
    expected_palettes = [16, 17, 17, 18, 17, 16, 18, 17, 19, 19]
    result: dict[str, dict[str, object]] = {}
    for (slot, phase, x, yz, _delay), palette in zip(slots,
                                                     expected_palettes):
        offset = int(slot, 16) & 0xFFFF
        raw = workram[offset:offset + 0xC0]
        require(len(raw) == 0xC0, f"class-0x1f presentation {slot} short read")
        u8 = lambda inner: raw[inner]
        u16 = lambda inner: int.from_bytes(raw[inner:inner + 2], "big")
        require(u8(0x00) == 1 and u8(0x02) == 0x1F and u8(0x08) == 12 and
                u16(0x04) == 0x0200 and u16(0x06) == phase and
                u16(0x10) == x and u16(0x14) == yz and u16(0x18) == yz and
                u8(0x0D) == 1 and u8(0x0E) == palette and
                u8(0x0F) == 1 and u16(0x2E) == 0x8000,
                f"class-0x1f presentation fields drift at {slot}")
        result[slot] = {
            "source_frame": 2092,
            "coordinate_mode_u8": u8(0x0D),
            "palette_u8": u8(0x0E),
            "object_or_u16": f"0x{u16(0x2E):04x}",
            "source_record_sha256": hashlib.sha256(raw).hexdigest(),
        }
    return result


def initial_class1f_transition_contract(samples: list[dict[str, str]],
                                        rng: list[dict[str, str]],
                                        opcodes: bytes,
                                        program: bytes) -> dict[str, object]:
    slots = (
        ("ff9d00", 0x1000, 632, 296, 0), ("ff9dc0", 0x1000, 616, 304, 0),
        ("ff9e80", 0x1000, 640, 256, 0), ("ff9f40", 0x1200, 696, 264, 0),
        ("ffa000", 0x1200, 600, 300, 0), ("ffa0c0", 0x1200, 648, 280, 0),
        ("ffa180", 0x1200, 640, 320, 0), ("ffa240", 0x1400, 744, 280, 9),
        ("ffa300", 0x1400, 704, 296, 3), ("ffa3c0", 0x1400, 656, 312, 16),
    )
    presentation_fields = initial_class1f_presentation_fields(slots)
    actors = []
    for slot, phase, x, yz, delay in slots:
        row = next((item for item in samples if item["slot"] == slot and
                    item["class"] == "1f" and int(item["frame"]) == 2074), None)
        require(row is not None and int(row["state"]) == 0x0200 and
                int(row["phase"]) == phase and int(row["facing"]) == 1 and
                int(row["x"]) == x and int(row["y"]) == yz and
                int(row["z"]) == yz and int(row["timer"]) == delay,
                f"class-0x1f initial actor {slot} drift")
        fields = presentation_fields[slot]
        actors.append({"source_slot": f"0x00{slot}", "state_u16": 0x0200,
                       "substate_u16": phase, "facing_u8": 1,
                       "x_s16": x, "y_s16": yz, "z_s16": yz,
                       "entry_delay_u8": delay,
                       "coordinate_mode_u8": fields["coordinate_mode_u8"],
                       "palette_u8": fields["palette_u8"],
                       "object_or_u16": fields["object_or_u16"],
                       "presentation_source_frame": fields["source_frame"],
                       "presentation_source_record_sha256":
                           fields["source_record_sha256"]})
    first_rng = [item for item in rng if item["class"] == "1f" and
                 item["pc"] == "0605be" and int(item["frame"]) == 2073]
    expected_seeds = ["a998", "fc94", "f589", "e069", "a10a",
                      "e3ed", "ab98", "029a", "07a1", "16b7"]
    require([(item["slot"], item["seed"]) for item in first_rng] ==
            [(item[0], seed) for item, seed in zip(slots, expected_seeds)],
            "class-0x1f initialization RNG order drift")
    audio = json.loads(AUDIO.read_text(encoding="ascii"))
    audio_edges = []
    for group in audio["trigger_groups"]:
        contexts = group["transition_guard"]["contexts"]
        if any(context["class_u8"] == "0x1f" and
               context["source_call"]["address"] == "0x060bba" and
               context["substate_u16"] == 0x1404 for context in contexts):
            audio_edges.append({"origin_record": group["origin_a6"],
                                "source_frame": group["first_frame"],
                                "command": group["command"],
                                "arguments": group["argument_variants"][0],
                                "source_call": "0x060bba",
                                "semantic_sound_name": "UNKNOWN"})
    require([(edge["origin_record"], edge["source_frame"], edge["command"])
             for edge in audio_edges] == [("0xffa240", 2255, "0x004d"),
                                          ("0xffa300", 2249, "0x0118")],
            "class-0x1f initial audio edge drift")
    def sequence(selector: int, start: int, count: int, terminal: str):
        return {"selector_u8": selector, "terminal_rule": terminal,
                "records": [animation_record(program, start + 16 * index)
                            for index in range(count)]}
    sequences = [
        sequence(0, 0x12e8a8, 4, "negative branch loops to selector first record"),
        sequence(1, 0x12e8ec, 4, "negative branch loops to selector first record"),
        sequence(52, 0x12e65c, 4, "negative branch self-loops while substate timer owns release"),
        sequence(60, 0x12e944, 3, "state guard advances before terminal record timer is animated"),
        sequence(62, 0x12e9cc, 2, "state guard advances before terminal record timer is animated"),
        sequence(76, 0x12ea24, 5, "terminal record holds until landing guard"),
    ]
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "accepted_audio_evidence_sha256": digest(AUDIO),
        "scope": "initial 0x0200:1000, 0x0200:1200 and 0x0200:1400 bodies",
        "actors": actors,
        "initialization": {
            "dispatch": "0x060532", "common_entry": "0x0605be",
            "rng_entry": "0x017c5e", "rng_calls": 10,
            "rng_seed_after_each_source_slot": [f"0x{seed}" for seed in expected_seeds],
            "scheduler_order": "type-12 ascending fixed-pool source slot",
            "phase_0x1000": {"entry": "0x0606aa", "reads": ["actor+0x06 state/substate"],
                "writes": {"actor+0xa5_u8": 1, "actor+0xa6_u8": 1,
                           "actor+0xa4_u8": 1, "actor+0xaa_u8": 216,
                           "actor+0x85_u8": 1}, "animation_selector_u8": 1},
            "phase_0x1200": {"entry": "0x0606d4", "reads": ["actor+0x06 state/substate"],
                "writes": {"actor+0xa5_u8": 1, "actor+0xa6_u8": 1,
                           "actor+0xa4_u8": 1, "actor+0xaa_u8": 216,
                           "actor+0x85_u8": 0}, "animation_selector_u8": 0},
            "phase_0x1400": {"entry": "0x0606fc", "reads": ["actor+0x2b_u8 entry delay"],
                "writes": {"actor+0xa5_u8": 1, "actor+0xa6_u8": 1,
                           "actor+0xa4_u8": 1, "actor+0xaa_u8": "actor+0x2b_u8",
                           "actor+0x85_u8": 1}, "animation_selector_u8": 1},
            "common_presentation_entry": "0x06113a",
            "presentation_field_offsets": {
                "coordinate_mode_u8": "actor+0x0d",
                "palette_u8": "actor+0x0e",
                "object_or_u16": "actor+0x2e",
            },
            "accepted_presentation_frame": 2092,
            "fixed_frame_initialization_forbidden": True,
        },
        "phase_0x1000_and_0x1200": {
            "entries": ["0x060b1a", "0x060b28"],
            "guard": "predecrement actor+0xaa_u8; zero clears actor+0x06_u16",
            "reads": ["actor+0xaa_u8", "current animation record"],
            "writes": ["actor+0xaa_u8", "actor+0x06_u16 on zero",
                       "animation timer/branch/record/assembly/hurt/attack while nonzero"],
            "movement": "x/y/z unchanged", "collision_selectors": [0],
            "next_state_substate": "0x0200:0000", "rng_calls": 0,
            "source_observed_clear_frame": 2287,
            "source_observed_next_dispatch": {
                "frame": 2288, "state_u16": 0x0200,
                "substate_u16": 0x1600,
            },
        },
        "phase_0x1400": {
            "dispatch": "0x060b36", "substate_offset_u8": "actor+0x07",
            "substates": [
                {"substate_u16": 0x1400, "entry": "0x060b4c",
                 "guard": "global route byte 0xff8209 equals 2, then predecrement actor+0xaa_u8 equals zero",
                 "reads": ["global 0xff8209_u8", "actor+0xaa_u8"],
                 "writes": ["actor+0xaa_u8", "actor+0x07_u8 += 2"],
                 "animation_selector_u8": 60, "next_substate_u16": 0x1402},
                {"substate_u16": 0x1402, "entry": "0x060b68",
                 "guard": "signed animation branch actor+0x24 is negative",
                 "writes": {"actor+0x07_u8_add": 2, "actor+0x5c_u8": 1,
                            "x_velocity_s32_16_16": 0x00030000,
                            "y_velocity_s32_16_16": 0x00091000,
                            "y_acceleration_s32_16_16": -0x00005000,
                            "actor+0x2a_u8": 42},
                 "facing_rule": "if actor+0x0f_u8 equals 0, negate x velocity",
                 "animation_selector_u8": 76, "next_substate_u16": 0x1404},
                {"substate_u16": 0x1404, "entry": "0x060bae",
                 "guard": "predecrement actor+0x2a_u8 equals zero and global 0xff9a10_u8 equals zero",
                 "reads": ["actor+0x2a_u8", "global 0xff9a10_u8", "actor position/facing"],
                 "writes": ["actor+0x2a_u8", "global 0xff9a10_u8 = 1",
                            "two type-24 class-0x4e variant-4 allocation attempts"],
                 "audio_edges": audio_edges,
                 "movement_arithmetic": "x_fp += x_velocity; y_fp += y_velocity; y_velocity += y_acceleration; signed 16.16 high words own x/y",
                 "landing_guard": "unsigned compare: continue while z_u16 < y_u16; otherwise y = z",
                 "landing_writes": {"actor+0x07_u8_add": 2, "actor+0x5c_u8": 0},
                 "animation_selector_u8_on_landing": 62,
                 "next_substate_u16": 0x1406},
                {"substate_u16": 0x1406, "entry": "0x060c04",
                 "guard": "signed animation branch actor+0x24 is negative",
                 "writes": {"actor+0xaa_u16": 64, "actor+0x07_u8_add": 2},
                 "animation_selector_u8": 52, "next_substate_u16": 0x1408},
                {"substate_u16": 0x1408, "entry": "0x060c1c",
                 "guard": "predecrement actor+0xaa_u16 equals zero",
                 "writes": ["actor+0xaa_u16", "actor+0x06_u16 = 0 on zero",
                            "animation timer/branch/record/assembly/hurt/attack while nonzero"],
                 "next_state_substate": "0x0200:0000",
                 "source_observed_clear": {
                     "slot": "0x00ffa3c0", "frame": 2351,
                     "state_u16": 0x0200, "substate_u16": 0,
                 },
                 "source_observed_next_dispatch": {
                     "slot": "0x00ffa3c0", "frame": 2352,
                     "state_u16": 0x0200, "substate_u16": 0x0600,
                 }},
            ],
            "collision_selectors_by_animation": {"60": [2, 10], "76": [0],
                "62": [11, 2], "52": [1, 4, 2]},
            "rng_calls_inside_transition": 0,
            "effect_dependency": "data/oracle11_round1_auxiliary_authority.json#/first_segment_dependencies/class_0x4e_type24_variant4_effect",
        },
        "animation_sequences": sequences,
        "mutation_controls": ["wrong route-global guard", "fixed-frame delay",
                              "wrong timer width", "wrong facing sign",
                              "wrong fixed-point branch order", "wrong selector",
                              "wrong RNG order", "wrong effect allocation order",
                              "wrong audio command", "wrong presentation mode",
                              "wrong presentation palette",
                              "wrong presentation object priority"],
    }


def class1f_current_state_contract(oracle09: dict[str, object],
                                   opcodes: bytes) -> dict[str, object]:
    """Project the accepted bounded street-alien evidence into native fields."""
    state = oracle09["bounded_state_contract"]
    spawn = state["spawn"]
    approach = state["authored_approach_0x1600"]
    attack = state["rng_attack_0x1800"]
    crossing = state["right_to_left_crossing_0x1a00"]
    above = state["above_lane_reposition_inner_8"]
    encounters = json.loads(ENCOUNTERS.read_text(encoding="ascii"))
    first_spawn = next(item for item in encounters["enemy_spawns"]
                       if item["frame"] == 2328 and
                       item["class"] == "0x1f" and item["type"] == 12)
    bounded_spawn = next(item for item in encounters["enemy_spawns"]
                         if item["frame"] == 3982 and
                         item["slot"] == "0xffa000" and
                         item["class"] == "0x1f" and item["type"] == 12)
    require(first_spawn["slot"] == "0xff9c40" and
            first_spawn["writer_pc"] == "0x06b3fe" and
            first_spawn["caller_chain"] ==
                ["0x06b3a8", "0x01bc70", "0x0084bc"],
            "class-0x1f first dynamic spawn drift")
    require(spawn["world"] == {"x": 960, "y": 343, "z": 343} and
            spawn["health"] == 87 and spawn["action"] == "0x0000" and
            approach["measured_motion_window"] == {
                "frames": [4214, 4252], "from": {"x": 1181, "z": 297},
                "to": {"x": 1292, "z": 274}, "facing": 1} and
            attack["contact_offsets"] == [48, 119] and
            attack["damage_each_native_health_units"] == 8 and
            attack["rng"]["seed_before"] == "0x7301" and
            attack["rng"]["seed_after"] == "0x595a" and
            attack["first_sample"]["timer"] == 120,
            "class-0x1f bounded current-state evidence drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "bounded first-segment class-0x1f current-state and first dynamic spawn",
        "accepted_oracle09_sha256": digest(ORACLE09),
        "accepted_encounter_authority_sha256": digest(ENCOUNTERS),
        "authority_boundary": {
            "native_fixed_pool_actor_owns": ["world position", "facing", "AI state",
                "animation selection", "collision", "damage", "HIT", "KO",
                "spawn", "removal", "encounter participation"],
            "retained_gameplay_authority_forbidden": True,
            "presentation_adapter_may_read_native_actor": True,
        },
        "dispatch": {
            "entry": "0x060532", "scheduler": "0x01b974",
            "scheduler_order": "type-12 ascending fixed-pool source slot",
            "outer_state_table": {"0x0000": "0x060546 initialization",
                "0x0200": "0x06075a current state", "0x0400": "0x061146 HIT",
                "0x0600": "0x06114c KO removal"},
            "inner_state_table": {"0x0000": "0x060772 action dispatch",
                "0x0200": "0x06105a shared HIT tail", "0x0400": "0x061134",
                "0x0600": "0x061134", "0x0800": "0x0610f6",
                "0x0a00": "0x060e26"},
            "unsupported_dispatch_forbidden": True,
        },
        "spawn": {
            "initial_actor": {"x_s16": spawn["world"]["x"],
                "y_s16": spawn["world"]["y"], "z_s16": spawn["world"]["z"],
                "health_s16": spawn["health"], "facing_u8": spawn["facing"],
                "state_u16": 0x0200, "substate_u16": 0x1600,
                "animation_record": spawn["animation_record"]},
            "first_dynamic": first_spawn,
            "bounded_current_state_dynamic": bounded_spawn,
            "bounded_current_state_guard_fields": {
                "guard": "living enemy count < 8 && (u8(g8019) & 7) == 0 && allocate_record12 succeeds",
                "source_global_phase_counter": "0xff8019_u8",
                "writer": "0x028a3e", "caller": "0x0288fa",
                "fixed_frame_substitute_forbidden": True,
            },
            "controller": {
                "dispatch": "0x06b2fa", "spawn_body": "0x06b3f2",
                "allocation": "0x01769e", "writer": "0x06b3fe",
                "owner_source_slot": "0x00ffb580", "owner_type": 20,
                "owner_class": "0x01", "state_byte_offset": "owner+0x05",
                "remaining_count_offset": "owner+0x66_u8",
                "timer_offset": "owner+0x2a_u16",
                "initial_spawn_guard": "signed animation branch owner+0x24 is negative",
                "repeat_spawn_guard": "owner x >= camera x && remaining count != 0 && timer == 0 && living enemy count < 6 && allocation succeeds",
                "writes": ["new.active += 1", "new.class = 0x1f",
                    "new.x/y/z = owner.x/y/z", "new.variant = 5",
                    "new.timer = 0", "living enemy count += 1",
                    "owner.remaining count -= 1", "owner.timer = 360"],
                "source_window": source_window(opcodes, 0x06B3F2),
                "fixed_frame_spawn_forbidden": True,
            },
        },
        "targeting": {
            "target_pointer": "actor+0x28 low word", "required_target": "active P1",
            "selection_guard": "current state owns target selection; no face-target-every-frame rule",
            "multiplayer_targeting": "NOT_REQUIRED_FOR_ROUND1",
        },
        "actions": {
            "approach_0x1600": {
                "state_u16": 0x0200, "inner_state_u8": 0,
                "facing_u8": 1, "ticks": 38,
                "movement_rule": "signed rational accumulator distributes +111 x and -23 z over 38 scheduler updates in source branch order",
                "x_delta_s16": 111, "z_delta_s16": -23,
                "records": approach["presentation_cycle"],
                "next_action": "0x1800"},
            "attack_0x1800": {
                "state_u16": 0x0200, "inner_state_u8": 0,
                "rng_entry": "0x017c5e", "rng_algorithm": "high=low16(3*seed)>>8; low=(low8(seed)+high)&0xff; result=(high<<8)|low",
                "rng_seed_before": attack["rng"]["seed_before"],
                "rng_seed_after": attack["rng"]["seed_after"],
                "timer_table_rule": "low byte < 0x40 selects 30; otherwise 120",
                "timer_u16": attack["first_sample"]["timer"],
                "contact_offsets_u16": attack["contact_offsets"],
                "contact_guard": "abs(P1.x-enemy.x) <= 68 && P1.z == enemy.z",
                "damage_s16": attack["damage_each_native_health_units"],
                "records": attack["presentation_cycle"],
                "completion_branches": ["P1.x < enemy.x -> 0x1a00 facing 0",
                    "else P1.z > enemy.z -> 0x0600 inner 8 facing 0",
                    "else -> 0x1600 facing 1"]},
            "reposition_0x1a00": {"state_u16": 0x0200, "inner_state_u8": 0,
                "timer_u16": crossing["first_sample"]["timer"],
                "facing_u8": crossing["first_sample"]["facing"],
                "animation_record": crossing["first_sample"]["animation_record"],
                "immediate_crossing_flip_forbidden": True},
            "above_lane_0x0600": {"state_u16": 0x0200, "inner_state_u8": 8,
                "facing_u8": above["first_sample"]["facing"],
                "animation_record": above["first_sample"]["animation_record"]},
        },
        "damage_hit_ko_removal": {
            "player_attack_guard": "current player attack selector overlaps current enemy hurt selector and guarded collision latch is clear",
            "damage_by_player_selector_s16": [8, 8, 10, 12],
            "health_s16": True, "hit_state_u16": 0x0400,
            "hit_ticks_u16": 39, "ko_state_u16": 0x0600,
            "ko_ticks_u16": 141,
            "accepted_port_v2_reaction_mapping": {
                "contract": HIT_KO_CONTRACT.relative_to(ROOT).as_posix(),
                "contract_sha256": digest(HIT_KO_CONTRACT),
                "native_outer_state_source_field": "adapter.actor.sub_state -> actor+0x04:u16",
                "native_action_substate_source_field": "adapter.actor.action -> actor+0x06:u16",
                "native_animation_record_source_field": "adapter.actor.anim_record -> actor+0x1c:u32",
                "native_animation_timer_source_field": "adapter.actor.anim_timer -> actor+0x0a:u16",
                "hit_entry_outer_state_u16": 0x0202,
                "hit_entry_action_substate_u16": 0x0002,
                "ko_entry_outer_state_u16": 0x0402,
                "ko_entry_action_substate_u16": 0x0000,
                "terminal_release_outer_state_u16": 0x0600,
                "rule": "the accepted adapter owns intermediate HIT/KO writes; native fixed-pool release may consume outer 0x0600 only after the KO timer and adapter sequence complete",
            },
            "removal_guard": "KO presentation completes and source release 0x0176b4 executes",
            "release_order": "type-12 LIFO fixed-pool release",
            "presentation_owned_removal_forbidden": True,
        },
        "mutation_controls": ["wrong first dynamic slot", "fixed-frame spawn",
            "missing living-count guard", "wrong spawn reload", "shadow actor position",
            "face target every frame", "wrong approach arithmetic", "random assembly",
            "wrong RNG algorithm", "wrong RNG consumption order", "wrong attack timer",
            "wrong contact tick", "wrong contact x guard", "wrong lane guard",
            "wrong damage", "wrong HIT duration", "wrong KO duration",
            "wrong reaction field mapping", "immediate KO release",
            "presentation-owned removal", "retained encounter gameplay step"],
    }


def counterfactuals(route: dict[str, object], class_id: str,
                    oracle09: dict[str, object]) -> dict[str, object]:
    names = {"0x00": ["remove_class_00", "suppress_warehouse_offense"],
             "0x01": ["remove_class_01", "suppress_warehouse_offense"],
             "0x06": ["remove_class_06", "suppress_boss_offense"],
             "0x1f": ["remove_class_1f", "suppress_street_offense"]}[class_id]
    result = {name: {
        "status": route["targeted_counterfactuals"][name]["status"],
        "completed_round1": route["targeted_counterfactuals"][name]["completed_round1"],
        "semantic_difference": route["targeted_counterfactuals"][name]["semantic_difference"],
        "stable_round2_handoff_frame":
            route["targeted_counterfactuals"][name]["stable_round2_handoff_frame"],
    } for name in names}
    if class_id == "0x1f":
        result["oracle09_state_facing_presentation"] = {
            "classification": oracle09["classification"],
            "counterfactual_count": len(oracle09["counterfactuals"]),
            "negative_controls": oracle09["negative_controls"],
            "evidence_sha256": digest(ORACLE09),
        }
    return result


def build_report() -> dict[str, object]:
    id_a, id_b = identity(BASE_A), identity(BASE_B)
    require(id_a["files"] == id_b["files"],
            "enemy completion captures differ")
    result = rows(BASE_A / "result.tsv")[0]
    require(int(result["final_route"]) == 4, "enemy baseline did not complete Round 1")
    samples = rows(BASE_A / "enemy_samples.tsv")
    entries = rows(BASE_A / "enemy_entries.tsv")
    writes = rows(BASE_A / "enemy_writes.tsv")
    rng = rows(BASE_A / "enemy_rng.tsv")
    damage = rows(BASE_A / "player_damage.tsv")
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    scheduler = json.loads(SCHEDULER.read_text(encoding="ascii"))
    oracle09 = json.loads(ORACLE09.read_text(encoding="ascii"))
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()
    archetypes = {(item["class"], item["type"]): item
                  for item in route["actor_archetypes"]}
    source_dispatch = next(item for item in scheduler["pools"]
                           if item["record_type"] == 12)
    require(source_dispatch["required_round1_dispatch"] == [
        {"class": name, "routine": f"0x{address:06x}"}
        for name, address in CLASSES.items()], "enemy dispatch table drift")

    reports = []
    owned_pcs = set()
    for class_id, entry in CLASSES.items():
        raw = class_id[2:]
        class_samples = [row for row in samples if row["class"] == raw]
        class_entries = [row for row in entries if row["class"] == raw]
        class_writes = [row for row in writes if row["class"] == raw]
        class_rng = [row for row in rng if row["class"] == raw]
        class_damage = [row for row in damage if row["owner_class"] == raw]
        counts = {"samples": len(class_samples), "entries": len(class_entries),
                  "writes": len(class_writes), "rng": len(class_rng),
                  "damage": len(class_damage)}
        require(counts == EXPECTED[class_id], f"{class_id}: route census count drift")
        writer_details = aggregate_writers(writes, class_id, opcodes)
        writer_pcs = {item["pc"] for item in writer_details}
        rng_pcs = {f"0x{row['pc']}" for row in class_rng}
        damage_pcs = {f"0x{row['pc']}" for row in class_damage}
        owned_pcs.update(writer_pcs | rng_pcs | damage_pcs | {f"0x{entry:06x}"})
        records = animation_records(samples, class_id, program)
        hit_ko_presentation = None
        if class_id == "0x1f":
            hit_ko_records, hit_ko_presentation = \
                accepted_class1f_hit_ko_records(program)
            by_address = {row["animation_record"]: row for row in records}
            by_address.update({row["animation_record"]: row
                               for row in hit_ko_records})
            records = [by_address[address] for address in sorted(by_address)]
        actor = archetypes[(class_id, 12)]
        reports.append({
            "class": class_id, "type": 12, "classification": "SOURCE_CLOSED",
            "dispatch_entry": f"0x{entry:06x}",
            "dispatch_entry_sha256": hashlib.sha256(
                opcodes[entry:entry + 64]).hexdigest(),
            "instance_count": actor["instance_count"],
            "source_frame_range": actor["source_frame_range"],
            "counts": counts,
            "state_phase_contexts": sorted({
                f"{int(row['state']):04x}:{int(row['phase']):04x}"
                for row in class_samples}),
            "facing_values": sorted({int(row["facing"]) for row in class_samples}),
            "target_pointers": sorted({f"0x{int(row['target'], 16):04x}"
                                       for row in class_samples}),
            "writer_provenance": writer_details,
            "orphan_write_rows": 0,
            "rng": {
                "source_entry": "0x017c5e",
                "calls": len(class_rng),
                "caller_pcs": dict(sorted(Counter(f"0x{row['pc']}"
                                                   for row in class_rng).items())),
                "consumption_order": "captured in fixed type-12 scheduler order",
                "orphan_calls": 0,
            },
            "presentation_and_collision": {
                "rule": ("active state owns animation record; record+4 owns assembly, "
                         "record+8 hurt selector and record+9 attack selector"),
                "records": records, "record_count": len(records),
                "orphan_records": 0,
            },
            "damage_hit_ko": {
                "enemy_health_writer_pcs": dict(sorted(Counter(
                    f"0x{row['pc']}" for row in class_writes
                    if row["offset"] in ("40", "41", "42", "43")).items())),
                "player_damage_writes": [{key: row[key] for key in
                    ("frame", "pc", "owner_slot", "owner_state", "owner_phase",
                     "owner_anim", "old_health", "data", "mask")}
                    for row in class_damage],
                "player_damage_write_count": len(class_damage),
                "current_state_owner_bound": True,
                "hit_ko_transitions": actor["state_transitions"],
            },
            "counterfactuals": counterfactuals(route, class_id, oracle09),
            "semantic_name_inferred": False,
        })
        if class_id == "0x1f":
            reports[-1]["initial_transition_contract"] = \
                initial_class1f_transition_contract(samples, rng, opcodes, program)
            reports[-1]["current_state_implementation_contract"] = \
                class1f_current_state_contract(oracle09, opcodes)
            reports[-1]["first_segment_action_execution_contract"] = \
                class1f_first_segment_action_contract(program, opcodes)
            reports[-1]["presentation_and_collision"][
                "accepted_hit_ko_records"] = hit_ko_presentation

    report = {
        "schema": "oracle11-round1-enemy-archetypes-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "all route-reachable Round 1 record-type-12 enemy archetypes",
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True, "final_route": 4},
        "scheduler": {
            "classification": "SOURCE_CLOSED", "pool_type": 12,
            "routine": "0x01b974", "dispatch_table": "0x01b9b6",
            "dispatch_table_sha256": source_dispatch["dispatch_table_identity"]["sha256"],
            "order": "ascending fixed-pool slot before the next pool",
        },
        "archetypes": reports,
        "owned_authoritative_writer_pcs": sorted(owned_pcs),
        "coverage": {
            "required_class_type_pairs": 4, "closed_class_type_pairs": 4,
            "orphan_class_type_pairs": 0, "orphan_state_phase_contexts": 0,
            "orphan_write_rows": 0, "orphan_rng_calls": 0,
            "orphan_animation_records": 0, "orphan_damage_writes": 0,
        },
        "scope_boundary": {
            "boss_actor_behavior_closed_here": True,
            "boss_encounter_orchestration_closed_here": False,
            "encounter_spawn_wave_route_guards_closed_here": False,
            "shared_collision_damage_primitive_reimplemented_here": False,
        },
        "negative_controls": {
            "generic_enemy_behavior_tree_forbidden": True,
            "independent_random_assembly_selection_forbidden": True,
            "shared_player_enemy_navigation_clamp_forbidden": True,
            "fixed_frame_attack_or_death_forbidden": True,
            "semantic_names_inferred": False,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED",
            "navigation_terrain_camera": "SOURCE_CLOSED",
            "global_audio_load_release": "SOURCE_CLOSED",
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "physical_saturn": "UNRUN", "spec02_active": False,
            "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-round1-enemy-archetypes-v1" and
            report["status"] == "SOURCE_CLOSED", "enemy-family status drift")
    require(report["capture_identity"]["byte_identical"] is True and
            report["capture_identity"]["final_route"] == 4,
            "enemy capture identity drift")
    require(report["scheduler"]["classification"] == "SOURCE_CLOSED" and
            report["scheduler"]["routine"] == "0x01b974" and
            report["scheduler"]["dispatch_table"] == "0x01b9b6",
            "enemy scheduler boundary drift")
    opcodes = OPCODES.read_bytes()
    require(len(report["archetypes"]) == 4 and
            {item["class"] for item in report["archetypes"]} == set(CLASSES),
            "enemy archetype inventory drift")
    for item in report["archetypes"]:
        class_id = item["class"]
        entry = CLASSES[class_id]
        require(item["classification"] == "SOURCE_CLOSED" and
                item["dispatch_entry"] == f"0x{entry:06x}" and
                item["dispatch_entry_sha256"] == hashlib.sha256(
                    opcodes[entry:entry + 64]).hexdigest() and
                item["counts"] == EXPECTED[class_id] and
                item["orphan_write_rows"] == 0 and item["writer_provenance"] and
                item["rng"]["orphan_calls"] == 0 and
                item["presentation_and_collision"]["orphan_records"] == 0 and
                item["presentation_and_collision"]["record_count"] > 0 and
                item["damage_hit_ko"]["current_state_owner_bound"] is True and
                item["damage_hit_ko"]["player_damage_write_count"] ==
                    EXPECTED[class_id]["damage"] and
                item["semantic_name_inferred"] is False,
                f"{class_id}: enemy authority drift")
        if class_id == "0x1f":
            expected_hit_ko, expected_hit_ko_binding = \
                accepted_class1f_hit_ko_records(PROGRAM.read_bytes())
            records_by_address = {
                row["animation_record"]: row
                for row in item["presentation_and_collision"]["records"]}
            require(item["presentation_and_collision"]["accepted_hit_ko_records"] ==
                    expected_hit_ko_binding and
                    all(records_by_address.get(row["animation_record"]) == row
                        for row in expected_hit_ko),
                    "0x1f: accepted HIT/KO presentation fields drift")
            contract = item["initial_transition_contract"]
            require(contract["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
                    contract["accepted_audio_evidence_sha256"] == digest(AUDIO) and
                    len(contract["actors"]) == 10 and
                    [actor["entry_delay_u8"] for actor in contract["actors"][-3:]] ==
                        [9, 3, 16] and
                    [actor["coordinate_mode_u8"] for actor in
                     contract["actors"]] == [1] * 10 and
                    [actor["palette_u8"] for actor in contract["actors"]] ==
                        [16, 17, 17, 18, 17, 16, 18, 17, 19, 19] and
                    [actor["object_or_u16"] for actor in contract["actors"]] ==
                        ["0x8000"] * 10 and
                    all(actor["presentation_source_frame"] == 2092 and
                        len(actor["presentation_source_record_sha256"]) == 64
                        for actor in contract["actors"]) and
                    contract["initialization"]["rng_calls"] == 10 and
                    contract["initialization"]["rng_seed_after_each_source_slot"][-1] ==
                        "0x16b7" and
                    contract["initialization"]["fixed_frame_initialization_forbidden"] is True and
                    contract["phase_0x1000_and_0x1200"]["source_observed_clear_frame"] == 2287 and
                    contract["phase_0x1000_and_0x1200"]["next_state_substate"] ==
                        "0x0200:0000" and
                    contract["phase_0x1000_and_0x1200"]["source_observed_next_dispatch"] ==
                        {"frame": 2288, "state_u16": 0x0200,
                         "substate_u16": 0x1600} and
                    [body["substate_u16"] for body in
                     contract["phase_0x1400"]["substates"]] ==
                        [0x1400, 0x1402, 0x1404, 0x1406, 0x1408] and
                    contract["phase_0x1400"]["substates"][1]["writes"]
                        ["y_acceleration_s32_16_16"] == -0x5000 and
                    contract["phase_0x1400"]["substates"][4]
                        ["next_state_substate"] == "0x0200:0000" and
                    contract["phase_0x1400"]["substates"][4]
                        ["source_observed_next_dispatch"]["substate_u16"] ==
                            0x0600 and
                    [edge["command"] for edge in contract["phase_0x1400"]
                     ["substates"][2]["audio_edges"]] == ["0x004d", "0x0118"] and
                    [sequence["selector_u8"] for sequence in
                     contract["animation_sequences"]] == [0, 1, 52, 60, 62, 76] and
                    contract["initialization"]["presentation_field_offsets"] == {
                        "coordinate_mode_u8": "actor+0x0d",
                        "palette_u8": "actor+0x0e",
                        "object_or_u16": "actor+0x2e",
                    } and
                    contract["initialization"]["accepted_presentation_frame"] ==
                        2092 and
                    len(contract["mutation_controls"]) == 12,
                    "0x1f: initial transition implementation contract drift")
            current = item["current_state_implementation_contract"]
            require(current["classification"] ==
                        "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
                    current["accepted_oracle09_sha256"] == digest(ORACLE09) and
                    current["accepted_encounter_authority_sha256"] ==
                        digest(ENCOUNTERS) and
                    current["authority_boundary"]
                        ["retained_gameplay_authority_forbidden"] is True and
                    current["spawn"]["first_dynamic"]["slot"] == "0xff9c40" and
                    current["spawn"]["first_dynamic"]["writer_pc"] ==
                        "0x06b3fe" and
                    current["spawn"]["bounded_current_state_dynamic"]
                        ["slot"] == "0xffa000" and
                    current["spawn"]["bounded_current_state_dynamic"]
                        ["writer_pc"] == "0x028a3e" and
                    current["spawn"]["controller"]["timer_offset"] ==
                        "owner+0x2a_u16" and
                    current["spawn"]["controller"]["writes"][-1] ==
                        "owner.timer = 360" and
                    current["actions"]["approach_0x1600"]
                        ["x_delta_s16"] == 111 and
                    current["actions"]["approach_0x1600"]
                        ["z_delta_s16"] == -23 and
                    current["actions"]["attack_0x1800"]
                        ["contact_offsets_u16"] == [48, 119] and
                    current["actions"]["attack_0x1800"]["damage_s16"] == 8 and
                    current["damage_hit_ko_removal"]["hit_ticks_u16"] == 39 and
                    current["damage_hit_ko_removal"]["ko_ticks_u16"] == 141 and
                    current["damage_hit_ko_removal"]
                        ["accepted_port_v2_reaction_mapping"]
                        ["hit_entry_outer_state_u16"] == 0x0202 and
                    current["damage_hit_ko_removal"]
                        ["accepted_port_v2_reaction_mapping"]
                        ["ko_entry_outer_state_u16"] == 0x0402 and
                    current["damage_hit_ko_removal"]
                        ["accepted_port_v2_reaction_mapping"]
                        ["terminal_release_outer_state_u16"] == 0x0600 and
                    len(current["mutation_controls"]) == 21,
                    "0x1f: current-state implementation contract drift")
            actions = item["first_segment_action_execution_contract"]
            require(actions["classification"] ==
                        "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
                    actions["capture_identity"]["byte_identical"] is True and
                    len(actions["initializer"]["variants"]) == 10 and
                    actions["initializer"]["variants"][8]["writes"]
                        ["timer_aa_u8"] == "entry_delay_u8" and
                    [row["action_u8"] for row in
                     actions["current_dispatch"]["action_targets"]] ==
                        list(range(0, 0x20, 2)) and
                    actions["current_dispatch"]["action_targets"][11]
                        ["target"] == "0x060c2e" and
                    actions["current_dispatch"]["required_state_contexts"] == [
                        "0x0200:0000", "0x0200:0200", "0x0200:0400",
                        "0x0200:0402", "0x0200:0404", "0x0200:0406",
                        "0x0200:0408", "0x0200:0600", "0x0200:0800",
                        "0x0200:0a00", "0x0200:0c00", "0x0200:0c02",
                        "0x0200:0c04", "0x0200:0e00", "0x0200:0e02",
                        "0x0200:0e04", "0x0200:1000", "0x0200:1200",
                        "0x0200:1400", "0x0200:1402", "0x0200:1404",
                        "0x0200:1406", "0x0200:1408", "0x0200:1600",
                        "0x0200:1800", "0x0200:1a00", "0x0200:1c00",
                        "0x0200:1e00"] and
                    [row["selector_u8"] for row in
                     actions["animation_selector_table"]["selectors"]] ==
                        list(CLASS1F_ROUTE_SELECTORS) and
                    [row["table_index_u8"] for row in
                     actions["movement_tables"]] == [1, 8] and
                    actions["movement_tables"][1]["vectors"][8] == {
                        "direction_u8": 8, "x_delta_s16": 2048,
                        "y_delta_s16": 0} and
                    actions["attack_timer_table_u8"] ==
                        [30, 30, 30, 30, 60, 60, 60, 60,
                         120, 120, 120, 120, 160, 160, 160, 160] and
                    actions["action_programs"]["source_bounds"]
                        ["activation_field_u8"] == "actor+0x01" and
                    actions["action_programs"]["source_bounds"]
                        ["latched_field_u8"] == "actor+0xa2" and
                    actions["action_programs"]["source_bounds"]
                        ["camera_operand_u16"] == "0xff8278" and
                    actions["action_programs"]["source_bounds"]
                        ["phase_guard_field_u8"] == "0xff8019" and
                    actions["action_programs"]["source_bounds"]
                        ["x_max_u16"] == 0x05f0 and
                    actions["action_programs"]["source_bounds"]
                        ["camera_relative_bias_u16"] == 0x0070 and
                    actions["action_programs"]["source_bounds"]
                        ["camera_relative_span_u16"] == 0x0260 and
                    actions["action_programs"]["source_bounds"]
                        ["failure_outer_state_u16"] == 0x0600 and
                    actions["action_programs"]["source_bounds"]
                        ["coffee_shop_observation"]["result"] ==
                            "pass after x_max; camera-relative test skipped" and
                    actions["action_programs"]
                        ["animation_movement_helper_0x0165c4"]
                        ["source_body_sha256"] ==
                            "b35c9aaf0a5328ff35e6ccb5c9d278fef7f898201fc6e005e69d11bd566a970b" and
                    actions["action_programs"]
                        ["animation_movement_helper_0x0165c4"]
                        ["movement_cadence"] ==
                            "only on timer expiry after binding the next animation record" and
                    actions["action_programs"]
                        ["animation_movement_helper_0x0165c4"]
                        ["movement_record"] ==
                            "newly bound next animation record" and
                    actions["action_programs"]["direction_helper_0x061032"]
                        ["upper_directions_by_a5_u8"] == [0x16, 0x0a] and
                    actions["action_programs"]["direction_helper_0x061032"]
                        ["lower_directions_by_a5_u8"] == [0x1a, 0x06] and
                    actions["action_programs"]["action_0x0e"]
                        ["z_velocity_table_s32_16_16"] ==
                        [-0x00010000, -0x00014000,
                         -0x00018000, -0x00020000] and
                    actions["action_programs"]["action_0x04"]
                        ["selector_groups_u16"] ==
                        [[55], [56], [43, 43, 43, 55], [43, 43, 56]] and
                    actions["action_programs"]["action_0x04"]
                        ["coffee_shop_observation"]["timer_result_u8"] == 6 and
                    actions["action_programs"]["action_0x04"]
                        ["timer_stage_offsets_u8"] ==
                        [0] * 5 + [32] * 8 + [64] * 6 +
                        [96] * 5 + [128] * 8 and
                    actions["action_programs"]["action_0x16"]
                        ["loop_counter"] == "b0_u8" and
                    actions["suppression_control"]["writer_pc"] ==
                        "0x0607e8" and
                    actions["suppression_control"]["suppressed_writes"] == 179 and
                    actions["suppression_control"]["baseline_main_aux_spawns"] ==
                        [15, 3] and
                    actions["suppression_control"]["mutant_main_aux_spawns"] ==
                        [16, 3] and
                    actions["suppression_control"]["fixed_frame_substitute"]
                        is False and
                    actions["suppression_control"]["action4_timer"]
                        ["suppressed_writes"] == 1 and
                    len(actions["mutation_controls"]) == 17,
                    "0x1f: first-segment action execution contract drift")
    require(all(value == 0 for key, value in report["coverage"].items()
                if key.startswith("orphan_")) and
            report["coverage"]["required_class_type_pairs"] == 4 and
            report["coverage"]["closed_class_type_pairs"] == 4,
            "enemy zero-orphan coverage drift")
    boundary = report["scope_boundary"]
    require(boundary == {
        "boss_actor_behavior_closed_here": True,
        "boss_encounter_orchestration_closed_here": False,
        "encounter_spawn_wave_route_guards_closed_here": False,
        "shared_collision_damage_primitive_reimplemented_here": False,
    }, "enemy-family scope expanded")
    require(report["negative_controls"]["semantic_names_inferred"] is False and
            report["negative_controls"]["generic_enemy_behavior_tree_forbidden"]
            is True, "enemy negative controls drift")
    require(report["protected_boundaries"]["production_runtime_writes"] == 0 and
            report["protected_boundaries"]["yaba_runs"] == 0 and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN" and
            report["protected_boundaries"]["spec02_active"] is False and
            report["protected_boundaries"]["oracle11_active"] is True,
            "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 Round 1 enemy archetypes: SOURCE_CLOSED; four class/type "
          "pairs with zero orphan states, writers, RNG, records, or damage events")


if __name__ == "__main__":
    main()
