#!/usr/bin/env python3
"""Close the Predator Warrior locomotion-to-neutral source sub-authority."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle11_player_locomotion_a"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
ORACLE07 = ROOT / "data" / "oracle07_predator_warrior_action_graph_equipment.json"
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

    for frame, expected_ee, expected_direction in (
            (2527, 0x01, 0x02), (2587, 0x02, 0x06),
            (2647, 0x08, 0x00), (2707, 0x04, 0x04)):
        actor = bytes.fromhex(str(base[frame]["hex"]))
        require(actor[0xEE] == expected_ee and actor[0x0C] == expected_direction,
                f"decoded direction mapping drift at frame {frame}")

    oracle07 = json.loads(ORACLE07.read_text(encoding="utf-8"))
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
            "route-reachable action/state dispatch beyond accepted ORACLE-07 subset",
            "equipment and projectile lifecycle beyond action-local flag evidence",
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
