#!/usr/bin/env python3
"""Validate ORACLE-06 private traces and emit the bounded encounter contract."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle06_round1_encounter"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
ORACLE04 = ROOT / "data" / "oracle04_predator_warrior_control_actions.json"
ORACLE05 = ROOT / "data" / "oracle05_street_alien_ai.json"
OUT = ROOT / "data" / "oracle06_round1_encounter.json"
VARIANTS = ["cold_run_1", "cold_run_2", "entry_hold", "clear_attack_suppression"]
FILES = ["samples.tsv", "actors.tsv", "controller_writes.tsv", "qsound.tsv"]
FIRST_FRAME, LAST_FRAME = 2200, 7200
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("ascii")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_samples(name: str) -> dict[int, dict[str, int]]:
    result: dict[int, dict[str, int]] = {}
    for raw in read_tsv(RAW / name / "samples.tsv"):
        frame = int(raw["frame"])
        result[frame] = {key: int(value) for key, value in raw.items()
                         if key != "variant"}
    require(list(result) == list(range(FIRST_FRAME, LAST_FRAME + 1)),
            f"{name}: non-contiguous sample window")
    return result


def first_diff(base: dict[int, dict[str, int]], other: dict[int, dict[str, int]],
               fields: list[str]) -> int | None:
    return next((frame for frame in base
                 if any(base[frame][field] != other[frame][field]
                        for field in fields)), None)


def exact_run(rows: dict[int, dict[str, int]], field: str, value: int,
              first: int, last: int) -> None:
    require(all(rows[frame][field] == value for frame in range(first, last + 1)),
            f"{field}={value} run drifted at {first}..{last}")
    if first > FIRST_FRAME:
        require(rows[first - 1][field] != value, f"{field} run starts before {first}")
    if last < LAST_FRAME:
        require(rows[last + 1][field] != value, f"{field} run ends after {last}")


def validate_static_image() -> dict[str, object]:
    require(digest(OPCODES) == OPCODE_SHA256, "decrypted opcode image identity drift")
    image = OPCODES.read_bytes()
    signatures = {
        0x00C15C: "66267001323c01004eb9000ad580546d0008426d000c426d0010426d00143b7c0340029e610006024ef900008438",
        0x00C754: "1b7c000102081b7c000101d51b6d01bf0236422d020a422d0209422d023a422d01b9426d9744422d023d422d023e4e75",
        0x0083F0: "3b7c000190e84ef9000019724ef90000bfd000010102010202034a2d01f367000028546d0008426d000c1b7c000102404eb90000c754",
        0x028BA0: "000000834e754a6e00426706536e0042661a4eb900020a1067121b7c000101f33b7c0480029e4ef900020cf44e75",
        0x008510: "4eb9000add764eb9000a99c2422d02484a2d01af66364a2d01d46630102d0380802d0480802d058066223b7c00060004",
        0x00C1EC: "00008438102d0236c02d01af6624546d0008426d000c426d0010426d00143b7c0300029c3b7c0400029e61000596",
    }
    for address, expected in signatures.items():
        require(image[address:address + len(expected) // 2].hex() == expected,
                f"opcode signature drift at 0x{address:06x}")
    return {
        "opcode_image_sha256": OPCODE_SHA256,
        "street_active_controller_block": "0x00c15c",
        "active_state_write_pc": "0x00c170",
        "shared_state_clear_routine": "0x00c784",
        "withdrawal_actor_block": "0x028ba0",
        "withdrawal_flag_write_pc": "0x028bc0",
        "withdrawal_controller_write_pc": "0x008418",
        "next_segment_active_write_pc": "0x00c200",
        "actor_cleanup_routine": "0x008522",
    }


def completed_voice_starts(rows: list[dict[str, str]], frame: int) -> list[dict[str, object]]:
    completed = [row for row in rows if row["port"] == "d002" and
                 int(row["frame"]) == frame]
    values = {int(row["register"], 16): int(row["value"], 16)
              for row in completed}
    names = ("bank", "address", "rate", "phase", "loop_length",
             "end_address", "volume")
    result = []
    for voice in range(16):
        regs = [((voice - 1) & 15) << 3, voice * 8 + 1, voice * 8 + 2,
                voice * 8 + 3, voice * 8 + 4, voice * 8 + 5, voice * 8 + 6]
        if all(reg in values for reg in regs):
            result.append({"voice": voice, **{
                name: f"0x{values[reg]:04x}" for name, reg in zip(names, regs)}})
    return result


def require_writer(rows: list[dict[str, str]], frame: int, address: str,
                   pc: str, data: str) -> None:
    require(any(int(row["frame"]) == frame and row["address"] == address and
                row["pc"] == pc and row["data"] == data for row in rows),
            f"missing controller write {frame}/{address}/{pc}/{data}")


def validate_report(report: dict[str, object]) -> None:
    """Validate the derived contract, including implementation-negative controls."""
    require(report["schema"] == 1, "unsupported ORACLE-06 schema")
    require(report["task"] == "ORACLE-06-ROUND1-ENCOUNTER-RULES", "task drift")
    require(report["classification"] ==
            "MEASURED_SOURCE_SET_PIECE_WITH_ADAPTED_SINGLE_ALIEN_CLEAR",
            "classification drift")
    source = report["source_set_piece"]
    require(source["clear_finding"]["classification"] ==
            "WITHDRAWAL_NOT_ENCOUNTER_CLEAR", "source withdrawal promoted to clear")
    require(source["clear_finding"]["living_enemies_at_transition"] == 6,
            "source transition no longer proves living enemies")
    contract = report["adapted_first_live_contract"]
    spawn = contract["spawn"]
    require(spawn["count"] == 1 and spawn["class"] == "0x1f" and
            spawn["type"] == 12 and spawn["slot"] == "0xffa000" and
            spawn["health"] == 87, "incorrect adapted spawn")
    clear = contract["clear"]
    require(clear["authority"] == "target_actor_ko_then_inactive",
            "timer-only or presentation-owned clear is forbidden")
    require(clear["timer_can_clear"] is False and
            clear["presentation_flag_can_clear"] is False,
            "non-gameplay state can clear the encounter")
    unlock = contract["camera_unlock"]
    require(unlock["required"] is True and
            unlock["after_clear_only"] is True,
            "missing or premature camera unlock")
    continuation = contract["continuation"]
    require(continuation["required"] is True and
            continuation["movement_after_unlock_required"] is True,
            "missing route continuation")
    ownership = report["ownership_separation"]
    require(ownership["encounter_controller"]["owns_clear"] is True and
            ownership["street_alien_actor"]["owns_ko_and_inactive"] is True and
            ownership["presentation"]["owns_clear"] is False,
            "controller/actor/presentation ownership collapsed")


def mutation_self_test(report: dict[str, object]) -> None:
    mutations = []
    timer = copy.deepcopy(report)
    timer["adapted_first_live_contract"]["clear"]["authority"] = "timer"
    mutations.append(timer)
    presentation = copy.deepcopy(report)
    presentation["adapted_first_live_contract"]["clear"]["authority"] = "presentation"
    mutations.append(presentation)
    spawn = copy.deepcopy(report)
    spawn["adapted_first_live_contract"]["spawn"]["count"] = 10
    mutations.append(spawn)
    unlock = copy.deepcopy(report)
    unlock["adapted_first_live_contract"]["camera_unlock"]["required"] = False
    mutations.append(unlock)
    continuation = copy.deepcopy(report)
    continuation["adapted_first_live_contract"]["continuation"]["required"] = False
    mutations.append(continuation)
    for mutant in mutations:
        try:
            validate_report(mutant)
        except AssertionError:
            continue
        raise AssertionError("ORACLE-06 negative-control mutation was accepted")


def build_report() -> dict[str, object]:
    manifest = json.loads((RAW / "input_manifest.json").read_text(encoding="utf-8-sig"))
    require(manifest["schema"] == 1 and manifest["frame_window"] == [2200, 7200],
            "capture manifest schema/window drift")
    require(manifest["mame"] == {
        "version": "0.289 (mame0289)",
        "sha256": "af6966108d9b52c22465c6d50f4e5d50cc371b50f2d27dc443935f287aad37a3",
    }, "MAME identity drift")
    require(manifest["nvram_baseline_sha256"] ==
            "35720ff0054bb7ba233da6d00ccbe92473c8a87e2c53c134c83ac2721f7d0ebf",
            "NVRAM baseline drift")
    require([item["name"] for item in manifest["variants"]] == VARIANTS,
            "variant inventory drift")
    require([item["mode"] for item in manifest["variants"]] ==
            ["baseline", "baseline", "entry_hold", "clear_attack_suppression"],
            "variant mode drift")
    for item in manifest["variants"]:
        for filename in FILES:
            require(item["sha256"][filename] == digest(RAW / item["name"] / filename),
                    f"{item['name']} {filename} manifest drift")
    for filename in FILES:
        require(digest(RAW / "cold_run_1" / filename) ==
                digest(RAW / "cold_run_2" / filename),
                f"cold capture nondeterminism: {filename}")

    traces = {name: load_samples(name) for name in VARIANTS}
    base, entry, suppress = (traces["cold_run_1"], traces["entry_hold"],
                             traces["clear_attack_suppression"])
    sample_fields = [key for key in base[FIRST_FRAME]
                     if key not in {"input_word", "in2_raw"}]
    actor_rows = read_tsv(RAW / "cold_run_1" / "actors.tsv")
    require(len(actor_rows) == (LAST_FRAME - FIRST_FRAME + 1) * 20,
            "actor ledger row count drift")
    writes = read_tsv(RAW / "cold_run_1" / "controller_writes.tsv")
    qsound = read_tsv(RAW / "cold_run_1" / "qsound.tsv")

    require((base[2405]["input_word"], base[2406]["in2_raw"],
             base[2407]["g801b"], base[2407]["g801d"]) == (2, 0xFEFF, 8, 8),
            "real Start route signature drift")
    require(base[3439]["p_active"] == 1 and base[3438]["p_active"] == 0,
            "player activation frame drift")
    require(base[3574]["class1f_active"] == 10 and
            base[3573]["class1f_active"] == 0, "initial spawn frame drift")
    spawn_rows = [row for row in actor_rows if int(row["frame"]) == 3574 and
                  int(row["active"]) and int(row["class"]) == 0x1F]
    spawn_positions = [{
        "slot": "0x" + row["address"], "pool_index": int(row["pool_index"]),
        "class": "0x1f", "type": int(row["type"]),
        "state": int(row["state"]), "action": f"0x{int(row['action']):04x}",
        "x": int(row["x"]), "z": int(row["z"]), "health": int(row["health"]),
    } for row in spawn_rows]
    require(len(spawn_positions) == 10 and
            all(row["type"] == 12 and row["health"] == 87 for row in spawn_positions),
            "initial class-0x1f spawn composition drift")

    exact_run(base, "scroll2_x", 576, 3575, 3717)
    exact_run(base, "scroll2_x", 768, 3821, 4994)
    exact_run(base, "scroll2_x", 944, 5071, 6768)
    require((base[3714]["g8009"], base[3715]["g8009"]) == (2, 4),
            "street active state transition drift")
    require_writer(writes, 3714, "ff8008", "00c170", "0004")
    require_writer(writes, 6766, "ff81f2", "028bc0", "0101")
    require_writer(writes, 6767, "ff8008", "008418", "0006")
    require_writer(writes, 6929, "ff8008", "0083d4", "0002")
    require_writer(writes, 7087, "ff8008", "00c200", "0004")
    require((base[6767]["g81f3"], base[6768]["g8009"],
             base[6768]["class1f_living"]) == (1, 6, 6),
            "withdrawal-with-living-enemies proof drift")
    require(base[6918]["class1f_active"] == 6 and
            base[6919]["class1f_active"] == 0, "presentation removal frame drift")
    require((base[6930]["g8009"], base[6935]["g801b"],
             base[6935]["g801d"], base[7088]["g8009"]) == (2, 44, 44, 4),
            "warehouse continuation drift")

    entry_input_diffs = [frame for frame in base
                         if base[frame]["input_word"] != entry[frame]["input_word"]]
    require(entry_input_diffs == list(range(3700, 3901)), "entry control drift")
    require(first_diff(base, entry, sample_fields) == 3715 and
            entry[3740]["g8009"] == 2 and entry[3741]["g8009"] == 4,
            "entry perturbation does not delay active state")
    exact_run(entry, "scroll2_x", 768, 4011, 5020)
    suppress_diffs = [frame for frame in base
                      if base[frame]["input_word"] != suppress[frame]["input_word"]]
    require(len(suppress_diffs) == 256 and suppress_diffs[0] == 3825 and
            suppress_diffs[-1] == 5180, "attack-suppression input drift")
    require(first_diff(base, suppress, sample_fields) == 3827,
            "attack-suppression downstream response drift")
    exact_run(suppress, "scroll2_x", 768, 3821, 4994)
    require(base[4994]["class1f_living"] == 7 and
            suppress[4994]["class1f_living"] == 8 and
            base[4995]["scroll2_x"] == suppress[4995]["scroll2_x"] == 779,
            "source camera release no longer disproves kill ownership")

    starts = completed_voice_starts(qsound, 3574)
    require([item["voice"] for item in starts] == [2, 3, 4, 5, 6, 7, 8],
            "entry QSound start batch drift")
    expected_witnesses = {
        "entry_title": (3574, "e9486ac7926450d9b40c43404258c1b223315dc3e38b56b876721f4b69ca6efc"),
        "camera_lock": (4994, "c096cbd1bd1d495eb2dfb3704ae9dfa761c92c0bb3021bff519e5f1d823b9015"),
        "withdrawal": (6768, "23780d2ac324a509578c912960b9d2fac6494f5d064c6b7679952113ef9a731a"),
        "continuation": (7088, "6d2df8ba15a7136c9b867a0d13ae8cd2caa7e710f7b121dc2756c853b3126106"),
    }
    witnesses = {}
    for name, (frame, expected) in expected_witnesses.items():
        filename = f"{frame:05d}.png"
        path = RAW / "cold_run_1" / "frames" / filename
        twin = RAW / "cold_run_2" / "frames" / filename
        require(digest(path) == expected and digest(twin) == expected,
                f"visual witness drift: {name}")
        witnesses[name] = {"frame": frame, "sha256": expected}

    oracle05 = json.loads(ORACLE05.read_text(encoding="utf-8"))
    target = oracle05["observed_loop"]
    require(target["slot"] == "0xffa000" and target["class"] == "0x1f" and
            target["type"] == 12 and target["spawn_init"]["health"] == 87,
            "ORACLE-05 target contract drift")
    ko = target["hit_recovery_ko_removal"]

    report: dict[str, object] = {
        "schema": 1,
        "task": "ORACLE-06-ROUND1-ENCOUNTER-RULES",
        "classification": "MEASURED_SOURCE_SET_PIECE_WITH_ADAPTED_SINGLE_ALIEN_CLEAR",
        "target": {"set": "avspu", "revision": "USA 940520"},
        "scope": "one bounded Round 1 street set piece and the minimum adapted first-live encounter contract; not later Round 1 or a generic encounter engine",
        "physical_saturn": "UNRUN",
        "provenance": {
            "mame": manifest["mame"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "rom_sha256": {item["name"]: item["sha256"] for item in manifest["roms"]},
            "cold_run": {filename: digest(RAW / "cold_run_1" / filename)
                         for filename in FILES},
            "oracle04_sha256": digest(ORACLE04),
            "oracle05_sha256": digest(ORACLE05),
        },
        "determinism": {
            "cold_runs_byte_identical": True,
            "identical_artifacts": FILES,
            "sample_frames_each": LAST_FRAME - FIRST_FRAME + 1,
            "actor_rows_each": (LAST_FRAME - FIRST_FRAME + 1) * 20,
        },
        "start_and_player_route": {
            "start_input_frames": [2405, 2407], "start_port_low_frame": 2406,
            "start_port_value": "0xfeff", "joined_route_state_frame": 2407,
            "player_active_frame": 3439,
            "finding": "a real credited Start creates an input-responsive P1 actor; the source opening retains its DEMONSTRATION presentation label and ends as a withdrawal set piece",
        },
        "static_binding": validate_static_image(),
        "source_set_piece": {
            "entry": {
                "preload_state": {"frame": 3469, "g8009": 2},
                "first_class_0x1f_spawn_frame": 3574,
                "initial_spawns": spawn_positions,
                "active_state": {"frame": 3715, "g8009": 4,
                                 "write_frame": 3714, "write_pc": "0x00c170"},
                "entry_qsound_start_batch": {"frame": 3574, "semantic_name": None,
                                               "complete_voice_starts": starts},
            },
            "camera": {
                "scroll2_x_locks": [
                    {"value": 576, "first_frame": 3575, "last_frame": 3717},
                    {"value": 768, "first_frame": 3821, "last_frame": 4994,
                     "player_right_clamp_x": 1184},
                    {"value": 944, "first_frame": 5071, "last_frame": 6768,
                     "player_right_clamp_x": 1360},
                ],
                "observed_right_edge_offset": 416,
            },
            "clear_finding": {
                "classification": "WITHDRAWAL_NOT_ENCOUNTER_CLEAR",
                "presentation_preflag": {"field": "g8249", "frame": 6467},
                "withdrawal_flag": {"field": "g81f3", "frame": 6767,
                                    "writer_pc": "0x028bc0"},
                "controller_state": {"field": "g8009", "frame": 6768,
                                     "value": 6, "writer_pc": "0x008418"},
                "living_enemies_at_transition": 6,
                "presentation_removal_frame": 6919,
                "finding": "the source unlock/route transition occurs with living class-0x1F actors and removes them during presentation transition; it cannot authorize a live kill gate",
            },
            "continuation": {
                "next_preload_frame": 6930, "next_segment_index_frame": 6935,
                "next_segment_index": 44, "next_active_frame": 7088,
                "next_active_write_pc": "0x00c200", "segment": "warehouse",
            },
            "visual_witnesses": witnesses,
        },
        "counterfactuals": {
            "entry_hold": {
                "suppressed_right_frames": [3700, 3900],
                "first_controller_difference": 3715,
                "active_state_baseline_frame": 3715,
                "active_state_mutant_frame": 3741,
                "second_lock_baseline_frame": 3821,
                "second_lock_mutant_frame": 4011,
                "finding": "forward movement participates in source entry/lock progression",
            },
            "clear_attack_suppression": {
                "input_window": [3800, 5200], "differing_input_frame_count": 256,
                "first_differing_input_frame": 3825,
                "first_actor_semantic_difference": 3846,
                "camera_unlock_frame_baseline": 4995,
                "camera_unlock_frame_mutant": 4995,
                "living_at_last_locked_frame_baseline": 7,
                "living_at_last_locked_frame_mutant": 8,
                "finding": "attack suppression changes actor outcomes but not the first source camera unlock; that unlock is not a kill-gated clear",
            },
        },
        "ownership_separation": {
            "encounter_controller": {
                "fields": ["g8009", "camera_lock", "camera_unlock", "continuation"],
                "owns_clear": True,
                "rule": "consume actor KO/inactive state; never timer or presentation state",
            },
            "street_alien_actor": {
                "source": "ORACLE-05-STREET-ALIEN-AI", "slot": "0xffa000",
                "owns_ko_and_inactive": True,
            },
            "presentation": {
                "fields": ["g81f3", "g8249", "QSound", "segment visuals"],
                "owns_clear": False, "owns_route_progression": False,
            },
        },
        "adapted_first_live_contract": {
            "fidelity": "SOURCE_BOUND_WITH_ADAPTED_SINGLE_ALIEN_CLEAR",
            "entry": {
                "authority": "player_crosses_measured_entry_threshold",
                "source_evidence": "entry_hold delays active state and second lock",
            },
            "spawn": {
                "count": 1, "slot": "0xffa000", "class": "0x1f", "type": 12,
                "health": 87, "position": {"x": 960, "y": 343, "z": 343},
                "source": "ORACLE-05 measured target spawn; one actor is an adapted reduction of the source set piece",
            },
            "active": {"authority": "encounter_controller", "requires_target_active": True},
            "clear": {
                "authority": "target_actor_ko_then_inactive",
                "ko_frame_in_oracle05": ko["ko_state_frame"],
                "inactive_frame_in_oracle05": ko["inactive_frame"],
                "timer_can_clear": False, "presentation_flag_can_clear": False,
            },
            "camera_lock": {"source_scroll2_x": 768, "right_edge_offset": 416},
            "camera_unlock": {"required": True, "after_clear_only": True},
            "continuation": {"required": True,
                             "movement_after_unlock_required": True},
        },
        "negative_control_contract": {
            "reject_timer_only_clear": True,
            "reject_presentation_owned_clear": True,
            "reject_incorrect_spawn": True,
            "reject_missing_camera_unlock": True,
            "reject_missing_continuation": True,
        },
        "bounded_unknowns": [
            "the semantic name of the frame-3574 QSound batch",
            "a source-native kill-gated clear in the opening street set piece",
            "later Round 1 encounter and boss rules",
            "multiplayer encounter scaling",
            "physical Saturn behavior",
        ],
    }
    validate_report(report)
    mutation_self_test(report)
    return report


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"ORACLE-06 PASS {OUT.relative_to(ROOT)} sha256={digest(OUT)}")


if __name__ == "__main__":
    main()
