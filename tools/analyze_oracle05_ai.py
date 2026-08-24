#!/usr/bin/env python3
"""Validate ORACLE-05 private traces and emit a source-only AI report."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle05_street_alien_ai"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
CONTACT = ROOT / "data" / "enemy_contact_capture.json"
HIT_KO = ROOT / "data" / "avsp_hit_ko_writer_set.json"
CLASS_TABLE = ROOT / "data" / "avsp_actor_class_table.json"
SUBSTATES = ROOT / "data" / "avsp_substate_dispatchers.json"
OUT = ROOT / "data" / "oracle05_street_alien_ai.json"
VARIANTS = [
    "cold_run_1", "cold_run_2", "distance_far", "lane_far",
    "attack_timing", "enemy_health", "ai_timer", "rng_state",
]
NUMERIC_HEX = {"p_anim", "e_anim", "rng_word"}
TARGET = "ffa000"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("ascii")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_samples(name: str) -> list[dict[str, int]]:
    rows = []
    for raw in read_tsv(RAW / name / "samples.tsv"):
        row = {key: (int(value, 16) if key in NUMERIC_HEX else int(value))
               for key, value in raw.items() if key != "variant"}
        rows.append(row)
    if len(rows) != 3101 or [row["frame"] for row in rows] != list(range(2400, 5501)):
        raise ValueError(f"{name}: sample window is not contiguous 2400..5500")
    return rows


def indexed(rows: list[dict[str, int]]) -> dict[int, dict[str, int]]:
    return {row["frame"]: row for row in rows}


def first_diff(base: dict[int, dict[str, int]], other: dict[int, dict[str, int]],
               fields: tuple[str, ...], start: int = 2400) -> int | None:
    return next((frame for frame in range(start, 5501)
                 if any(base[frame][field] != other[frame][field]
                        for field in fields)), None)


def rng_next(seed: int) -> int:
    mixed_high = ((seed * 3) & 0xffff) >> 8
    mixed_low = ((seed & 0xff) + mixed_high) & 0xff
    return (mixed_high << 8) | mixed_low


def validate_rng_trace(rows: list[dict[str, str]]) -> int:
    # The rng_state variant contains one declared research-only state write
    # from the Lua callback. Exclude that control write from routine triples.
    rows = [row for row in rows if row["kind"] == "entry" or
            row["pc"] in ("017c70", "017c72")]
    if len(rows) % 3:
        raise ValueError("RNG trace is not entry/write/write triples")
    for offset in range(0, len(rows), 3):
        entry, low, high = rows[offset:offset + 3]
        if [entry["kind"], low["kind"], high["kind"]] != ["entry", "write", "write"]:
            raise ValueError("RNG trace ordering drift")
        if not (entry["frame"] == low["frame"] == high["frame"] and
                entry["a6"] == low["a6"] == high["a6"]):
            raise ValueError("RNG call attribution drift")
        seed = int(entry["seed"], 16)
        result = rng_next(seed)
        if (low["mask"], high["mask"]) != ("00ff", "ff00"):
            raise ValueError("RNG write-mask drift")
        if int(low["data"], 16) & 0xff != result & 0xff:
            raise ValueError("RNG low-byte recurrence drift")
        if int(high["data"], 16) & 0xff != result >> 8:
            raise ValueError("RNG high-byte recurrence drift")
        if int(high["seed"], 16) != ((seed & 0xff00) | (result & 0xff)):
            raise ValueError("RNG intermediate state drift")
    return len(rows) // 3


def target_rng(rows: list[dict[str, str]], minimum_frame: int = 3900) -> list[dict[str, object]]:
    result = []
    for row in rows:
        if row["kind"] != "entry" or row["a6"] != TARGET or int(row["frame"]) < minimum_frame:
            continue
        seed = int(row["seed"], 16)
        result.append({
            "frame": int(row["frame"]), "return_pc": "0x" + row["pc"],
            "seed_before": f"0x{seed:04x}", "seed_after": f"0x{rng_next(seed):04x}",
        })
    return result


def validate_scheduler(samples: list[dict[str, int]], scheduler: list[dict[str, str]],
                       classes: list[dict[str, str]]) -> dict[str, object]:
    by_frame: dict[int, list[dict[str, str]]] = {}
    for row in scheduler:
        by_frame.setdefault(int(row["frame"]), []).append(row)
    expected_fetch = [f"{0xff9580 + index * 0xc0:06x}" for index in range(21)]
    expected_d7 = ["0013", "0013"] + [f"{value:04x}" for value in range(0x12, -1, -1)]
    if sorted(by_frame) != list(range(2400, 5500)):
        raise ValueError("scheduler frame window drift")
    for rows in by_frame.values():
        if [row["slot"] for row in rows] != expected_fetch:
            raise ValueError("scheduler actor order drift")
        if [row["d7"] for row in rows] != expected_d7:
            raise ValueError("scheduler DBRA/prefetch signature drift")

    sample_map = indexed(samples)
    target_entries = {(int(row["frame"]), row["slot"]) for row in classes}
    for frame in range(2400, 5500):
        expected = (sample_map[frame]["e_active"] != 0 or
                    (sample_map[frame]["e_active"] == 0 and
                     sample_map[frame + 1]["e_active"] == 1 and
                     sample_map[frame + 1]["e_state"] == 2))
        if ((frame, TARGET) in target_entries) != expected:
            raise ValueError("class-entry tap does not match target liveness")
    return {
        "routine": "0x01b974",
        "loop_fetch_pc": "0x01b986",
        "pool_first": "0xff9580",
        "pool_last_executed": "0xffa3c0",
        "actor_stride_bytes": 192,
        "executed_slot_count": 20,
        "target_slot": "0xffa000",
        "target_zero_based_pool_index": 14,
        "loop_head_fetch_rows_per_frame": 21,
        "terminal_not_executed_prefetch": "0xffa480",
        "target_class_entry_pc": "0x060532",
        "target_class_entry_count": sum(row["slot"] == TARGET for row in classes),
        "interpretation": "20 ordered actor updates; the 21st loop-head opcode fetch is the not-executed terminal prefetch and is excluded",
    }


def validate_static_image() -> dict[str, object]:
    image = OPCODES.read_bytes()
    if len(image) != 0x200000 or digest(OPCODES) != "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501":
        raise ValueError("decrypted opcode image identity drift")
    signatures = {
        0x01b974: "303c0045720b4eb9000011ea7e134ded1580",
        0x017020: "74ff760241ed038038484a10672430280010",
        0x017c5e: "302d01a83200d040d041e048d12d01a91b4001a8102d01a9",
        0x060532: "102e0004323b00064efb10020008021c0c080c0e",
        0x060546: "70007c0f41ee008020c051cefffc542e00043d7c8000002e",
        0x06075a: "102e0005323b00064efb1002000c08f409ce09ce09",
        0x060d0c: "4eb900017c5e0240000f1d7b0024002a0c2e000200a6",
    }
    for address, expected in signatures.items():
        actual = image[address:address + len(expected) // 2].hex()
        if actual != expected:
            raise ValueError(f"opcode signature drift at 0x{address:06x}")
    return {
        "opcode_image_sha256": digest(OPCODES),
        "class_dispatch": "0x060532",
        "class_state0_init": "0x060546",
        "nested_state_dispatch": "0x06075a",
        "class_table_set": "0x00130ac8",
        "one_player_target_routine": "0x017020",
        "target_candidates": ["0xff8380", "0xff8480", "0xff8580"],
        "target_metric": "abs(dx) + 2*abs(dz); active minimum; later player wins a tie",
        "target_pointer_field": "actor+0x28 low word",
        "rng_routine": "0x017c5e",
        "rng_state": "0xff81a8..0xff81a9",
        "rng_recurrence": "high=((3*seed)&0xffff)>>8; low=(old_low+high)&0xff; seed=(high<<8)|low",
        "rng_return": "new low byte",
    }


def assert_loop(base: dict[int, dict[str, int]], contact: dict) -> dict[str, object]:
    exact = {
        3983: (1, 2, 0, 0, 87),
        3984: (1, 2, 0, 5632, 87),
        4214: (1, 2, 0, 5632, 87),
        4253: (1, 2, 0, 6144, 87),
        4373: (1, 2, 0, 0, 87),
        4374: (1, 2, 0, 5632, 87),
        5190: (1, 2, 2, 0, 63),
        5329: (1, 4, 0, 0, -1),
        5330: (2, 4, 2, 0, -1),
        5469: (2, 6, 0, 0, -1),
        5470: (0, 0, 0, 0, -1),
    }
    for frame, values in exact.items():
        got = tuple(base[frame][key] for key in
                    ("e_active", "e_state", "e_inner", "e_action", "e_health"))
        if got != values:
            raise ValueError(f"target loop drift at frame {frame}")
    if any(base[frame]["e_target_slot"] != 0x8380
           for frame in range(3983, 5470) if base[frame]["e_active"]):
        raise ValueError("one-player target binding drift")
    if [(event["frame"], event["from"], event["to"])
            for event in contact["player_health_events"][:3]] != [
                (4243, 30, 22), (4301, 22, 14), (4372, 14, 6)]:
        raise ValueError("enemy contact sequence drift")
    return {
        "slot": "0xffa000", "class": "0x1f", "type": 12,
        "spawn_init": {
            "rng_call_frame": 3982, "active_frame": 3983,
            "state": 2, "health": 87, "position": {"x": 960, "y": 343, "z": 343},
            "facing": 1, "first_action_frame": 3984, "first_action": "0x1600",
        },
        "targeting": {"stored_target": "0xff8380", "status": "MEASURED_ONE_PLAYER"},
        "approach_and_lane_motion": {
            "action": "0x1600", "start_frame": 4214, "end_frame": 4252,
            "from": {"x": 1181, "z": 297}, "to": {"x": 1292, "z": 274},
            "x_displacement": 111, "z_displacement": -23, "facing": 1,
            "scope": "observed source motion; target-relative lane steering outside this route is not generalized",
        },
        "attack": {
            "selection_rng_frame": 4252, "action": "0x1800",
            "start_frame": 4253, "timer_initial": 120, "timer_last_nonzero_frame": 4372,
            "contact_frames": [4301, 4372], "contact_offsets": [48, 119],
            "damage_each_native_units": 8, "player_health": [22, 14, 6],
            "recovery_clear_frame": 4373, "next_approach_frame": 4374,
            "cooldown_representation": "the measured action timer includes startup/contact/recovery; no separate post-action cooldown state appears before reselection",
        },
        "hit_recovery_ko_removal": {
            "hit_frames": [5190, 5236, 5283, 5329],
            "health_sequence": [87, 63, 39, 8, -1],
            "nonlethal_recovery_frames": [5227, 5277, 5322],
            "ko_state_frame": 5329, "death_active_frame": 5330,
            "death_timer_phase_frame": 5409, "remove_state_frame": 5469,
            "inactive_frame": 5470,
        },
    }


def build_report() -> dict:
    manifest = json.loads((RAW / "input_manifest.json").read_text(encoding="utf-8-sig"))
    if [item["name"] for item in manifest["variants"]] != VARIANTS:
        raise ValueError("ORACLE-05 variant inventory drift")
    for item in manifest["variants"]:
        run = RAW / item["name"]
        for field, filename in (("samples_sha256", "samples.tsv"),
                                ("rng_calls_sha256", "rng_calls.tsv"),
                                ("scheduler_sha256", "scheduler.tsv"),
                                ("class_entries_sha256", "class_entries.tsv")):
            if item[field] != digest(run / filename):
                raise ValueError(f"{item['name']}: manifest {field} drift")

    loaded = {name: load_samples(name) for name in VARIANTS}
    maps = {name: indexed(rows) for name, rows in loaded.items()}
    raw_rng = {name: read_tsv(RAW / name / "rng_calls.tsv") for name in VARIANTS}
    rng_counts = {name: validate_rng_trace(rows) for name, rows in raw_rng.items()}
    if any(count <= 0 for count in rng_counts.values()):
        raise ValueError("missing consumed RNG evidence")

    identical_files = ["samples.tsv", "rng_calls.tsv", "scheduler.tsv", "class_entries.tsv"]
    if any(digest(RAW / "cold_run_1" / name) != digest(RAW / "cold_run_2" / name)
           for name in identical_files):
        raise ValueError("ORACLE-05 cold captures are not byte-identical")

    base = maps["cold_run_1"]
    scheduler = validate_scheduler(
        loaded["cold_run_1"], read_tsv(RAW / "cold_run_1" / "scheduler.tsv"),
        read_tsv(RAW / "cold_run_1" / "class_entries.tsv"))
    static = validate_static_image()
    contact = json.loads(CONTACT.read_text(encoding="utf-8"))
    loop = assert_loop(base, contact)

    target_base_rng = target_rng(raw_rng["cold_run_1"])
    target_mutant_rng = target_rng(raw_rng["rng_state"])
    selection = next(item for item in target_base_rng if item["frame"] == 4252)
    selection_mutant = next(item for item in target_mutant_rng if item["frame"] == 4252)
    if selection != {"frame": 4252, "return_pc": "0x060d12",
                     "seed_before": "0x7301", "seed_after": "0x595a"}:
        raise ValueError("baseline target RNG selection drift")
    if selection_mutant["seed_before"] != "0x0001" or selection_mutant["seed_after"] != "0x0001":
        raise ValueError("RNG fixed-point control drift")

    enemy_fields = ("e_active", "e_state", "e_inner", "e_action", "e_phase",
                    "e_facing", "e_x", "e_y", "e_z", "e_ai_timer", "e_health", "e_hit")
    player_fields = ("p_action", "p_x", "p_y", "p_z", "p_health", "p_hit")
    distance, lane, timing = maps["distance_far"], maps["lane_far"], maps["attack_timing"]
    health, timer, rng = maps["enemy_health"], maps["ai_timer"], maps["rng_state"]
    if any(any(base[f][key] != distance[f][key] for key in enemy_fields)
           for f in range(4435, 4609)):
        raise ValueError("distance control changed committed target action window")
    if any(any(base[f][key] != lane[f][key] for key in enemy_fields)
           for f in range(4435, 4609)):
        raise ValueError("lane control changed committed target action window")
    differing_inputs = [f for f in range(2400, 5501)
                        if base[f]["input_word"] != timing[f]["input_word"]]
    if differing_inputs != list(range(4420, 4425)):
        raise ValueError("attack-timing input control drift")
    if (health[5184]["e_health"], health[5190]["e_health"], health[5190]["e_state"],
            health[5327]["e_active"]) != (15, -1, 4, 0):
        raise ValueError("enemy-health counterfactual drift")
    if (timer[4254]["e_ai_timer"], timer[4257]["e_action"], timer[4258]["e_action"],
            timer[4297]["e_inner"]) != (3, 0, 5632, 8):
        raise ValueError("AI-timer counterfactual drift")
    if (rng[4252]["rng_word"], rng[4253]["e_ai_timer"], rng[4283]["e_action"]) != (1, 30, 0):
        raise ValueError("consumed-RNG counterfactual drift")

    report = {
        "schema": 1,
        "task": "ORACLE-05-STREET-ALIEN-AI",
        "classification": "MEASURED_MAME_EXECUTION_WITH_STATIC_ROUTINE_BINDING",
        "target": {"set": "avspu", "revision": "USA 940520"},
        "scope": "one class-0x1F slot on the deterministic first-live-encounter route; not a generic AI or archetype model",
        "provenance": {
            "mame": manifest["mame"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "rom_sha256": {item["name"]: item["sha256"] for item in manifest["roms"]},
            "cold_run": {name.replace("_sha256", ""): digest(RAW / "cold_run_1" / filename)
                         for name, filename in (("samples_sha256", "samples.tsv"),
                                                ("rng_calls_sha256", "rng_calls.tsv"),
                                                ("scheduler_sha256", "scheduler.tsv"),
                                                ("class_entries_sha256", "class_entries.tsv"))},
            "enemy_contact_capture_sha256": digest(CONTACT),
            "hit_ko_writer_set_sha256": digest(HIT_KO),
            "actor_class_table_sha256": digest(CLASS_TABLE),
            "substate_dispatchers_sha256": digest(SUBSTATES),
        },
        "determinism": {
            "cold_runs_byte_identical": True,
            "identical_artifacts": identical_files,
            "sample_frames_each": 3101,
            "rng_calls_each": rng_counts["cold_run_1"],
            "scheduler_frames_each": 3100,
        },
        "static_binding": static,
        "scheduler": scheduler,
        "observed_loop": loop,
        "rng_consumption": {
            "global_calls_in_baseline_window": rng_counts["cold_run_1"],
            "target_calls_from_frame_3900": target_base_rng,
            "attack_selection": selection,
            "attack_result": {"action": "0x1800", "timer": 120},
            "fixed_point_control": {
                "forced_seed_frame": 4252, "seed": "0x0001",
                "selection": selection_mutant,
                "result_action": "0x1800", "result_timer": 30,
                "first_action_end_frame": 4283,
            },
        },
        "counterfactuals": {
            "distance": {
                "write_frames": [4435, 4608], "player_x": 1792,
                "spans_target_spawn_frame": 4447,
                "target_fields_identical_during_write_window": True,
                "first_rng_state_difference": first_diff(base, distance, ("rng_word",), 4435),
                "first_target_difference": first_diff(base, distance, enemy_fields, 4435),
                "finding": "the already selected spawn/approach/attack schedule is invariant in this window; later shared-route RNG divergence is retained, not generalized",
            },
            "lane": {
                "write_frames": [4435, 4608], "player_z": 400,
                "spans_target_spawn_frame": 4447,
                "target_fields_identical_during_write_window": True,
                "first_rng_state_difference": first_diff(base, lane, ("rng_word",), 4435),
                "first_target_difference": first_diff(base, lane, enemy_fields, 4435),
                "finding": "the first target action is not reselected from this lane displacement; later divergence follows shared-route RNG",
            },
            "player_attack_timing": {
                "suppressed_input_frames": differing_inputs,
                "first_player_difference": first_diff(base, timing, player_fields, 4420),
                "first_rng_state_difference": first_diff(base, timing, ("rng_word",), 4420),
                "first_target_difference": first_diff(base, timing, enemy_fields, 4420),
                "baseline_target_timer_at_4487": base[4487]["e_ai_timer"],
                "mutant_target_timer_at_4487": timing[4487]["e_ai_timer"],
            },
            "enemy_health": {
                "write_frame": 5184, "forced_health": 15,
                "first_hit_frame": 5190, "health_after": -1, "ko_state": 4,
                "inactive_frame": 5327, "baseline_inactive_frame": 5470,
            },
            "ai_timer": {
                "write_frame": 4254, "forced_timer": 3,
                "attack_clear_frame": 4257, "next_approach_frame": 4258,
                "first_reposition_state_frame": 4297, "reposition_inner_state": 8,
                "baseline_attack_clear_frame": 4373,
            },
            "consumed_rng": {
                "write_frame": 4252, "forced_seed": "0x0001",
                "baseline_timer": 120, "mutant_timer": 30,
                "baseline_attack_clear_frame": 4373, "mutant_attack_clear_frame": 4283,
            },
        },
        "visual_witness_sha256": {
            f"frame_{frame}": digest(RAW / "cold_run_1" / f"{frame:05d}.png")
            for frame in (2400, 4214, 4253, 4301, 4372, 5190, 5330, 5470)
        },
        "bounded_findings": {
            "spawn_init_target_approach_facing": "MEASURED",
            "observed_lane_axis_motion": "MEASURED_ROUTE_ONLY",
            "target_relative_lane_reselection": "NOT_OBSERVED_IN_CONTROL_WINDOW",
            "attack_selection_timer_contacts_damage": "MEASURED",
            "hit_recovery_ko_removal": "MEASURED",
            "repositioning": "MEASURED_BY_TIMER_COUNTERFACTUAL",
            "scheduler_order": "MEASURED_AND_STATIC_BOUND",
            "consumed_rng_state_and_recurrence": "MEASURED_AND_STATIC_BOUND",
            "other_enemy_archetypes": "UNKNOWN_OUT_OF_SCOPE",
            "multiplayer_targeting": "STATIC_ALGORITHM_ONLY_UNRUN",
        },
        "evidence_tier": "MAME_TRACE_COUNTERFACTUAL_AND_DECRYPTED_OPCODE_BINDING",
        "saturn_emulator": "UNRUN",
        "physical_saturn": "UNRUN",
    }
    return report


def validate(report: dict) -> None:
    if report["classification"] != "MEASURED_MAME_EXECUTION_WITH_STATIC_ROUTINE_BINDING":
        raise ValueError("ORACLE-05 classification drift")
    if report["determinism"] != {
            "cold_runs_byte_identical": True,
            "identical_artifacts": ["samples.tsv", "rng_calls.tsv", "scheduler.tsv", "class_entries.tsv"],
            "sample_frames_each": 3101, "rng_calls_each": 1339,
            "scheduler_frames_each": 3100}:
        raise ValueError("ORACLE-05 deterministic repeat drift")
    if report["scheduler"]["executed_slot_count"] != 20:
        raise ValueError("ORACLE-05 scheduler count drift")
    if report["scheduler"]["target_zero_based_pool_index"] != 14:
        raise ValueError("ORACLE-05 target order drift")
    if report["observed_loop"]["attack"]["contact_frames"] != [4301, 4372]:
        raise ValueError("ORACLE-05 attack contacts drift")
    if report["observed_loop"]["hit_recovery_ko_removal"]["health_sequence"] != [87, 63, 39, 8, -1]:
        raise ValueError("ORACLE-05 HIT/KO sequence drift")
    rng = report["rng_consumption"]
    if rng["attack_selection"] != {"frame": 4252, "return_pc": "0x060d12",
                                    "seed_before": "0x7301", "seed_after": "0x595a"}:
        raise ValueError("ORACLE-05 RNG ownership drift")
    if rng["fixed_point_control"]["result_timer"] != 30:
        raise ValueError("ORACLE-05 RNG counterfactual drift")
    controls = report["counterfactuals"]
    if controls["player_attack_timing"]["suppressed_input_frames"] != list(range(4420, 4425)):
        raise ValueError("ORACLE-05 attack timing control drift")
    if controls["enemy_health"]["inactive_frame"] != 5327:
        raise ValueError("ORACLE-05 health control drift")
    if controls["ai_timer"]["attack_clear_frame"] != 4257:
        raise ValueError("ORACLE-05 timer control drift")
    if controls["consumed_rng"]["mutant_attack_clear_frame"] != 4283:
        raise ValueError("ORACLE-05 RNG action drift")
    if report["bounded_findings"]["target_relative_lane_reselection"] != "NOT_OBSERVED_IN_CONTROL_WINDOW":
        raise ValueError("ORACLE-05 lane result overclaim")
    if report["bounded_findings"]["multiplayer_targeting"] != "STATIC_ALGORITHM_ONLY_UNRUN":
        raise ValueError("ORACLE-05 multiplayer overclaim")
    if report["saturn_emulator"] != "UNRUN" or report["physical_saturn"] != "UNRUN":
        raise ValueError("ORACLE-05 overclaims Saturn evidence")
    for value in report["provenance"]["cold_run"].values():
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError("ORACLE-05 provenance hash drift")


def self_test(report: dict) -> None:
    mutations = []
    changed = copy.deepcopy(report)
    changed["scheduler"]["executed_slot_count"] = 21
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["rng_consumption"]["attack_selection"]["seed_after"] = "0x0001"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["counterfactuals"]["enemy_health"]["inactive_frame"] = 5470
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["bounded_findings"]["target_relative_lane_reselection"] = "MEASURED"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["physical_saturn"] = "PASS"
    mutations.append(changed)
    for index, mutation in enumerate(mutations):
        try:
            validate(mutation)
        except ValueError:
            continue
        raise ValueError(f"ORACLE-05 negative mutation {index} unexpectedly passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    report = build_report() if args.generate else json.loads(OUT.read_text(encoding="utf-8"))
    validate(report)
    self_test(report)
    if args.generate:
        OUT.write_bytes(canonical(report))
    print("ORACLE-05 class-0x1F street-alien AI evidence: PASS")
    print(f"samples={report['determinism']['sample_frames_each']} rng_calls={report['determinism']['rng_calls_each']}")
    print(f"samples_sha256={report['provenance']['cold_run']['samples']}")


if __name__ == "__main__":
    main()
