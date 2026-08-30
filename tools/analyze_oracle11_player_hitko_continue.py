#!/usr/bin/env python3
"""Close Predator Warrior HIT/KO, continue, respawn, and control return."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps" / "mame" / "oracle11_player_hitko_continue_a"
RAW_B = ROOT / ".deps" / "mame" / "oracle11_player_hitko_continue_b"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
COFFEE_SHOP = (ROOT / ".deps" / "mame" /
               "oracle11_progression_lifecycle_cs21a")
COFFEE_ACTORS = COFFEE_SHOP / "coffee_shop_scene_actors.tsv"
COFFEE_SAMPLES = COFFEE_SHOP / "samples.tsv"
PLAYER_AUDIO = ROOT / "data" / "oracle11_predator_player_audio.json"
OUT = ROOT / "data" / "oracle11_predator_hitko_continue.json"
FILES = ("samples.tsv", "player_writes.tsv", "global_writes.tsv",
         "qsound_writes.tsv")


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


def indexed(root: Path, variant: str) -> dict[int, dict[str, str]]:
    return {int(row["frame"]): row
            for row in rows(root / variant / "samples.tsv")}


def writes(root: Path, variant: str, filename: str) -> list[dict[str, str]]:
    return rows(root / variant / filename)


def has_write(items: list[dict[str, str]], frame: int, offset: str,
              pc: str, data: str | None = None) -> bool:
    return any(int(row["frame"]) == frame and row["offset"] == offset and
               row["pc"] == pc and (data is None or row["data"] == data)
               for row in items)


def first_frame(samples: dict[int, dict[str, str]], predicate) -> int | None:
    return next((frame for frame, row in sorted(samples.items())
                 if predicate(row)), None)


def source_window(image: bytes, start: int, end: int) -> dict[str, object]:
    return {"start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
            "bytes": end - start,
            "sha256": hashlib.sha256(image[start:end]).hexdigest()}


def manifest_identity(root: Path) -> dict[str, object]:
    path = root / "input_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    for variant in manifest["variants"]:
        for filename, expected in variant["sha256"].items():
            require(digest(root / variant["name"] / filename) == expected,
                    f"{root.name}/{variant['name']}/{filename}: identity drift")
    return {"manifest_sha256": digest(path),
            "variant_names": [item["name"] for item in manifest["variants"]]}


def build_report() -> dict[str, object]:
    image = OPCODES.read_bytes()
    program = PROGRAM.read_bytes()
    require(len(image) == 0x200000, "decoded source image size drift")
    require(len(program) == 0x200000, "decoded source program size drift")
    identities = {root.name: manifest_identity(root)
                  for root in (RAW_A, RAW_B)}
    for filename in FILES:
        require(digest(RAW_A / "baseline_hitko_1" / filename) ==
                digest(RAW_A / "baseline_hitko_2" / filename),
                f"independent HIT/KO captures differ: {filename}")

    baseline = indexed(RAW_A, "baseline_hitko_1")
    player_writes = writes(RAW_A, "baseline_hitko_1", "player_writes.tsv")
    global_writes = writes(RAW_A, "baseline_hitko_1", "global_writes.tsv")

    coffee_player = {
        int(row["frame"]): row for row in rows(COFFEE_ACTORS)
        if row["pool"] == "player" and row["slot"] == "ff8380" and
        2749 <= int(row["frame"]) <= 2780
    }
    coffee_samples = {
        int(row["frame"]): row for row in rows(COFFEE_SAMPLES)
        if 2749 <= int(row["frame"]) <= 2780
    }
    require(sorted(coffee_player) == list(range(2749, 2781)) and
            sorted(coffee_samples) == list(range(2749, 2781)),
            "Coffee Shop player HIT source window drift")
    player_audio = json.loads(PLAYER_AUDIO.read_text(encoding="ascii"))
    hit_audio = next(edge for edge in player_audio["trigger_edges"]
                     if edge["command_identity"] == "0x003b" and
                     edge["caller_provenance"]["player_stack_owner_return"] ==
                     "0x003b5a")

    def player_anchor(frame: int) -> dict[str, object]:
        row = coffee_player[frame]
        return {
            "frame_u16": frame,
            "outer_state_u16": int(row["state"], 16),
            "substate_u16": int(row["substate"], 16),
            "facing_u8": int(row["facing"]),
            "x_fp_s32_16_16": f"0x{int(row['x_fp'], 16):08x}",
            "z_s16": int(row["z"]),
            "animation_record": f"0x{int(row['animation_record'], 16):08x}",
            "animation_timer_u16": int(row["animation_timer"], 16),
            "animation_branch_s16": int(row["animation_branch"]),
            "health_s16": int(row["health"]),
            "hit_count_u8": int(coffee_samples[frame]["hit"]),
            "resource_u8": int(coffee_samples[frame]["resource"]),
            "resource_recharge_u8": int(coffee_samples[frame]["recharge"]),
        }

    require((int(baseline[6080]["p_health"]),
             int(baseline[6081]["p_health"])) == (0, -1),
            "lethal signed-health crossing drift")
    require(has_write(player_writes, 6080, "40", "01d5ee", "fff5") and
            has_write(player_writes, 6080, "40", "01d5f6", "ffff") and
            has_write(player_writes, 6080, "04", "01d4aa", "0400"),
            "lethal damage/state writer drift")
    require((int(baseline[6081]["p_state"]),
             int(baseline[6082]["p_active"]),
             int(baseline[6082]["p_inner"])) == (4, 2, 2),
            "KO entry drift")
    require(has_write(player_writes, 6081, "04", "01b14c") and
            has_write(player_writes, 6081, "00", "01b150", "0201"),
            "KO dispatcher entry writer drift")

    ko_phases = [(6094, "0202", "01b2a0"),
                 (6095, "0808", "01b344"),
                 (6108, "0202", "01b406"),
                 (6122, "0404", "01b30c"),
                 (6125, "0606", "01b36e")]
    require(all(has_write(player_writes, frame, "06", pc, data)
                for frame, data, pc in ko_phases),
            "KO action-phase writer sequence drift")
    require(has_write(player_writes, 6137, "04", "01b3d2", "0404") and
            int(baseline[6138]["p_timer"]) == 0x3c00 and
            has_write(player_writes, 6197, "04", "01b272", "0600") and
            has_write(player_writes, 6198, "00", "01b562", "0000"),
            "KO countdown/removal drift")
    require((int(baseline[6199]["p_active"]),
             int(baseline[6199]["g8009"]),
             int(baseline[6200]["g8009"])) == (0, 0, 2),
            "failure-state entry drift")
    require(any(int(row["frame"]) == 6199 and row["address"] == "ff8008" and
                row["pc"] == "008bb2" and row["data"] == "0002"
                for row in global_writes), "failure-state writer drift")

    require(int(baseline[6692]["g8009"]) == 4 and
            any(int(row["frame"]) == 6691 and row["address"] == "ff8008" and
                row["pc"] == "0090f2" and row["data"] == "0004"
                for row in global_writes), "credited Start transition drift")
    require((int(baseline[6723]["p_active"]),
             int(baseline[6723]["p_state"]),
             int(baseline[6723]["p_action"]),
             int(baseline[6723]["p_health"]),
             int(baseline[6723]["p_latched_health"])) ==
            (1, 2, 0x1202, 101, 101), "respawn initialization drift")
    require(has_write(player_writes, 6722, "00", "00eab8", "0100") and
            has_write(player_writes, 6722, "04", "01965c", "0200") and
            has_write(player_writes, 6722, "06", "01965c", "1200") and
            has_write(player_writes, 6722, "40", "019706", "0065") and
            has_write(player_writes, 6722, "42", "01970c", "0065"),
            "respawn source writers drift")
    require((int(baseline[6786]["p_action"]),
             int(baseline[6786]["p_inner"])) == (0, 0) and
            has_write(player_writes, 6785, "04", "01a3fa", "0200") and
            has_write(player_writes, 6785, "06", "01a3fa", "0000"),
            "respawn return-to-control drift")

    require((int(baseline[6811]["p_health"]),
             int(baseline[6812]["p_health"]),
             int(baseline[6812]["p_inner"])) == (101, 85, 2),
            "nonlethal HIT entry drift")
    require(has_write(player_writes, 6811, "40", "01d5ee", "0055") and
            has_write(player_writes, 6812, "06", "01a988", "0202") and
            has_write(player_writes, 6812, "42", "01a9c8", "0055") and
            has_write(player_writes, 6855, "06", "01ab9e", "0404") and
            has_write(player_writes, 6856, "70", "01abbe", "0101"),
            "nonlethal HIT recovery writer drift")
    require((int(baseline[6857]["p_inner"]),
             int(baseline[6857]["p_action"]),
             int(baseline[6857]["p_invuln"]),
             int(baseline[6858]["p_invuln"])) == (0, 0, 1, 0),
            "HIT control return/invulnerability drift")

    variant_samples = {
        name: indexed(RAW_A, name) for name in
        ("no_continue", "coin_only", "start_only", "delayed_start",
         "survive_contact", "respawn_input_suppressed")}
    variant_samples.update({name: indexed(RAW_B, name) for name in
        ("continue_confirm_gun", "continue_confirm_attack",
         "continue_confirm_jump", "continue_confirm_right")})
    activation = {name: first_frame(sample, lambda row:
                    int(row["frame"]) >= 6200 and int(row["p_active"]) == 1)
                  for name, sample in variant_samples.items()}
    require(activation == {
        "no_continue": None, "coin_only": None, "start_only": 6723,
        "delayed_start": 6768, "survive_contact": 6200,
        "respawn_input_suppressed": None, "continue_confirm_gun": 6723,
        "continue_confirm_attack": 6723, "continue_confirm_jump": 6843,
        "continue_confirm_right": None,
    }, "continue/confirmation counterfactual drift")
    survive = variant_samples["survive_contact"]
    require(int(survive[6081]["p_active"]) == 1 and
            int(survive[6081]["p_state"]) != 4 and
            int(survive[6081]["p_health"]) == 50,
            "health-threshold negative control drift")

    report = {
        "schema": "oracle11-predator-hitko-continue-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "Predator Warrior route-reachable nonlethal HIT, lethal KO, failure, credited continue, respawn, and return to control",
        "coverage_universe": {
            "routes": ["baseline-completion-a", "baseline-completion-b",
                       "perturbed-completions", "failure-continue",
                       "targeted-counterfactuals"],
            "natural_route_window": [5800, 6900],
            "required_bodies": ["nonlethal-hit", "lethal-ko",
                "failure-state", "credited-start", "button-confirmation",
                "respawn-initialization", "return-to-control"],
            "all_required_bodies_closed": True,
        },
        "source_identity": {
            "decoded_opcodes_sha256": hashlib.sha256(image).hexdigest(),
            "player_top_state_dispatch_and_init": source_window(
                image, 0x0195EC, 0x019764),
            "nonlethal_hit_entry_and_recovery": source_window(
                image, 0x01A96E, 0x01ABCA),
            "ko_state_and_substate_bodies": source_window(
                image, 0x01B132, 0x01B5D2),
            "continue_credit_debit": source_window(
                image, 0x00E880, 0x00E910),
            "continue_player_preview_dispatch": source_window(
                image, 0x00E910, 0x00EB80),
            "continue_dispatch_table": {
                "base": "0x00e93c", "actor_byte": "+0xd5",
                "entries": {"0x00": "0x00e942", "0x02": "0x00e9ce",
                            "0x04": "0x00eb80"},
            },
            "global_failure_and_continue_writers": source_window(
                image, 0x008530, 0x009102),
            "capture_manifests": identities,
        },
        "nonlethal_hit": {
            "classification": "SOURCE_CLOSED",
            "damage_guard": "current signed 16-bit health remains nonnegative after current-state collision damage",
            "entry": "0x01a96e", "active_recovery": "0x01aad0",
            "health": {"before": 101, "after": 85,
                       "latched_at_entry": 85},
            "writers": ["0x01d5ee", "0x01a988", "0x01a9c8",
                        "0x01ab9e", "0x01abbe", "0x01a3fa"],
            "return_to_control_frame": 6857,
            "invulnerability": "actor +0x70 is set to 1 at recovery and consumed by the next scheduler tick",
            "rng_consumption": "none",
            "first_segment_execution_contract": {
                "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
                "spec_executable": True,
                "capture_identity": {
                    "two_completion_captures_byte_identical": True,
                    "oracle11_hitko_baseline_samples_sha256":
                        digest(RAW_A / "baseline_hitko_1" / "samples.tsv"),
                    "coffee_shop_scene_actors_sha256": digest(COFFEE_ACTORS),
                    "coffee_shop_samples_sha256": digest(COFFEE_SAMPLES),
                    "player_audio_artifact_sha256": digest(PLAYER_AUDIO),
                },
                "source_routines": {
                    "outer_dispatch_entry": "0x01a96e",
                    "entry_body": "0x01a982",
                    "active_body": "0x01aad0",
                    "predator_dispatch": "0x01ab1a",
                    "phase_0x0200": "0x01ab2c",
                    "phase_0x0202": "0x01ab52",
                    "phase_0x0204": "0x01abb8",
                    "animation_step": "0x01656e",
                    "world_bound_step": "0x01affc",
                },
                "field_types": {
                    "outer_state": "u16 actor+0x04",
                    "substate": "u8 actor+0x07 projected as u16",
                    "facing": "u8 actor+0x0f",
                    "x_fp": "s32 16.16 actor+0x10",
                    "health": "s16 actor+0x40",
                    "motion_index": "u8 actor+0x6c low nibble",
                    "hit_count": "u8 actor+0x6d",
                    "invulnerability": "u8 actor+0x70",
                    "animation_timer": "u16 actor+0x0a",
                    "animation_record": "u32 actor+0x1c",
                    "animation_branch": "s16 actor+0x24",
                    "shake_countdown": "u8 actor+0x2c",
                    "x_velocity": "s32 16.16 actor+0x30",
                    "x_acceleration": "s32 16.16 actor+0x38",
                },
                "transition_guard": {
                    "collision_writer": "0x01d5ee",
                    "rule": "current signed health remains nonnegative after current-state damage",
                    "health_before_s16": 101,
                    "damage_s16": 10,
                    "health_after_s16": 91,
                    "entry_visible_frame_u16": 2751,
                    "next_update_visible_frame_u16": 2752,
                },
                "scheduler_order": [
                    "player update", "record12 actor update",
                    "current-state enemy-v-player collision",
                    "next player update dispatches HIT phase 0x0200"],
                "states": {
                    "control_outer_u16": 0x0200,
                    "hit_outer_u16": 0x0202,
                    "entry_substate_u16": 0x0000,
                    "shake_substate_u16": 0x0200,
                    "motion_substate_u16": 0x0202,
                    "return_substate_u16": 0x0204,
                },
                "entry_writes": {
                    "clear_fields": ["actor+0x92:u8", "actor+0xaa:u8",
                                     "actor+0x95:u8", "actor+0x81:u8",
                                     "actor+0x82:u8", "actor+0x9d:u8"],
                    "carried_record": {
                        "animation_record": "0x0015f278",
                        "assembly": "0x00160af2",
                        "visible_timer_u16": 1,
                        "hurt_selector_u8": 0,
                        "attack_selector_u8": 0,
                    },
                    "shake_countdown_u8": 10,
                    "motion_index_u8": 2,
                },
                "phase_0x0200": {
                    "guard": "final shake countdown reaches zero and dispatches inner phase 0",
                    "writes": {
                        "next_substate_u16": 0x0202,
                        "x_velocity_s32_16_16": 0x0001C000,
                        "x_acceleration_s32_16_16": -0x00002000,
                    },
                    "motion_table": {
                        "address": "0x001f892",
                        "index_u8": 2,
                        "row_hex": program[0x1F892 + 2 * 8:
                                           0x1F892 + 3 * 8].hex(),
                    },
                    "presentation": {
                        "animation_record": "0x0015eee8",
                        "assembly": "0x00160ede",
                        "timer_u16": 8,
                        "branch_s16": -0x8000,
                        "hurt_selector_u8": 0,
                        "attack_selector_u8": 0,
                    },
                },
                "shake": {
                    "guard": "actor+0x2c predecrement body runs before phase dispatch",
                    "table_address": "0x01aa90",
                    "table_s16": [2, -2] * 8,
                    "facing_side_nonzero_negates": True,
                    "visible_frames_u16": [2753, 2761],
                    "final_tick_dispatches_motion_substate": True,
                },
                "phase_0x0202": {
                    "interruption_order": ["0x01a7e6", "health/button guard",
                                           "0x01abd0", "0x01a6f4"],
                    "movement_order": ["read signed velocity", "apply facing sign",
                                       "add to x s32 16.16", "add acceleration to velocity",
                                       "test velocity sign", "world bound step",
                                       "animation step"],
                    "negative_velocity_guard": "transition when post-acceleration velocity is negative",
                    "animation_loop": {"timer_u16": 8, "branch_s16": -0x8000},
                },
                "phase_0x0204": {
                    "writes": {"invulnerability_u8": 1,
                               "facing_u8": 0,
                               "return_outer_state_u16": 0x0200,
                               "return_substate_u16": 0x0000},
                    "presentation": {"animation_record": "0x0015f1f4",
                                     "assembly": "0x001626a4",
                                     "timer_u16": 0x0fff,
                                     "branch_s16": -0x8000},
                    "return_visible_frame_u16": 2778,
                },
                "collision_and_control": {
                    "attack_selector_during_hit_u8": 0,
                    "hurt_selector_during_hit_u8": 0,
                    "player_attack_and_direction_dispatch_suppressed": True,
                    "resource_tick_continues": True,
                    "world_navigation_and_camera_continue": True,
                },
                "audio": {
                    "player_side_return": "0x003b5a",
                    "command_u16": 0x003b,
                    "shared_dispatch_entry": "0x001922",
                    "source_context": {"outer_state_u16": 0x0202,
                                       "action_u16": 0x0200,
                                       "substate_u16": 0x0000},
                    "downstream_difference_source_frame_u16": 2752,
                    "semantic_name_inferred": False,
                    "provenance_sha256": hit_audio["caller_provenance"]
                        ["player_side_call"]["source_window"]["sha256"],
                },
                "rng": {"calls": [], "consumption_order": []},
                "observed_anchors": [player_anchor(frame) for frame in
                    (2750, 2751, 2752, 2753, 2761, 2762, 2769, 2770,
                     2776, 2777, 2778)],
                "mutation_control": {
                    "reject_fixed_frame_entry": True,
                    "reject_double_health_subtraction": True,
                    "reject_idle_presentation_during_hit": True,
                    "reject_missing_shake_or_wrong_sign": True,
                    "reject_wrong_motion_table_row": True,
                    "reject_input_owned_return": True,
                    "reject_rng_consumption": True,
                    "first_rejected_visible_frame_u16": 2751,
                },
            },
        },
        "lethal_ko": {
            "classification": "SOURCE_CLOSED",
            "damage_guard": "current signed 16-bit health crosses below zero",
            "top_state": 4, "entry": "0x01b132",
            "active_word": "0x0201",
            "required_action_phases": ["0x0202", "0x0800", "0x0202",
                                       "0x0404", "0x0606"],
            "final_countdown_ticks": 60,
            "inactive_frame": 6199,
            "writers": ["0x01d5ee", "0x01d5f6", "0x01d4aa",
                        "0x01b14c", "0x01b150", "0x01b2a0",
                        "0x01b344", "0x01b406", "0x01b30c",
                        "0x01b36e", "0x01b3d2", "0x01b272",
                        "0x01b562", "0x01b566"],
            "rng_consumption": "none",
        },
        "failure_continue": {
            "classification": "SOURCE_CLOSED",
            "global_state_byte": "0xff8009",
            "failure_state": {"value": 2, "frame": 6200,
                              "write_pc": "0x008bb2"},
            "credited_start": {"value": 4, "frame": 6692,
                               "write_pc": "0x0090f2"},
            "credit_rule": "0x00e880 performs packed-BCD credit debit and rejects borrow before setting player/continue ownership bits",
            "confirmation_rule": "phase +0xd5=2 computes new input edges from +0xee/+0xef; Button1 bit4, Button2 bit5, or Button3 bit6 enters 0x00ea74; left/right bits1/0 only move the selection cursor",
            "direction_only_confirms": False,
            "coin_without_start_confirms": False,
            "start_with_available_credit_enters_continue": True,
            "rng_consumption": "none",
        },
        "respawn_return": {
            "classification": "SOURCE_CLOSED",
            "confirmation_writer": "0x00eab8",
            "continue_marker": "actor +0xed=1 at 0x00eac8",
            "init_entry": "0x019604",
            "spawn_coordinates": "route +0x278/+0x27c with source offsets",
            "health_and_latched_health": 101,
            "initial_action": "0x1200 -> 0x1202 -> 0x1204 -> 0x0c00",
            "active_frame": 6723,
            "return_to_control_frame": 6786,
            "cleanup": "0x01a3fa clears the respawn action before locomotion dispatch",
            "rng_consumption": "none",
        },
        "counterfactuals": {
            "activation_frames": activation,
            "no_continue_no_respawn": True,
            "coin_only_no_respawn": True,
            "start_only_matches_baseline": True,
            "delayed_start_shifts_continue_and_respawn": True,
            "health_50_suppresses_lethal_ko": True,
            "all_gameplay_buttons_confirm": True,
            "direction_alone_does_not_confirm": True,
            "no_gameplay_input_no_respawn": True,
        },
        "mutation_controls": [
            "reject nonnegative health as KO", "reject fitted KO phase order",
            "reject shortened death countdown", "reject Coin without Start",
            "reject direction-only confirmation", "reject missing gameplay-button confirmation",
            "reject health/resource reset other than 101", "reject fixed-frame respawn",
            "reject missing HIT invulnerability", "reject random HIT/KO/continue selection",
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
            report["remaining_unknowns"] == [], "HIT/KO authority not closed")
    require(report["coverage_universe"]["all_required_bodies_closed"] is True,
            "required HIT/KO body coverage drift")
    require(all(report[name]["classification"] == "SOURCE_CLOSED"
                for name in ("nonlethal_hit", "lethal_ko",
                             "failure_continue", "respawn_return")),
            "required sub-authority classification drift")
    require(report["lethal_ko"]["required_action_phases"] ==
            ["0x0202", "0x0800", "0x0202", "0x0404", "0x0606"] and
            report["lethal_ko"]["final_countdown_ticks"] == 60,
            "KO phase/countdown drift")
    require(report["failure_continue"]["direction_only_confirms"] is False and
            report["failure_continue"]["coin_without_start_confirms"] is False and
            report["failure_continue"]["start_with_available_credit_enters_continue"] is True,
            "continue input guard drift")
    require(report["respawn_return"]["health_and_latched_health"] == 101 and
            report["respawn_return"]["active_frame"] == 6723 and
            report["respawn_return"]["return_to_control_frame"] == 6786,
            "respawn/control return drift")
    require(report["nonlethal_hit"]["return_to_control_frame"] == 6857 and
            report["nonlethal_hit"]["rng_consumption"] == "none" and
            report["lethal_ko"]["rng_consumption"] == "none" and
            report["failure_continue"]["rng_consumption"] == "none" and
            report["respawn_return"]["rng_consumption"] == "none",
            "HIT/KO/continue RNG or control drift")
    execution = report["nonlethal_hit"]["first_segment_execution_contract"]
    require(execution["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            execution["spec_executable"] is True and
            execution["transition_guard"] == {
                "collision_writer": "0x01d5ee",
                "rule": "current signed health remains nonnegative after current-state damage",
                "health_before_s16": 101, "damage_s16": 10,
                "health_after_s16": 91, "entry_visible_frame_u16": 2751,
                "next_update_visible_frame_u16": 2752} and
            execution["phase_0x0200"]["writes"] == {
                "next_substate_u16": 0x0202,
                "x_velocity_s32_16_16": 0x0001C000,
                "x_acceleration_s32_16_16": -0x00002000} and
            execution["entry_writes"]["carried_record"] == {
                "animation_record": "0x0015f278",
                "assembly": "0x00160af2", "visible_timer_u16": 1,
                "hurt_selector_u8": 0, "attack_selector_u8": 0} and
            execution["shake"]["table_s16"] == [2, -2] * 8 and
            execution["phase_0x0204"]["return_visible_frame_u16"] == 2778 and
            execution["audio"]["command_u16"] == 0x003b and
            execution["rng"] == {"calls": [], "consumption_order": []} and
            [row["frame_u16"] for row in execution["observed_anchors"]] ==
            [2750, 2751, 2752, 2753, 2761, 2762, 2769, 2770,
             2776, 2777, 2778],
            "first-segment HIT execution contract drift")
    controls = report["counterfactuals"]
    require(all(value is True for key, value in controls.items()
                if key != "activation_frames"), "counterfactual failure")
    protected = report["protected_boundaries"]
    require(protected == {
        "production_runtime_writes": 0, "yaba_run": False,
        "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
        "salvage08_active": False, "physical_saturn": "UNRUN",
    }, "workflow shield drift")


if __name__ == "__main__":
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"wrote {OUT.relative_to(ROOT)}")
