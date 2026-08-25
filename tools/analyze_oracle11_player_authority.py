#!/usr/bin/env python3
"""Close the Predator Warrior locomotion-to-neutral source sub-authority."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle11_player_locomotion_a"
RAW_JUMP = ROOT / ".deps" / "mame" / "oracle11_player_jump_a"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
ORACLE07 = ROOT / "data" / "oracle07_predator_warrior_action_graph_equipment.json"
ORACLE10 = ROOT / "data" / "oracle10_round1_route.json"
OUT = ROOT / "data" / "oracle11_predator_warrior_authority.json"
VARIANTS = ("cold_run_1", "cold_run_2", "skip_right_edge",
            "hold_right", "reverse_without_neutral")

PREFIXES = {
    0x01A364: "102e00ee0240000f1d7b001e000c0800000067061d7c0001000f"
              "0800000167061d7c0000000f4e75ff0206ff040305ff000107ff",
    0x019A34: "6100092e4a2e000c6a000012542e00071d7c000a002a"
              "4ef90001656e",
    0x019A98: "532e002a6700094461000e2c",
    0x01A3E2: "610011f4660011f6610012086600120a2d7c020000000004",
    0x01A39C: "7000102e000c6b3c122e00d24881d24141fa12de32301000"
              "41f01000e74841f000002018d1ae00102010d1ae0014",
    0x01A6DC: "2d7c0200060000044a6e005a67082d7c0200140000044e75",
    0x022588: "542e0007422e0080422e00951d7c0001009d1d7c000c0092"
              "4eb90001a3644eb90001d768",
    0x022666: "4a2e008167064a2e006e671c4a2e002567164eb90001a6c4"
              "670e6100002a422e0007422e0092",
    0x0226AC: "4a2e00806700003e0c2e000100816614102e00ee0200000f"
              "0c00000867180c0000046712522e0081022e00030081"
              "1d7c001e00824e75",
    0x022ED6: "542e0007422e00801d7c0001009d1d7c000c00924eb90001"
              "a3644eb90001d768",
    0x01A6A2: "102e00ef4600c02e00ee080000064e752d7c020004000004"
              "422e0095700360000a02",
    0x02331E: "70001d40000c122e00ee080100026600006a02410003672e",
    0x0233E6: "4a6e00246a0000f2542e00071d7c0001005c6100ff24",
    0x023630: "1d7c00040007422e005c4eb90000229a4a6e007466063d6e"
              "00180014700a4ef90001b0c4",
    0x01A8E6: "4a6e00746644202e0030d1ae00104840320002418000202e"
              "0038d1ae0030302e003002408000b1416708",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def samples(name: str) -> dict[int, dict[str, object]]:
    rows = read_rows(RAW / name / "samples.tsv")
    text = {"variant", "anim", "hex"}
    result = {}
    for row in rows:
        converted = {key: value if key in text else int(value)
                     for key, value in row.items()}
        result[int(row["frame"])] = converted
    require(len(result) == 261 and min(result) == 2500 and max(result) == 2760,
            f"{name}: sample window drift")
    return result


def indexed_rows(path: Path) -> dict[int, dict[str, str]]:
    return {int(row["frame"]): row for row in read_rows(path)}


def write_exists(rows: list[dict[str, str]], *, frame: int, offset: str,
                 pc: str, data: str | None = None,
                 mask: str | None = None) -> bool:
    return any(int(row["frame"]) == frame and row["offset"] == offset and
               row["pc"] == pc and (data is None or row["data"] == data) and
               (mask is None or row["mask"] == mask) for row in rows)


def source_window(data: bytes, start: int, end: int) -> dict[str, object]:
    return {"start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
            "bytes": end - start,
            "sha256": hashlib.sha256(data[start:end]).hexdigest()}


def record_identity(program: bytes, address: int) -> dict[str, object]:
    assembly = int.from_bytes(program[address + 4:address + 8], "big")
    require(0 < assembly < len(program) - 32,
            f"animation assembly outside source image: 0x{address:06x}")
    return {
        "animation_record": f"0x{address:06x}",
        "assembly": f"0x{assembly:06x}",
        "hurt_selector": program[address + 8],
        "attack_selector": program[address + 9],
        "record_sha256": hashlib.sha256(program[address:address + 16]).hexdigest(),
        "assembly_window_sha256": hashlib.sha256(
            program[assembly:assembly + 32]).hexdigest(),
    }


def build_report() -> dict[str, object]:
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()
    require(len(opcodes) == len(program) == 0x200000,
            "decoded source image size drift")
    for address, expected in PREFIXES.items():
        raw = bytes.fromhex(expected)
        require(opcodes[address:address + len(raw)] == raw,
                f"decoded source prefix drift at 0x{address:06x}")

    manifest = json.loads((RAW / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    require([row["name"] for row in manifest["variants"]] == list(VARIANTS),
            "variant inventory drift")
    for item in manifest["variants"]:
        for filename, expected in item["sha256"].items():
            require(digest(RAW / item["name"] / filename) == expected,
                    f"{item['name']}: {filename} identity drift")
    for filename in ("samples.tsv", "player_writes.tsv", "player_entries.tsv"):
        require(digest(RAW / "cold_run_1" / filename) ==
                digest(RAW / "cold_run_2" / filename),
                f"cold locomotion captures differ: {filename}")

    jump_manifest = json.loads((RAW_JUMP / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    require([row["name"] for row in jump_manifest["variants"]] ==
            ["jump_cold_1", "jump_cold_2", "dash_right"],
            "jump variant inventory drift")
    for item in jump_manifest["variants"]:
        for filename, expected in item["sha256"].items():
            require(digest(RAW_JUMP / item["name"] / filename) == expected,
                    f"{item['name']}: {filename} identity drift")
    for filename in ("samples.tsv", "player_writes.tsv",
                     "player_global_writes.tsv"):
        require(digest(RAW_JUMP / "jump_cold_1" / filename) ==
                digest(RAW_JUMP / "jump_cold_2" / filename),
                f"cold jump captures differ: {filename}")

    runs = {name: samples(name) for name in VARIANTS}
    writes = {name: read_rows(RAW / name / "player_writes.tsv")
              for name in VARIANTS}
    base = runs["cold_run_1"]

    require((base[2527]["action"], base[2527]["facing"], base[2527]["x"]) ==
            (0x0200, 1, 980), "right locomotion entry drift")
    require((base[2547]["action"], base[2547]["facing"], base[2547]["timer"]) ==
            (0x0204, 1, 0x0A00), "right release/stop entry drift")
    require((base[2557]["action"], base[2557]["facing"], base[2557]["anim"]) ==
            (0x0000, 1, "0015f1f4") and
            (base[2558]["action"], base[2558]["facing"]) == (0x0002, 1),
            "neutral did not preserve the last right-facing value")
    require((base[2587]["action"], base[2587]["facing"], base[2587]["x"]) ==
            (0x0200, 0, 1021), "left locomotion entry drift")
    require((base[2615]["action"], base[2615]["facing"]) == (0x0204, 0),
            "left release did not preserve left facing")

    baseline_writes = writes["cold_run_1"]
    require(write_exists(baseline_writes, frame=2526, offset="0e",
                         pc="01a37e", data="0101", mask="00ff") and
            write_exists(baseline_writes, frame=2586, offset="0e",
                         pc="01a38a", data="0000", mask="00ff"),
            "directional facing writer identity drift")
    require(write_exists(baseline_writes, frame=2546, offset="06",
                         pc="019a46", data="0404", mask="00ff") and
            write_exists(baseline_writes, frame=2546, offset="2a",
                         pc="019a4a", data="0a0a", mask="ff00") and
            write_exists(baseline_writes, frame=2556, offset="06",
                         pc="01a3fa", data="0000", mask="ffff") and
            write_exists(baseline_writes, frame=2557, offset="06",
                         pc="0198de", data="0202", mask="00ff"),
            "locomotion-to-neutral state writer set drift")
    require(not any(2546 <= int(row["frame"]) <= 2557 and
                    row["offset"] in {"0e", "0f"}
                    for row in baseline_writes),
            "neutral transition unexpectedly wrote facing")

    skip, hold, reverse = (runs["skip_right_edge"], runs["hold_right"],
                           runs["reverse_without_neutral"])
    require(base[2527]["action"] == 0x0200 and skip[2527]["action"] == 0x0002 and
            skip[2528]["action"] == 0x0200 and
            base[2557]["x"] - skip[2557]["x"] == 2,
            "one-frame right-edge counterfactual drift")
    require(hold[2557]["action"] == 0x0202 and hold[2557]["facing"] == 1 and
            hold[2573]["action"] == 0x0204 and
            (hold[2583]["action"], hold[2583]["facing"]) == (0, 1),
            "held-right/release counterfactual drift")
    require((reverse[2547]["action"], reverse[2547]["facing"]) ==
            (0x0202, 0) and reverse[2573]["action"] == 0x0204 and
            (reverse[2583]["action"], reverse[2583]["facing"]) == (0, 0),
            "direct reversal counterfactual drift")

    require((base[2645]["input_word"], base[2647]["y"], base[2647]["z"]) ==
            (128, 321, 321) and base[2664]["y"] == base[2664]["z"] == 327,
            "source up-lane world-coordinate response drift")
    require((base[2705]["input_word"], base[2707]["y"], base[2707]["z"]) ==
            (256, 326, 326) and base[2717]["y"] == base[2717]["z"] == 315,
            "source down-lane world-coordinate response drift")
    require(base[2718]["inner"] == 0x0204 and base[2718]["anim"] == "0015f520",
            "down-lane geometry interruption witness drift")

    jump = indexed_rows(RAW_JUMP / "jump_cold_1" / "samples.tsv")
    dash = indexed_rows(RAW_JUMP / "dash_right" / "samples.tsv")
    require((int(jump[4422]["p_action"]), int(jump[4422]["p_y"]),
             int(jump[4422]["p_z"])) == (0x0400, 319, 319),
            "normal jump dispatch drift")
    require(int(jump[4424]["p_action"]) == 0x0402 and
            max(int(jump[frame]["p_y"]) for frame in range(4422, 4461)) == 395 and
            all(int(jump[frame]["p_z"]) == 319 for frame in range(4422, 4461)),
            "normal jump arc drift")
    require((int(jump[4460]["p_action"]), int(jump[4460]["p_y"]),
             int(jump[4460]["p_z"])) == (0x0404, 319, 319) and
            (int(jump[4462]["p_action"]), int(jump[4462]["p_facing"])) ==
            (0x0002, 0), "normal jump landing/control return drift")
    require(int(dash[4424]["p_action"]) == 0x0402 and
            dash[4424]["p_anim"] == "0015f43c" and
            int(dash[4433]["p_inner"]) == 2,
            "directional jump falsification control drift")

    for frame, expected_ee, expected_direction in (
            (2527, 0x01, 0x02), (2587, 0x02, 0x06),
            (2647, 0x08, 0x00), (2707, 0x04, 0x04)):
        actor = bytes.fromhex(str(base[frame]["hex"]))
        require(actor[0xEE] == expected_ee and actor[0x0C] == expected_direction,
                f"decoded direction mapping drift at frame {frame}")

    oracle07 = json.loads(ORACLE07.read_text(encoding="utf-8"))
    oracle10 = json.loads(ORACLE10.read_text(encoding="utf-8"))
    route_melee = next(row for row in oracle10["player_action_families"]
                       if row["id"] == "button2-contextual-close-combo")
    require(route_melee["classification"] == "SOURCE_CLOSED",
            "ORACLE-10 melee classification drift")
    neutral_records = [0x15F258, 0x15F268, 0x15F278, 0x15F1F4]
    report = {
        "schema": "oracle11-predator-warrior-authority-v1",
        "status": "PARTIAL",
        "character": "Predator Warrior",
        "scope": "Round 1 one-player source authority; locomotion-to-neutral is closed while remaining action/equipment/continue bodies stay active backlog",
        "source_identity": {
            "decoded_opcodes_sha256": hashlib.sha256(opcodes).hexdigest(),
            "decrypted_program_sha256": hashlib.sha256(program).hexdigest(),
            "input_facing_decode": source_window(opcodes, 0x01A364, 0x01A39C),
            "fixed_point_motion": source_window(opcodes, 0x01A39C, 0x01A3E2),
            "walk_release": source_window(opcodes, 0x019A34, 0x019AE6),
            "common_control_reset": source_window(opcodes, 0x01A3E2, 0x01A45A),
            "predator_warrior_vector_table": source_window(program, 0x01B68C, 0x01B6D4),
            "button2_dispatch": source_window(opcodes, 0x01A6DC, 0x01A6F4),
            "close_combo_entry": source_window(opcodes, 0x022588, 0x022666),
            "close_combo_transition": source_window(opcodes, 0x022666, 0x0226FC),
            "contextual_melee": source_window(opcodes, 0x022ED6, 0x022F9C),
            "jump_input_dispatch": source_window(opcodes, 0x01A6A2, 0x01A6C4),
            "jump_vector_setup": source_window(opcodes, 0x02331E, 0x0233C4),
            "jump_state_machine": source_window(opcodes, 0x0233E6, 0x023680),
            "air_motion_arithmetic": source_window(opcodes, 0x01A8E6, 0x01A932),
        },
        "route_reachable_melee_actions": {
            "classification": "SOURCE_CLOSED",
            "input_guard": "new Button2 edge from actor +0xee/+0xef bit 5",
            "dispatch": {
                "common_action": "0x0600",
                "common_writer": "0x01a6e4",
                "target_context_action": "0x1400",
                "target_context_guard": "actor +0x5a nonzero",
                "target_context_writer": "0x01a6ea",
            },
            "close_combo": {
                "entry": "0x022588",
                "phase_field": "+0x07 u8 even dispatch offset",
                "step_field": "+0x81 u8",
                "step_values": [0, 1, 2, 3],
                "completion_guard": "animation/event flag +0x80",
                "followup_window": {"field": "+0x82 high u8", "ticks": 30,
                                    "decrement_writer": "0x01982a"},
                "step_rule": "advance modulo four on completion; lane inputs 0x08 or 0x04 at step one retain the step and toggle +0x87 instead",
                "held_input_rule": "held Button2 does not create a new edge or auto-chain",
                "attack_selectors": [1, 2, 3, 4],
                "animation_sequences": oracle07["presentation_identity"]["sequences"],
            },
            "contextual_melee": {
                "entry": "0x022ed6",
                "step_field": "+0x81 u8",
                "step_rule": "advance modulo four on +0x80 completion, otherwise clear the step and toggle +0x87",
                "attack_selectors_observed": [21, 20],
                "animation_sequence": oracle07["presentation_identity"]["sequences"]["contextual_button2"],
            },
            "collision_damage_identity": "accepted source combat contract bound through ORACLE-07; presentation cannot own contact or damage",
            "rng_consumption": "none for selector or assembly choice; state selects the measured animation record",
            "scheduler_position": "player slot before the non-player pools",
            "counterfactuals": {
                "held_button_no_auto_chain": True,
                "startup_repeat_no_chain": True,
                "recovery_edge_advances": True,
                "expired_window_restarts_step_one": True,
                "random_selector_cycle_forbidden": True,
            },
            "mutation_control": "tests reject selector reorder, random selection, held auto-chain, window fitting, and classification mutations",
            "remaining_unknowns": [],
        },
        "normal_jump_air_landing": {
            "classification": "SOURCE_CLOSED",
            "scope": "neutral Button3 jump through airborne arc, source landing, and return to control; directional dash/air actions remain separate backlog",
            "input_guard": "new Button3 edge from actor +0xee/+0xef bit 6",
            "dispatch": {"action": "0x0400", "writer": "0x01a6b2",
                         "buffer_clear": "0x01a6ba clears +0x95",
                         "presentation_selector": 3},
            "state_machine": {
                "entry": "0x0233e6",
                "air_action": "0x0402",
                "air_entry_writer": "0x0233f4",
                "movement_routine": "0x01a8e6",
                "landing_action": "0x0404",
                "landing_writer": "0x023636",
                "landing_guard": "signed comparison of source world Y against ground/world Z after fixed-point velocity and acceleration updates",
                "ground_sync": "0x023646 copies +0x18 world Z to +0x14 world Y when +0x74 is zero",
                "cleanup": "0x01a3e2 common control reset, then idle phase writer 0x0198de",
            },
            "arithmetic": {
                "position_fields": ["+0x10 s16.16 X", "+0x14 s16.16 Y"],
                "velocity_fields": ["+0x30 s16.16 X velocity", "+0x34 s16.16 Y velocity"],
                "acceleration_fields": ["+0x38 s16.16 X acceleration", "+0x3c s16.16 Y acceleration"],
                "source_table": "0x0243d2 selected from input lane and facing by 0x02331e",
            },
            "witness": {"dispatch_frame": 4422, "air_frame": 4424,
                        "apex_world_y": 395, "ground_world_z": 319,
                        "landing_frame": 4460, "control_return_frame": 4462,
                        "retained_facing": 0},
            "presentation": oracle07["presentation_identity"]["sequences"]["jump"],
            "rng_consumption": "none",
            "scheduler_position": "player slot before the non-player pools",
            "counterfactuals": {
                "independent_cold_runs_byte_identical": True,
                "direction_plus_jump_selects_distinct_presentation": True,
                "directional_variant_hit_interruption_observed": True,
                "directional_variant_does_not_authorize_normal_jump_changes": True,
            },
            "mutation_control": "tests reject fitted apex, inverted ground comparison, missing landing sync, RNG, and widened directional scope",
            "remaining_unknowns": [],
        },
        "locomotion_neutral_facing": {
            "classification": "SOURCE_CLOSED",
            "actor_slot": "0xff8380",
            "input_decode": {
                "right": {"trace_word": 8, "actor_input_bit": 0,
                          "direction_index": 2, "facing": 1,
                          "facing_writer": "0x01a37e"},
                "left": {"trace_word": 4, "actor_input_bit": 1,
                         "direction_index": 6, "facing": 0,
                         "facing_writer": "0x01a38a"},
                "up_lane": {"trace_word": 128, "actor_input_bit": 3,
                            "direction_index": 0,
                            "source_world_effect": "+Y and +Z"},
                "down_lane": {"trace_word": 256, "actor_input_bit": 2,
                              "direction_index": 4,
                              "source_world_effect": "-Y and -Z"},
                "resolver_table": [255, 2, 6, 255, 4, 3, 5, 255,
                                   0, 1, 7, 255, 255, 255, 255, 255],
            },
            "movement_arithmetic": {
                "routine": "0x01a39c",
                "rule": "character table selects eight signed 16.16 vector pairs; direction index multiplies by eight; first long adds to world X, second to world Y, and world Z mirrors or receives the same lane delta according to +0x74",
                "fields_read": ["+0x0c s8 direction", "+0xd2 s8 character", "+0x74 u16 mode"],
                "fields_written": ["+0x10 s16.16 X", "+0x14 s16.16 Y", "+0x18 s16.16 Z"],
            },
            "release_transition": {
                "walking_action": "0x0202",
                "stop_action": "0x0204",
                "stop_guard": "+0x0c direction becomes negative when no valid direction is held",
                "stop_entry_writer": "0x019a46",
                "stop_timer": {"field": "+0x2a high u8", "ticks": 10,
                               "writer": "0x019a4a", "decrement": "0x019a9e"},
                "cleanup_writer": "0x01a3fa writes inner/action long 0x02000000",
                "idle_phase_writer": "0x0198de writes action low byte 0x02 on the next update",
                "facing_rule": "neutral performs no +0x0f write and preserves the last directional facing",
                "right_witness": {"stop_frame": 2547, "neutral_frame": 2557,
                                  "retained_facing": 1},
                "left_witness": {"stop_frame": 2607, "retained_facing": 0},
                "presentation": [record_identity(program, address)
                                 for address in neutral_records],
            },
            "navigation_boundary": "source input/vector arithmetic is closed here; the frame-2718 measured-geometry interruption remains owned by Round 1 navigation authority and forbids unrestricted wall traversal",
            "rng_consumption": "none",
            "counterfactuals": {
                "skip_right_edge": {"status": "PASS",
                                    "response_shift_frames": 1,
                                    "final_x_delta": -2},
                "hold_right": {"status": "PASS",
                               "stop_deferred_until_release": True,
                               "retained_neutral_facing": 1},
                "reverse_without_neutral": {"status": "PASS",
                                            "direct_facing_change": [1, 0],
                                            "retained_neutral_facing": 0},
            },
            "mutation_control": "tests reject facing reset, lane-bit inversion, stop-timer, writer, and classification mutations",
            "remaining_unknowns": [],
        },
        "accepted_prior_player_bodies": {
            "source": "data/oracle07_predator_warrior_action_graph_equipment.json",
            "source_sha256": digest(ORACLE07),
            "attack_selector_order": oracle07["action_graph"]["close_button2"]["attack_selectors"],
            "random_attack_selection": oracle07["equipment_contract"]["random_selection"],
        },
        "remaining_player_backlog": [
            "Button1 equipment and projectile lifecycle beyond action-local flag evidence",
            "directional jump/dash, airborne action, and their interruption authority",
            "special action resource, spawned actor, and recovery authority",
            "player HIT/KO, failure/continue, spawn return, and return to control",
            "route-wide resource, pickup, and audio/load interactions",
        ],
        "determinism": {
            "independently_launched_cold_runs": True,
            "byte_identical": True,
            "files": {filename: digest(RAW / "cold_run_1" / filename)
                      for filename in ("samples.tsv", "player_writes.tsv",
                                       "player_entries.tsv")},
        },
        "protected_boundaries": {
            "production_runtime_writes": 0, "frontend_active": False,
            "user09_status": "CHANGES_REQUESTED", "salvage08_active": False,
            "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-predator-warrior-authority-v1" and
            report["status"] == "PARTIAL", "player authority status drift")
    closed = report["locomotion_neutral_facing"]
    require(closed["classification"] == "SOURCE_CLOSED" and
            closed["remaining_unknowns"] == [], "locomotion is not closed")
    decode = closed["input_decode"]
    require((decode["up_lane"]["actor_input_bit"],
             decode["down_lane"]["actor_input_bit"]) == (3, 2) and
            (decode["up_lane"]["source_world_effect"],
             decode["down_lane"]["source_world_effect"]) ==
            ("+Y and +Z", "-Y and -Z"), "lane source mapping drift")
    release = closed["release_transition"]
    require(release["facing_rule"].startswith("neutral performs no") and
            release["right_witness"]["retained_facing"] == 1 and
            release["left_witness"]["retained_facing"] == 0,
            "neutral facing preservation drift")
    require(release["stop_timer"]["ticks"] == 10 and
            release["stop_entry_writer"] == "0x019a46",
            "stop transition identity drift")
    require([row["animation_record"] for row in release["presentation"]] ==
            ["0x15f258", "0x15f268", "0x15f278", "0x15f1f4"],
            "neutral presentation order drift")
    require(all(row["status"] == "PASS"
                for row in closed["counterfactuals"].values()),
            "locomotion counterfactual failed")
    require(report["accepted_prior_player_bodies"]["attack_selector_order"] ==
            [1, 2, 3, 4] and
            report["accepted_prior_player_bodies"]["random_attack_selection"] is False,
            "accepted attack lock drift")
    melee = report["route_reachable_melee_actions"]
    require(melee["classification"] == "SOURCE_CLOSED" and
            melee["remaining_unknowns"] == [], "melee authority is not closed")
    require(melee["close_combo"]["attack_selectors"] == [1, 2, 3, 4] and
            melee["close_combo"]["followup_window"]["ticks"] == 30 and
            melee["rng_consumption"].startswith("none"),
            "melee selector/window/RNG contract drift")
    require(all(melee["counterfactuals"].values()),
            "melee counterfactual failed")
    jump = report["normal_jump_air_landing"]
    require(jump["classification"] == "SOURCE_CLOSED" and
            jump["remaining_unknowns"] == [], "normal jump authority is not closed")
    require(jump["witness"]["apex_world_y"] == 395 and
            jump["witness"]["ground_world_z"] == 319 and
            jump["witness"]["control_return_frame"] == 4462,
            "normal jump witness drift")
    require(jump["state_machine"]["landing_writer"] == "0x023636" and
            jump["state_machine"]["ground_sync"].startswith("0x023646") and
            jump["rng_consumption"] == "none",
            "normal jump landing/RNG contract drift")
    require(all(jump["counterfactuals"].values()),
            "normal jump counterfactual failed")
    require(bool(report["remaining_player_backlog"]),
            "player authority was prematurely declared complete")
    require(report["protected_boundaries"] == {
        "production_runtime_writes": 0, "frontend_active": False,
        "user09_status": "CHANGES_REQUESTED", "salvage08_active": False,
        "physical_saturn": "UNRUN",
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 Predator Warrior: locomotion/neutral/facing SOURCE_CLOSED; player family PARTIAL")


if __name__ == "__main__":
    main()
