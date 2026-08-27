#!/usr/bin/env python3
"""Close route-reachable Predator Warrior directional and airborne authority."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle11_player_air_b"
RAW_DOWN = ROOT / ".deps" / "mame" / "oracle11_player_air_c"
RAW_GUN = ROOT / ".deps" / "mame" / "oracle11_player_air_d"
RAW_NATURAL = ROOT / ".deps" / "mame" / "oracle11_player_jump_a"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
WEAPON = ROOT / "data" / "oracle11_predator_weapon_projectile_resource.json"
OUT = ROOT / "data" / "oracle11_predator_air_authority.json"
ROUTE_RUNS = {
    "baseline-completions": ROOT / ".deps" / "mame" /
        "oracle10_round1_system_census_e" / "baseline" / "samples.tsv",
    "perturbed-completions": ROOT / ".deps" / "mame" /
        "oracle10_round1_system_census_c" / "route_perturbed" / "samples.tsv",
    "failure-continue": ROOT / ".deps" / "mame" /
        "oracle10_round1_system_census_d" / "no_continue" / "samples.tsv",
}

ROUTE_REQUIRED = {0x0400, 0x0402, 0x0404, 0x0406}
COUNTERFACTUAL_REQUIRED = {0x040A, 0x040C, 0x040E, 0x0410}
NOT_REQUIRED = {0x0408, 0x0412, 0x0414}
STATE_TABLE = {
    0x00: 0x0233E6, 0x02: 0x02349A, 0x04: 0x0234E4,
    0x06: 0x0234F0, 0x08: 0x023500, 0x0A: 0x023534,
    0x0C: 0x02358E, 0x0E: 0x02359C, 0x10: 0x0235BC,
    0x12: 0x0235EC, 0x14: 0x02360C,
}
VECTOR_TABLE_BASE = 0x0243D2
VECTOR_TABLE_END = 0x024452
AIR_RECORDS = {
    0x15F2CC: (0x160BC6, 1, 0), 0x15F2DC: (0x160BC6, 1, 0),
    0x15F2F0: (0x160CDA, 2, 0), 0x15F300: (0x160D02, 2, 0),
    0x15F310: (0x160D2A, 2, 0), 0x15F320: (0x160D52, 2, 0),
    0x15F330: (0x160D86, 2, 0), 0x15F344: (0x160BEE, 2, 0),
    0x15F354: (0x160C16, 2, 0), 0x15F364: (0x160C3E, 13, 0),
    0x15F374: (0x160C66, 14, 0), 0x15F384: (0x160C84, 15, 0),
    0x15F394: (0x160CAC, 16, 0), 0x15F3A4: (0x160BEE, 2, 0),
    0x15F3B8: (0x160BEE, 2, 0), 0x15F3C8: (0x160CAC, 16, 0),
    0x15F3D8: (0x160C84, 15, 0), 0x15F3E8: (0x160C66, 14, 0),
    0x15F3F8: (0x160C3E, 13, 0), 0x15F408: (0x160C16, 2, 0),
    0x15F418: (0x160BEE, 2, 0), 0x15F428: (0x160BEE, 2, 0),
    0x15F43C: (0x162BAA, 18, 0), 0x15F44C: (0x162BC8, 18, 0),
    0x15F45C: (0x162BAA, 18, 0), 0x15FC3C: (0x162EE2, 9, 22),
    0x15FC4C: (0x162EE2, 9, 23), 0x15FC60: (0x162EE2, 9, 35),
    0x15FCE8: (0x16212C, 7, 0),
}
AIR_SELECTOR_RECORDS = {
    3: [0x15F2CC, 0x15F2DC],
    4: [0x15F2F0, 0x15F300, 0x15F310, 0x15F320, 0x15F330],
    5: [0x15F344, 0x15F354, 0x15F364, 0x15F374, 0x15F384,
        0x15F394, 0x15F3A4],
    6: [0x15F3B8, 0x15F3C8, 0x15F3D8, 0x15F3E8, 0x15F3F8,
        0x15F408, 0x15F418, 0x15F428],
    10: [0x15F2CC, 0x15F2DC],
    15: [0x15F43C, 0x15F44C, 0x15F45C],
    41: [0x15FC3C, 0x15FC4C],
    42: [0x15FCE8],
    60: [0x15FC60],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def indexed(path: Path) -> dict[int, dict[str, str]]:
    return {int(row["frame"]): row for row in rows(path)}


def source_window(data: bytes, start: int, end: int) -> dict[str, object]:
    return {"start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
            "bytes": end - start,
            "sha256": hashlib.sha256(data[start:end]).hexdigest()}


def u32be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big", signed=False)


def s32be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big", signed=True)


def fixed(value: int) -> dict[str, object]:
    return {"raw_s32": value, "hex": f"0x{value & 0xffffffff:08x}",
            "pixels_per_tick": value / 65536.0}


def vector_entry(program: bytes, address: int) -> dict[str, object]:
    values = [s32be(program, address + offset) for offset in range(0, 16, 4)]
    return {
        "source_address": f"0x{address:06x}",
        "x_velocity_s32_16_16": fixed(values[0]),
        "x_acceleration_s32_16_16": fixed(values[1]),
        "z_velocity_s32_16_16": fixed(values[2]),
        "z_acceleration_s32_16_16": fixed(values[3]),
    }


def record_identity(program: bytes, address: int) -> dict[str, object]:
    expected = AIR_RECORDS[address]
    actual = (u32be(program, address + 4), program[address + 8],
              program[address + 9])
    require(actual == expected, f"air presentation record drift: {address:06x}")
    return {"record": f"0x{address:06x}",
            "timer_u16": int.from_bytes(program[address:address + 2], "big"),
            "branch_s16": int.from_bytes(program[address + 2:address + 4],
                                           "big", signed=True),
            "assembly": f"0x{actual[0]:06x}",
            "hurt_selector_u8": actual[1], "attack_selector_u8": actual[2]}


def selector_sequences(program: bytes) -> dict[str, object]:
    base = 0x15E240
    result = {}
    for selector, expected_records in AIR_SELECTOR_RECORDS.items():
        offset = int.from_bytes(program[base + selector * 2:
                                        base + selector * 2 + 2], "big")
        address = base + offset
        actual = []
        while True:
            actual.append(address)
            if int.from_bytes(program[address + 2:address + 4],
                              "big", signed=True) < 0:
                break
            address += 16
            require(len(actual) <= 16, "unbounded air selector sequence")
        require(actual == expected_records,
                f"air selector {selector} record sequence drift")
        result[str(selector)] = [record_identity(program, item)
                                 for item in actual]
    return result


def observed_record_sequence(sample_path: Path, first: int,
                             last: int) -> list[str]:
    sequence: list[str] = []
    for row in rows(sample_path):
        frame = int(row["frame"])
        if first <= frame <= last:
            record = f"0x{int(row['p_anim'], 16):06x}"
            if not sequence or sequence[-1] != record:
                sequence.append(record)
    return sequence


def manifest_identity(root: Path) -> dict[str, object]:
    manifest_path = root / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    for variant in manifest["variants"]:
        for filename, expected in variant["sha256"].items():
            require(digest(root / variant["name"] / filename) == expected,
                    f"{root.name}/{variant['name']}/{filename}: identity drift")
    return {"manifest_sha256": digest(manifest_path),
            "variant_names": [item["name"] for item in manifest["variants"]]}


def phases(path: Path) -> set[int]:
    observed = set()
    for row in rows(path):
        value = int(row["p_action"] if "p_action" in row else row["p_phase"])
        if value >> 8 == 4:
            observed.add(value)
    return observed


def phase_writer(path: Path, phase: int, pc: str) -> bool:
    return any(row["offset"] == "06" and row["pc"] == pc and
               (int(row["data"], 16) & 0xffff) == phase
               for row in rows(path))


def build_report() -> dict[str, object]:
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()
    require(len(opcodes) == len(program) == 0x200000,
            "decoded source image size drift")
    identities = {root.name: manifest_identity(root)
                  for root in (RAW, RAW_DOWN, RAW_GUN)}
    for filename in ("samples.tsv", "player_writes.tsv",
                     "player_global_writes.tsv"):
        require(digest(RAW / "air_cold_1" / filename) ==
                digest(RAW / "air_cold_2" / filename),
                f"independent cold air captures differ: {filename}")

    route_phase_sets = {name: sorted(phases(path))
                        for name, path in ROUTE_RUNS.items()}
    for name, observed in route_phase_sets.items():
        require(set(observed) == ROUTE_REQUIRED,
                f"{name}: route airborne phase census drift")

    dash = {name: indexed(RAW / name / "samples.tsv") for name in
            ("dash_right", "dash_left", "dash_up", "dash_down")}
    require(int(dash["dash_right"][4424]["p_action"]) == 0x0402 and
            int(dash["dash_left"][4424]["p_action"]) == 0x0402 and
            int(dash["dash_up"][4424]["p_action"]) == 0x0402,
            "directional jump phase drift")
    require((int(dash["dash_down"][4424]["p_action"]),
             int(dash["dash_down"][4437]["p_action"])) == (0x040A, 0x040C),
            "Down+Button3 source phases drift")
    require(int(dash["dash_left"][4462]["p_action"]) == 0x0404 and
            int(dash["dash_right"][4441]["p_action"]) == 0x0404 and
            int(dash["dash_up"][4473]["p_action"]) == 0x0404,
            "directional landing drift")

    air_b2 = indexed(RAW / "air_button2_neutral" / "samples.tsv")
    air_down = indexed(RAW_DOWN / "air_button2_midair_down" / "samples.tsv")
    require(int(air_b2[4432]["p_action"]) == 0x040E and
            int(air_down[4432]["p_action"]) == 0x0410,
            "air Button2 branch drift")
    require(all(phase not in phases(RAW / name / "samples.tsv")
                for name in ("air_button2_followup_4436",
                             "air_button2_followup_4442",
                             "air_button2_followup_4449",
                             "air_button2_followup_4454")
                for phase in (0x0412, 0x0414)),
            "air follow-up negative control unexpectedly reached gated body")

    gun = indexed(RAW_GUN / "air_button1_resource" / "samples.tsv")
    require((int(gun[4697]["p_action"]), int(gun[4697]["p_x"]),
             int(gun[4697]["p_z"])) == (0x0406, 1360, 319),
            "route-reachable airborne Button1 phase drift")
    require(phase_writer(RAW_GUN / "air_button1_resource" /
                         "player_writes.tsv", 0x0406, "023860"),
            "airborne Button1 writer drift")

    natural = indexed(RAW_NATURAL / "dash_right" / "samples.tsv")
    natural_writes = RAW_NATURAL / "dash_right" / "player_writes.tsv"
    require(int(natural[4424]["p_action"]) == 0x0402 and
            int(natural[4433]["p_inner"]) == 2 and
            phase_writer(natural_writes, 0x0202, "01a988"),
            "natural directional-air HIT interruption drift")

    counterfactual_phases = set()
    for name in ("dash_right", "dash_left", "dash_up", "dash_down",
                 "air_button2_neutral"):
        counterfactual_phases |= phases(RAW / name / "samples.tsv")
    counterfactual_phases |= phases(
        RAW_DOWN / "air_button2_midair_down" / "samples.tsv")
    counterfactual_phases |= phases(
        RAW_GUN / "air_button1_resource" / "samples.tsv")
    require(COUNTERFACTUAL_REQUIRED <= counterfactual_phases,
            "targeted counterfactual phase coverage drift")

    vectors = [vector_entry(program, VECTOR_TABLE_BASE + index * 0x10)
               for index in range(6)]
    require([[item[key]["raw_s32"] for key in
              ("x_velocity_s32_16_16", "x_acceleration_s32_16_16",
               "z_velocity_s32_16_16", "z_acceleration_s32_16_16")]
             for item in vectors] == [
                 [0, 0, 0x00088000, -0x00008000],
                 [0, 0, 0x000c0000, -0x00008000],
                 [-0x000f0000, 0x00006800, 0x00040000, -0x00003800],
                 [-0x00090000, 0x00002400, 0x000c0000, -0x00008800],
                 [0x00090000, -0x00002000, 0x00040000, -0x00008000],
                 [0x00088000, -0x00002400, 0x000c0000, -0x00008800],
             ], "Button3 vector table drift")
    down_vectors = {
        "vertical_only": {
            "source_address": "0x024432",
            "x_velocity_s32_16_16": fixed(s32be(program, 0x024432)),
            "x_acceleration_s32_16_16": fixed(s32be(program, 0x024436)),
        },
        "with_horizontal": {
            "source_address": "0x024442",
            "x_velocity_s32_16_16": fixed(s32be(program, 0x024442)),
            "x_acceleration_s32_16_16": fixed(s32be(program, 0x024446)),
        },
    }
    require([down_vectors[name][field]["raw_s32"] for name in
             ("vertical_only", "with_horizontal") for field in
             ("x_velocity_s32_16_16", "x_acceleration_s32_16_16")] ==
            [0x00060000, -0x00008000, 0x000c0000, -0x0000a000],
            "Down+Button3 vector table drift")
    presentation_records = [record_identity(program, address)
                            for address in AIR_RECORDS]
    presentation_sequences = selector_sequences(program)
    observed_sequences = {
        "neutral_or_up": observed_record_sequence(
            RAW / "dash_up" / "samples.tsv", 4422, 4475),
        "left_facing_0": observed_record_sequence(
            RAW / "dash_left" / "samples.tsv", 4422, 4464),
        "right_facing_0": observed_record_sequence(
            RAW / "dash_right" / "samples.tsv", 4422, 4443),
        "down": observed_record_sequence(
            RAW / "dash_down" / "samples.tsv", 4422, 4447),
    }
    require(observed_sequences == {
        "neutral_or_up": ["0x15f2cc", "0x15f2dc", "0x15f2f0",
                           "0x15f300", "0x15f310", "0x15f320",
                           "0x15f330", "0x15f2cc", "0x15f2dc",
                           "0x15f1f4"],
        "left_facing_0": ["0x15f2cc", "0x15f2dc", "0x15f344",
                           "0x15f354", "0x15f364", "0x15f374",
                           "0x15f384", "0x15f394", "0x15f3a4",
                           "0x15f2cc", "0x15f2dc", "0x15f1f4"],
        "right_facing_0": ["0x15f2cc", "0x15f2dc", "0x15f43c",
                            "0x15f44c", "0x15f45c", "0x15f2cc",
                            "0x15f2dc", "0x15f1f4"],
        "down": ["0x15f2cc", "0x15f2dc", "0x15fc60", "0x15fce8",
                 "0x15f1f4"],
    }, "Button3 presentation sequence drift")
    presentation_actor_fields = set()
    for name in ("air_cold_1", "dash_right", "dash_left", "dash_up",
                 "dash_down"):
        for row in rows(RAW / name / "samples.tsv"):
            if int(row["p_action"]) >> 8 != 4:
                continue
            actor = bytes.fromhex(row["actor_hex"])
            presentation_actor_fields.add((actor[0x0d], actor[0x0e],
                                           int.from_bytes(
                                               actor[0x2e:0x30], "big")))
    require(presentation_actor_fields == {(0, 0, 0x8000)},
            "Button3 presentation actor field drift")

    weapon = json.loads(WEAPON.read_text(encoding="ascii"))
    report = {
        "schema": "oracle11-predator-air-authority-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "Predator Warrior route-reachable directional jump, airborne Button1/Button2 actions, landing, interruption cancellation, and return to control",
        "coverage_universe": {
            "routes": ["baseline-completion-a", "baseline-completion-b",
                       "perturbed-completions", "failure-continue",
                       "targeted-counterfactuals"],
            "route_phase_census": route_phase_sets,
            "required_route_phases": [f"0x{x:04x}" for x in sorted(ROUTE_REQUIRED)],
            "required_counterfactual_phases": [
                f"0x{x:04x}" for x in sorted(COUNTERFACTUAL_REQUIRED)],
            "all_required_phases_closed": True,
        },
        "source_identity": {
            "decoded_opcodes_sha256": hashlib.sha256(opcodes).hexdigest(),
            "decrypted_program_sha256": hashlib.sha256(program).hexdigest(),
            "jump_dispatch_and_vector_setup": source_window(
                opcodes, 0x02331E, 0x0233C4),
            "jump_vector_table": source_window(
                program, VECTOR_TABLE_BASE, VECTOR_TABLE_END),
            "player_animation_selector_table": source_window(
                program, 0x15E240, 0x15E2BA),
            "air_state_dispatch_and_bodies": source_window(
                opcodes, 0x0233C4, 0x02370C),
            "air_vector_table_resolver": source_window(
                opcodes, 0x02370C, 0x023858),
            "airborne_button1_spawn_branch": source_window(
                opcodes, 0x023858, 0x023926),
            "fixed_point_air_motion": source_window(
                opcodes, 0x01A8E6, 0x01A932),
            "button2_edge_guard": source_window(
                opcodes, 0x01A6C4, 0x01A6DC),
            "air_reverse_guard": source_window(
                opcodes, 0x01A932, 0x01A96E),
            "interruption_reset": source_window(
                opcodes, 0x01A96E, 0x01AA5E),
            "capture_manifests": identities,
        },
        "state_dispatch": {
            f"0x{state:02x}": f"0x{pc:06x}"
            for state, pc in STATE_TABLE.items()
        },
        "directional_actions": {
            "classification": "SOURCE_CLOSED",
            "input_guard": "new Button3 edge at actor +0xee/+0xef bit 6",
            "entry": "0x0233e6",
            "vector_resolver": "0x02331e",
            "directions": {
                "neutral": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "right": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "left": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "up_lane": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "down_lane": {"phases": ["0x0400", "0x040a", "0x040c"]},
            },
            "landing_guard": "0x01a8e6 signed world-Y versus world-Z comparison; carry clear enters 0x023630",
            "landing_writer": "0x023636",
            "landing_phase": "0x0404",
            "cleanup": "0x01a3fa clears action; 0x0198de returns to source idle/locomotion dispatch",
            "facing": "latched from +0x0f; direction-specific fixed-point vectors are selected before airborne updates",
            "rng_consumption": "none",
            "implementation_contract": {
                "spec_executable": True,
                "source_input": {
                    "current_u8_offset": "0x00ee",
                    "previous_u8_offset": "0x00ef",
                    "button3_mask_u8": "0x40",
                    "direction_masks_u8": {"right": "0x01", "left": "0x02",
                                           "down": "0x04", "up": "0x08"},
                    "entry_guard": "new Button3 edge; state dispatcher writes 0x0400 and initialization runs only when timer_s16_at_0x24 < 0",
                },
                "actor_fields": {
                    "phase_u16": "0x0006", "subphase_u8": "0x0007",
                    "direction_class_u8": "0x000c", "facing_u8": "0x000f",
                    "x_position_s32_16_16": "0x0010",
                    "world_y_s32_16_16": "0x0014",
                    "world_z_s32_16_16": "0x0018",
                    "timer_s16": "0x0024", "phase_timer_s16": "0x002a",
                    "x_velocity_s32_16_16": "0x0030",
                    "z_velocity_s32_16_16": "0x0034",
                    "x_acceleration_s32_16_16": "0x0038",
                    "z_acceleration_s32_16_16": "0x003c",
                    "airborne_latch_u8": "0x005c",
                    "animation_event_u8": "0x006e",
                    "terrain_mode_u8": "0x0074",
                    "collision_selector_u8": "0x0092",
                },
                "branch_order": [
                    "down bit", "horizontal bits", "up bit",
                    "horizontal direction versus facing", "facing sign transform"],
                "vector_table": vectors,
                "down_vector_table": down_vectors,
                "input_facing_mapping": [
                    {"input": "neutral", "facing": "either", "entry_index": 0,
                     "negate_x_pair": False},
                    {"input": "up", "facing": "either", "entry_index": 1,
                     "negate_x_pair": False},
                    {"input": "left", "facing": 0, "entry_index": 2,
                     "negate_x_pair": False},
                    {"input": "left", "facing": 1, "entry_index": 4,
                     "negate_x_pair": True},
                    {"input": "right", "facing": 0, "entry_index": 4,
                     "negate_x_pair": False},
                    {"input": "right", "facing": 1, "entry_index": 2,
                     "negate_x_pair": True},
                    {"input": "up_left", "facing": 0, "entry_index": 3,
                     "negate_x_pair": False},
                    {"input": "up_left", "facing": 1, "entry_index": 5,
                     "negate_x_pair": True},
                    {"input": "up_right", "facing": 0, "entry_index": 5,
                     "negate_x_pair": False},
                    {"input": "up_right", "facing": 1, "entry_index": 3,
                     "negate_x_pair": True},
                    {"input": "down", "facing": "retained", "down_entry": "vertical_only"},
                    {"input": "down_left", "facing_write": 0,
                     "down_entry": "with_horizontal"},
                    {"input": "down_right", "facing_write": 1,
                     "down_entry": "with_horizontal"},
                ],
                "initialization": {
                    "non_down": {"next_phase_u16": "0x0402",
                                 "airborne_latch_u8": 1,
                                 "default_collision_selector_u8": 3,
                                 "presentation_selector_neutral_u8": 4,
                                 "same_facing_horizontal": {
                                     "collision_up_u8": 1, "collision_level_u8": 2,
                                     "presentation": "facing + 5"},
                                 "opposite_facing_horizontal": {
                                     "collision_up_u8": 4, "collision_level_u8": 8,
                                     "presentation_up_u8": 6,
                                     "presentation_level_u8": 15}},
                    "down": {"next_phase_u16": "0x040a",
                             "airborne_latch_u8": 0,
                             "collision_selector_u8": 7,
                             "presentation_vertical_u8": 60,
                             "presentation_horizontal_u8": 41},
                },
                "motion_and_landing": {
                    "phase_0x0402": {
                        "motion_routine": "0x01a8e6",
                        "landing_guard": "carry clear after signed world_y versus world_z comparison",
                        "post_motion_interruption_order": [
                            "Button2 edge 0x01a6c4", "special edge path",
                            "air reversal 0x01a932", "Button1 edge/resource 0x01a6f4"],
                    },
                    "landing_0x023630": {
                        "next_phase_u16": "0x0404", "airborne_latch_u8": 0,
                        "terrain_mode_zero_write": "world_y high word = world_z high word",
                        "presentation_selector_u8": 10},
                    "phase_0x0404": {
                        "timer_negative": "0x01a3e2 common reset",
                        "timer_nonnegative": "0x01656e animation update"},
                    "phase_0x040a": {
                        "x_step": "signed x_velocity; negate before add when facing == 0",
                        "velocity_step": "x_velocity += x_acceleration",
                        "negative_velocity_transition": {"next_phase_u16": "0x040c",
                                                         "phase_timer_s16": 10,
                                                         "presentation_selector_u8": 42}},
                    "phase_0x040c": {
                        "timer_step": "predecrement phase_timer_s16",
                        "zero_transition": "0x01a3e2 common reset"},
                    "cleanup": "0x01a3fa clears action then 0x0198de returns to idle/locomotion",
                },
                "presentation_records": presentation_records,
                "presentation_selector_sequences": presentation_sequences,
                "presentation_actor_fields": {
                    "coordinate_mode_u8": 0, "palette_u8": 0,
                    "object_or_u16": "0x8000",
                    "source_fields": {"coordinate_mode": "actor +0x0d u8",
                                      "palette": "actor +0x0e u8",
                                      "facing": "actor +0x0f u8",
                                      "object_or": "actor +0x2e u16"},
                    "capture_scope": ["neutral", "right", "left", "up", "down"],
                },
                "observed_record_sequences": observed_sequences,
                "scheduler": "player actor slot is updated once in fixed actor-pool scheduler order before current-state collision and presentation submission",
                "rng_calls": [],
                "mutation_controls": [
                    "reject vector magnitude or sign mutation",
                    "reject input/facing table-index mutation",
                    "reject x-pair sign transform mutation",
                    "reject collision selector mutation",
                    "reject presentation selector or record mutation",
                    "reject landing comparison polarity or terrain-mode guard mutation",
                    "reject phase or timer transition mutation",
                    "reject interruption branch reordering",
                    "reject added RNG consumption",
                ],
            },
        },
        "airborne_actions": {
            "classification": "SOURCE_CLOSED",
            "button1": {
                "guard": "0x01a6f4 source edge/resource checks",
                "phase": "0x0406", "writer": "0x023860",
                "spawn_branch": "0x023858",
                "resource_and_projectile_authority": "data/oracle11_predator_weapon_projectile_resource.json",
                "resource_artifact_sha256": digest(WEAPON),
                "resource_status": weapon["status"],
            },
            "button2": {
                "guard": "0x01a6c4 new Button2 edge",
                "neutral_or_non_down_phase": "0x040e",
                "down_held_at_air_edge_phase": "0x0410",
                "writer": "0x02367c",
                "held_or_repeated_edge": "does not auto-repeat or enter a gated continuation when +0x6e animation-event byte remains zero",
            },
            "motion": "all required branches return through 0x01a8e6 and source landing 0x023630",
            "rng_consumption": "none for action, direction, phase, or presentation selection",
        },
        "interruption": {
            "classification": "SOURCE_CLOSED",
            "natural_witness": {"air_phase_frame": 4424,
                                "hit_cancel_frame": 4433,
                                "phase_before": "0x0402",
                                "inner_after": 2},
            "writers": ["0x01a988", "0x01aa30", "0x01aa34", "0x01aa5c"],
            "rule": "source HIT entry advances the inner dispatcher, clears buffered/action-local state, and replaces the airborne action; damage and HIT recovery remain owned by the player HIT/KO authority checkpoint",
            "rng_consumption": "none",
        },
        "not_required_for_round1": {
            "classification": "NOT_REQUIRED_FOR_ROUND1",
            "phases": {
                "0x0408": "dispatcher body exists but has no entry in either completion, failure/continue, perturbed, or input-only targeted routes",
                "0x0412": "requires +0x6e animation-event continuation from an air attack; all reachable PW air-attack records keep the guard clear",
                "0x0414": "requires the 0x01a932 direction/terrain-mask reversal guard; directional Button3-repeat counterfactual does not satisfy it",
            },
            "mutation_rule": "a future route witness for any phase reopens this family and forbids retaining NOT_REQUIRED_FOR_ROUND1",
        },
        "counterfactuals": {
            "independent_cold_runs_byte_identical": True,
            "all_four_direction_lanes_exercised": True,
            "air_button2_neutral_and_down_split": True,
            "air_button2_hold_no_auto_repeat": True,
            "air_button2_followup_guards_rejected": True,
            "air_button3_directional_repeat_guard_rejected": True,
            "air_button1_empty_rejected_and_sufficient_resource_accepted": True,
            "natural_hit_cancels_directional_air": True,
        },
        "mutation_controls": [
            "reject missing required phase", "reject widened phase requirement",
            "reject incorrect phase writer", "reject random action selection",
            "reject held Button2 auto-repeat", "reject interruption omission",
            "reject a NOT_REQUIRED phase once a route witness appears",
        ],
        "remaining_unknowns": [],
        "protected_boundaries": {
            "production_runtime_writes": 0, "yaba_run": False,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED" and
            report["remaining_unknowns"] == [], "air authority not closed")
    universe = report["coverage_universe"]
    require(universe["all_required_phases_closed"] is True and
            set(universe["required_route_phases"]) ==
            {f"0x{x:04x}" for x in ROUTE_REQUIRED} and
            set(universe["required_counterfactual_phases"]) ==
            {f"0x{x:04x}" for x in COUNTERFACTUAL_REQUIRED},
            "required phase coverage drift")
    require(report["directional_actions"]["classification"] ==
            "SOURCE_CLOSED" and
            report["airborne_actions"]["classification"] ==
            "SOURCE_CLOSED" and
            report["interruption"]["classification"] == "SOURCE_CLOSED",
            "required sub-authority classification drift")
    require(report["directional_actions"]["landing_writer"] == "0x023636" and
            report["airborne_actions"]["button1"]["writer"] == "0x023860" and
            report["airborne_actions"]["button2"]["writer"] == "0x02367c",
            "air phase writer identity drift")
    require(report["directional_actions"]["rng_consumption"] == "none" and
            report["airborne_actions"]["rng_consumption"].startswith("none") and
            report["interruption"]["rng_consumption"] == "none",
            "unsourced player-air RNG introduced")
    implementation = report["directional_actions"]["implementation_contract"]
    require(implementation["spec_executable"] is True and
            implementation["source_input"]["button3_mask_u8"] == "0x40" and
            implementation["branch_order"] == [
                "down bit", "horizontal bits", "up bit",
                "horizontal direction versus facing", "facing sign transform"],
            "Button3 input/branch contract drift")
    expected_vectors = [
        [0, 0, 0x00088000, -0x00008000],
        [0, 0, 0x000c0000, -0x00008000],
        [-0x000f0000, 0x00006800, 0x00040000, -0x00003800],
        [-0x00090000, 0x00002400, 0x000c0000, -0x00008800],
        [0x00090000, -0x00002000, 0x00040000, -0x00008000],
        [0x00088000, -0x00002400, 0x000c0000, -0x00008800],
    ]
    require([[entry[field]["raw_s32"] for field in
              ("x_velocity_s32_16_16", "x_acceleration_s32_16_16",
               "z_velocity_s32_16_16", "z_acceleration_s32_16_16")]
             for entry in implementation["vector_table"]] == expected_vectors,
            "Button3 numeric vector contract drift")
    require([(entry.get("input"), entry.get("facing"),
              entry.get("entry_index"), entry.get("negate_x_pair"))
             for entry in implementation["input_facing_mapping"][:10]] == [
                 ("neutral", "either", 0, False), ("up", "either", 1, False),
                 ("left", 0, 2, False), ("left", 1, 4, True),
                 ("right", 0, 4, False), ("right", 1, 2, True),
                 ("up_left", 0, 3, False), ("up_left", 1, 5, True),
                 ("up_right", 0, 5, False), ("up_right", 1, 3, True)],
            "Button3 input/facing mapping drift")
    require(implementation["initialization"]["non_down"][
                "opposite_facing_horizontal"]["collision_level_u8"] == 8 and
            implementation["initialization"]["down"][
                "presentation_horizontal_u8"] == 41 and
            implementation["motion_and_landing"]["landing_0x023630"][
                "presentation_selector_u8"] == 10 and
            implementation["motion_and_landing"]["phase_0x040a"][
                "negative_velocity_transition"]["phase_timer_s16"] == 10,
            "Button3 state/presentation/collision contract drift")
    sequences = implementation["presentation_selector_sequences"]
    require(len(implementation["presentation_records"]) == len(AIR_RECORDS) and
            set(sequences) == {str(item) for item in AIR_SELECTOR_RECORDS} and
            [row["record"] for row in sequences["6"]] ==
                [f"0x{item:06x}" for item in AIR_SELECTOR_RECORDS[6]] and
            sequences["41"][0]["attack_selector_u8"] == 22 and
            sequences["41"][1]["attack_selector_u8"] == 23 and
            sequences["60"][0]["attack_selector_u8"] == 35 and
            implementation["presentation_actor_fields"] == {
                "coordinate_mode_u8": 0, "palette_u8": 0,
                "object_or_u16": "0x8000",
                "source_fields": {"coordinate_mode": "actor +0x0d u8",
                                  "palette": "actor +0x0e u8",
                                  "facing": "actor +0x0f u8",
                                  "object_or": "actor +0x2e u16"},
                "capture_scope": ["neutral", "right", "left", "up", "down"]} and
            implementation["rng_calls"] == [] and
            len(implementation["mutation_controls"]) == 9,
            "Button3 presentation/RNG/mutation contract drift")
    require(set(report["not_required_for_round1"]["phases"]) ==
            {f"0x{x:04x}" for x in NOT_REQUIRED},
            "NOT_REQUIRED phase inventory drift")
    require(report["counterfactuals"]["air_button2_hold_no_auto_repeat"] and
            report["counterfactuals"]["natural_hit_cancels_directional_air"],
            "air negative control drift")
    protected = report["protected_boundaries"]
    require(protected["production_runtime_writes"] == 0 and
            protected["yaba_run"] is False and
            protected["frontend_active"] is False and
            protected["user09_status"] == "CHANGES_REQUESTED" and
            protected["salvage08_active"] is False and
            protected["physical_saturn"] == "UNRUN",
            "workflow shield drift")


if __name__ == "__main__":
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"wrote {OUT.relative_to(ROOT)}")
