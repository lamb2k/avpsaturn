#!/usr/bin/env python3
"""Derive the bounded class-0x1f state/facing/presentation contract."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle09_alien_state_source_closure"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
ORACLE05 = ROOT / "data" / "oracle05_street_alien_ai.json"
CONTACT = ROOT / "data" / "enemy_contact_capture.json"
SOURCE_COMBAT = ROOT / "data" / "avsp_source_combat_presentation_contract.json"
HIT_KO = ROOT / "data" / "avsp_hit_ko_writer_set.json"
OUT = ROOT / "data" / "oracle09_street_alien_state_facing_presentation.json"

VARIANTS = (
    "cold_run_1", "cold_run_2", "left_static", "right_static",
    "above_static", "below_static", "cross_left_to_right",
    "cross_right_to_left", "move_during_attack",
    "attack_during_approach", "attack_during_attack", "inside_range",
    "outside_range",
)
FILES = ("samples.tsv", "enemy_writes.tsv", "class_entries.tsv", "rng_calls.tsv")
ACTOR_FIELDS = (
    "e_active", "e_class", "e_type", "e_state", "e_inner", "e_action",
    "e_phase", "e_facing", "e_x", "e_y", "e_z", "e_anim",
    "e_assembly", "e_hurt", "e_attack", "e_timer", "e_health",
    "e_target", "e_flags5d", "e_hex",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii") + b"\n"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    require(bool(rows), f"empty trace: {path}")
    return rows


def load_samples(variant: str) -> list[dict[str, int | str]]:
    rows = read_tsv(RAW / variant / "samples.tsv")
    required = {"frame", "variant", "input_word", "rng_word", "p_state",
                "p_action", "p_facing", "p_x", "p_y", "p_z", *ACTOR_FIELDS}
    require(required <= set(rows[0]), f"sample schema drift: {variant}")
    text_fields = {"variant", "rng_word", "e_anim", "e_assembly", "e_hex"}
    converted = [{key: value if key in text_fields else int(value)
                  for key, value in row.items()} for row in rows]
    require(len(converted) == 701 and converted[0]["frame"] == 3900 and
            converted[-1]["frame"] == 4600,
            f"sample window drift: {variant}")
    return converted


def indexed(rows: list[dict[str, int | str]]) -> dict[int, dict[str, int | str]]:
    return {int(row["frame"]): row for row in rows}


def same_actor(left: dict[int, dict[str, int | str]],
               right: dict[int, dict[str, int | str]], start: int,
               end: int) -> bool:
    return all(left[frame]["e_hex"] == right[frame]["e_hex"]
               for frame in range(start, end + 1))


def first_actor_diff(left: dict[int, dict[str, int | str]],
                     right: dict[int, dict[str, int | str]],
                     start: int = 3900) -> int | None:
    for frame in range(start, 4601):
        if left[frame]["e_hex"] != right[frame]["e_hex"]:
            return frame
    return None


def write_exists(rows: list[dict[str, str]], *, frame: int, offset: str,
                 pc: str, data: str | None = None,
                 mask: str | None = None) -> bool:
    return any(int(row["frame"]) == frame and row["offset"].lower() == offset and
               row["pc"].lower() == pc and
               (data is None or row["data"].lower() == data) and
               (mask is None or row["mask"].lower() == mask)
               for row in rows)


def u32(data: bytes, address: int) -> int:
    require(0 <= address <= len(data) - 4, f"program pointer outside image: {address:06x}")
    return int.from_bytes(data[address:address + 4], "big")


def record_identity(program: bytes, row: dict[str, int | str]) -> dict[str, object]:
    record = int(str(row["e_anim"]), 16)
    assembly = int(str(row["e_assembly"]), 16)
    require(u32(program, record + 4) == assembly,
            f"record/assembly pointer drift at 0x{record:06x}")
    require(assembly + 32 <= len(program), "assembly source window outside program")
    return {
        "animation_record": f"0x{record:06x}",
        "assembly": f"0x{assembly:06x}",
        "hurt_selector": int(row["e_hurt"]),
        "attack_selector": int(row["e_attack"]),
        "animation_record_sha256": hashlib.sha256(
            program[record:record + 16]).hexdigest(),
        "assembly_source_window_sha256": hashlib.sha256(
            program[assembly:assembly + 32]).hexdigest(),
    }


def presentation_cycle(program: bytes, samples: dict[int, dict[str, int | str]],
                       start: int, end: int,
                       expected: list[str]) -> list[dict[str, object]]:
    records: list[str] = []
    rows: dict[str, dict[str, int | str]] = {}
    for frame in range(start, end + 1):
        row = samples[frame]
        record = str(row["e_anim"])
        if record not in rows:
            rows[record] = row
            records.append(record)
    require(records == expected, f"presentation cycle drift: {start}-{end}")
    return [record_identity(program, rows[record]) for record in records]


def state_sample(row: dict[str, int | str]) -> dict[str, object]:
    return {
        "active": row["e_active"], "state": row["e_state"],
        "inner": row["e_inner"], "action": f"0x{int(row['e_action']):04x}",
        "facing": row["e_facing"], "world": {"x": row["e_x"],
        "y": row["e_y"], "z": row["e_z"]},
        "animation_record": f"0x{int(str(row['e_anim']), 16):06x}",
        "assembly": f"0x{int(str(row['e_assembly']), 16):06x}",
        "timer": row["e_timer"], "health": row["e_health"],
        "target": f"0xff{int(row['e_target']):04x}",
    }


def build_report() -> dict[str, object]:
    manifest = json.loads((RAW / "input_manifest.json").read_text(encoding="utf-8-sig"))
    require([item["name"] for item in manifest["variants"]] == list(VARIANTS),
            "ORACLE-09 variant inventory drift")
    field_names = {
        "samples.tsv": "samples_sha256", "enemy_writes.tsv": "writes_sha256",
        "class_entries.tsv": "class_entries_sha256",
        "rng_calls.tsv": "rng_calls_sha256",
    }
    for item in manifest["variants"]:
        for filename, field in field_names.items():
            require(item[field] == digest(RAW / item["name"] / filename),
                    f"{item['name']}: {field} drift")
    require(all(digest(RAW / "cold_run_1" / filename) ==
                digest(RAW / "cold_run_2" / filename) for filename in FILES),
            "ORACLE-09 cold captures are not byte-identical")

    loaded = {name: load_samples(name) for name in VARIANTS}
    maps = {name: indexed(rows) for name, rows in loaded.items()}
    writes = {name: read_tsv(RAW / name / "enemy_writes.tsv")
              for name in VARIANTS}
    base = maps["cold_run_1"]
    oracle05 = json.loads(ORACLE05.read_text(encoding="utf-8"))
    contact = json.loads(CONTACT.read_text(encoding="utf-8"))
    source_combat = json.loads(SOURCE_COMBAT.read_text(encoding="utf-8"))
    program = PROGRAM.read_bytes()

    require((base[3983]["e_active"], base[3983]["e_class"],
             base[3983]["e_type"], base[3983]["e_state"],
             base[3983]["e_health"], base[3983]["e_target"]) ==
            (1, 31, 12, 2, 87, 0x8380), "target spawn identity drift")
    require(all(base[frame]["e_target"] == 0x8380
                for frame in range(3983, 4447) if base[frame]["e_active"]),
            "one-player target pointer drift")

    attack_writes = writes["cold_run_1"]
    require(write_exists(attack_writes, frame=4252, offset="2a", pc="060d1c",
                         data="7878", mask="ff00"), "attack timer writer drift")
    require(write_exists(attack_writes, frame=4252, offset="06", pc="060d2a",
                         data="1818", mask="ff00") and
            write_exists(attack_writes, frame=4252, offset="06", pc="060d30",
                         data="0000", mask="00ff"), "attack action writer drift")
    require(write_exists(attack_writes, frame=4252, offset="1c", pc="01652a",
                         data="0012") and
            write_exists(attack_writes, frame=4252, offset="1e", pc="01652a",
                         data="e8ec"), "attack animation writer drift")
    require((base[4253]["e_action"], base[4253]["e_facing"],
             base[4253]["e_timer"], base[4253]["e_anim"],
             base[4253]["e_assembly"]) ==
            (0x1800, 1, 120, "0012e8ec", "0012f5de"),
            "attack next-sample identity drift")

    rtl = maps["cross_right_to_left"]
    rtl_writes = writes["cross_right_to_left"]
    require(write_exists(rtl_writes, frame=4284, offset="06", pc="060d52",
                         data="1a1a", mask="ff00") and
            write_exists(rtl_writes, frame=4284, offset="06", pc="060d58",
                         data="0000", mask="00ff") and
            write_exists(rtl_writes, frame=4284, offset="0e", pc="060d5e",
                         data="0000", mask="00ff") and
            write_exists(rtl_writes, frame=4284, offset="1c", pc="01652a",
                         data="0012") and
            write_exists(rtl_writes, frame=4284, offset="1e", pc="01652a",
                         data="d5e4"), "crossing state writer set drift")
    require((rtl[4285]["e_action"], rtl[4285]["e_facing"],
             rtl[4285]["e_anim"], rtl[4285]["e_assembly"]) ==
            (0x1a00, 0, "0012d5e4", "0012fae8"),
            "crossing state identity drift")

    above = maps["above_static"]
    above_writes = writes["above_static"]
    require(write_exists(above_writes, frame=4322, offset="0e", pc="060822",
                         data="0000", mask="00ff") and
            write_exists(above_writes, frame=4322, offset="04", pc="0610c8",
                         data="0808", mask="00ff"), "lane/reposition writer drift")
    require((above[4323]["e_inner"], above[4323]["e_action"],
             above[4323]["e_facing"], above[4323]["e_anim"],
             above[4323]["e_assembly"]) ==
            (8, 0x0600, 0, "0012d5e4", "0012fae8"),
            "above-lane state identity drift")

    left = maps["left_static"]
    require((left[4006]["p_x"], left[4006]["e_x"], left[4006]["e_action"],
             left[4006]["e_facing"]) == (800, 1019, 0x0408, 1),
            "left-static authored-facing witness drift")
    require(same_actor(base, maps["right_static"], 3975, 4375),
            "right-static control changed opening actor schedule")
    require(same_actor(base, maps["outside_range"], 3975, 4375),
            "outside-range control changed opening actor schedule")
    require(same_actor(base, maps["move_during_attack"], 4253, 4412),
            "movement during attack changed committed actor action")
    require(same_actor(base, maps["attack_during_attack"], 3900, 4600),
            "player attack during enemy attack changed actor bytes")
    inside = maps["inside_range"]
    require((inside[4054]["e_state"], inside[4055]["e_state"],
             inside[4055]["e_facing"], inside[4056]["e_active"],
             inside[4206]["e_active"], inside[4207]["e_active"]) ==
            (2, 4, 0, 2, 0, 1), "inside-range contact lifecycle drift")

    approach_cycle = presentation_cycle(
        program, base, 3984, 4022,
        ["0012ec04", "0012ec14", "0012ec24", "0012ec34",
         "0012ec44", "0012ec54", "0012ec64", "0012ec74"])
    attack_cycle = presentation_cycle(
        program, base, 4253, 4372,
        ["0012e8ec", "0012e8fc", "0012e90c", "0012e91c"])

    rendered = []
    for event in source_combat["events"]:
        enemy = event["enemy_contact"]
        reaction = event["enemy_reaction"]
        rendered.append({
            "contact_frame": event["contact_frame"],
            "source_actor_tick": {
                "slot": enemy["slot"], "class_id": enemy["class_id"],
                "type": enemy["type"], "substate": enemy["substate"],
                "action": f"0x{enemy['action']:04x}", "facing": enemy["facing"],
                "animation_record": enemy["animation_record"],
                "assembly": enemy["assembly"],
                "source_render_frame": enemy["source_render_frame"],
                "object_identity_sha256": enemy["object_identity_sha256"],
                "tile_identity_sha256": enemy["tile_identity_sha256"],
                "palette": enemy["palette"],
            },
            "reaction_render": {
                "animation_record": reaction["animation_record"],
                "assembly": reaction["assembly"],
                "source_render_frame": reaction["source_render_frame"],
                "object_identity_sha256": reaction["object_identity_sha256"],
                "tile_identity_sha256": reaction["tile_identity_sha256"],
                "palette": reaction["palette"],
            },
        })

    loop = oracle05["observed_loop"]
    rng = oracle05["rng_consumption"]
    scheduler = oracle05["scheduler"]
    report: dict[str, object] = {
        "schema": 1,
        "task": "ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION",
        "classification": "MEASURED_MAME_SOURCE_BOUNDED_ALIEN_STATE_PRESENTATION_CONTRACT",
        "target": {"set": "avspu", "revision": "USA 940520",
                   "slot": "0xffa000", "class": "0x1f", "type": 12,
                   "one_player_target": "0xff8380"},
        "scope": "one class-0x1f type-12 actor on the deterministic first-live encounter route; not a generic alien AI, range model, or multiplayer controller",
        "evidence_tier": "MAME_COUNTERFACTUAL_TRACE_PROGRAM_RECORD_AND_ACCEPTED_RENDER_IDENTITY",
        "saturn_emulator": "UNRUN",
        "physical_saturn": "UNRUN",
        "provenance": {
            "mame": manifest["mame"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "rom_sha256": manifest["roms"],
            "capture_manifest_sha256": digest(RAW / "input_manifest.json"),
            "decrypted_program_sha256": digest(PROGRAM),
            "decrypted_opcodes_sha256": digest(OPCODES),
            "oracle05_sha256": digest(ORACLE05),
            "enemy_contact_capture_sha256": digest(CONTACT),
            "source_combat_contract_sha256": digest(SOURCE_COMBAT),
            "hit_ko_writer_set_sha256": digest(HIT_KO),
            "capture_artifacts": {
                item["name"]: {filename.replace(".tsv", "_sha256"):
                               digest(RAW / item["name"] / filename)
                               for filename in FILES}
                for item in manifest["variants"]
            },
        },
        "declared_capture_mutations": manifest["declared_mutations"],
        "determinism": {
            "cold_runs_byte_identical": True,
            "identical_artifacts": list(FILES),
            "sample_frames_each": 701,
            "frame_window": [3900, 4600],
        },
        "actor_layout": {
            "active": "actor+0x00 byte", "class": "actor+0x02 byte",
            "state_inner": "actor+0x04 bytes", "action_phase": "actor+0x06 bytes",
            "type": "actor+0x08 byte", "facing": "actor+0x0f byte",
            "world_x": "actor+0x10 signed word", "world_y": "actor+0x14 signed word",
            "world_z": "actor+0x18 signed word", "animation_record": "actor+0x1c long",
            "target_pointer": "actor+0x28 low word", "action_timer": "actor+0x2a high byte",
            "health": "actor+0x40 signed word",
        },
        "source_dispatch": copy.deepcopy(oracle05["static_binding"]),
        "bounded_state_contract": {
            "spawn": state_sample(base[3983]),
            "authored_approach_0x1600": {
                "first_sample": state_sample(base[3984]),
                "measured_motion_window": {"frames": [4214, 4252],
                    "from": {"x": 1181, "z": 297},
                    "to": {"x": 1292, "z": 274}, "facing": 1},
                "presentation_cycle": approach_cycle,
                "authority": "source route state; left-static evidence proves this is not a generic face-target rule",
            },
            "rng_attack_0x1800": {
                "dispatch_write_frame": 4252, "first_sample": state_sample(base[4253]),
                "writers": {"timer_120": "0x060d1c", "action_high": "0x060d2a",
                            "action_low": "0x060d30", "animation_record": "0x01652a"},
                "rng": copy.deepcopy(rng["attack_selection"]),
                "fixed_rng_control": copy.deepcopy(rng["fixed_point_control"]),
                "presentation_cycle": attack_cycle,
                "contact_frames": contact["tracked_attack"]["contact_frames"],
                "contact_offsets": contact["tracked_attack"]["contact_action_offsets"],
                "damage_each_native_health_units": contact["tracked_attack"]["damage_per_contact_native_health_units"],
                "rule": "RNG selects the measured action timer; animation record selection is state-owned and must not be randomly cycled",
            },
            "right_to_left_crossing_0x1a00": {
                "player_cross_write_after_frame": 4100,
                "source_write_frame": 4284, "first_sample": state_sample(rtl[4285]),
                "writers": {"timer_160": "0x060d1c", "action_high": "0x060d52",
                            "action_low": "0x060d58", "facing_0": "0x060d5e",
                            "animation_record": "0x01652a"},
                "same_tick_identity": {"action": "0x1a00", "facing": 0,
                    "animation_record": "0x12d5e4", "assembly": "0x12fae8"},
                "scope_guard": "measured delayed state response on this route; not an immediate universal crossing rule",
            },
            "above_lane_reposition_inner_8": {
                "source_write_frame": 4322, "first_sample": state_sample(above[4323]),
                "writers": {"facing_0": "0x060822", "inner_8": "0x0610c8",
                            "animation_record": "0x01652a"},
                "same_tick_identity": {"inner": 8, "action": "0x0600", "facing": 0,
                    "animation_record": "0x12d5e4", "assembly": "0x12fae8"},
                "return_facing_sample": {"frame": 4410, "facing": 1,
                    "writer": "0x041b86"},
            },
        },
        "counterfactuals": {
            "player_left": {"position": {"x": 800, "z": 319},
                "witness_frame": 4006, "actor": state_sample(left[4006]),
                "finding": "actor remains facing 1 with the player to its left; face-target-every-frame is falsified"},
            "player_right": {"position": {"x": 1500, "z": 319},
                "actor_identical_to_baseline_through_frame": 4375,
                "first_actor_difference_after_hold_release": first_actor_diff(base, maps["right_static"]),
                "finding": "opening route action, facing, and presentation are invariant during the declared hold"},
            "cross_left_to_right": {"cross_after_frame": 4100,
                "first_reapproach_frame": 4208,
                "sample": state_sample(maps["cross_left_to_right"][4208]),
                "finding": "source returns to authored 0x1600 facing 1; no arbitrary immediate sprite flip"},
            "cross_right_to_left": {"cross_after_frame": 4100,
                "source_response_frame": 4285,
                "sample": state_sample(rtl[4285]),
                "finding": "source state writes action, facing, animation record, and assembly together"},
            "player_above": {"position": {"x": 1300, "z": 400},
                "source_response_frame": 4323, "sample": state_sample(above[4323])},
            "player_below": {"position": {"x": 1300, "z": 220},
                "spawn_sample": state_sample(maps["below_static"][3983]),
                "finding": "spawn lane changes from z=343 to z=336, while facing remains 1; do not translate this into screen-y directly"},
            "motion_during_approach": {
                "comparison": "baseline route inputs versus right_static player hold",
                "actor_identical_frames": [3975, 4375],
                "finding": "the authored approach/attack schedule is invariant in the compared window"},
            "motion_during_attack": {"input_frames": [4253, 4372],
                "actor_identical_through_frame": 4412,
                "first_actor_difference": first_actor_diff(base, maps["move_during_attack"]),
                "finding": "player motion does not retarget or flip the active enemy attack state"},
            "player_attack_during_approach": {"input_frames": [4050, 4054],
                "first_actor_difference": first_actor_diff(base, maps["attack_during_approach"]),
                "baseline_timer_at_4093": base[4093]["e_timer"],
                "mutant_timer_at_4093": maps["attack_during_approach"][4093]["e_timer"],
                "finding": "player action perturbs shared RNG before the next source selection; it does not authorize a direct AI interruption rule"},
            "player_attack_during_attack": {"input_frames": [4300, 4304],
                "actor_bytes_identical_full_capture": True,
                "finding": "the input does not directly cancel, reroll, or flip the active enemy attack"},
            "inside_range": {"position": {"x": 1000, "z": 343},
                "hit_state_frame": 4055, "death_active_frame": 4056,
                "inactive_frame": 4206, "respawn_frame": 4207,
                "finding": "contact/hit lifecycle, not a clean attack-range selector witness"},
            "outside_range": {"position": {"x": 1800, "z": 400},
                "actor_identical_to_baseline_through_frame": 4375,
                "finding": "opening attack selection remains route/RNG-owned; no Euclidean range threshold is generalized"},
        },
        "presentation_identity": {
            "animation_record_layout": {"assembly_pointer": "record+0x04",
                "hurt_selector": "record+0x08", "attack_selector": "record+0x09"},
            "state_owned_rule": "choose the animation record from the active source state, then consume its assembly pointer; never cycle assemblies independently",
            "rendered_source_bound_hit_identities": rendered,
        },
        "scheduler_rng_hit_ko": {
            "scheduler": {"routine": scheduler["routine"],
                "executed_slot_count": scheduler["executed_slot_count"],
                "target_zero_based_pool_index": scheduler["target_zero_based_pool_index"],
                "target_slot": scheduler["target_slot"]},
            "rng_recurrence": oracle05["static_binding"]["rng_recurrence"],
            "hit_recovery_ko_removal": copy.deepcopy(loop["hit_recovery_ko_removal"]),
            "authority": "consumed by exact identity from accepted ORACLE-05; not re-inferred from presentation",
        },
        "negative_controls": {
            "generic_face_target_every_frame_forbidden": True,
            "immediate_universal_crossing_flip_forbidden": True,
            "independent_random_assembly_selection_forbidden": True,
            "guessed_euclidean_attack_range_forbidden": True,
            "shared_player_enemy_navigation_clamp_forbidden": True,
            "presentation_owned_hit_ko_or_removal_forbidden": True,
        },
        "bounded_findings": {
            "state_substate_dispatch": "MEASURED_AND_STATIC_BOUND",
            "opening_approach_lane_motion": "MEASURED_AUTHORED_ROUTE_STATE",
            "target_crossing_facing_state": "MEASURED_BOUNDED_ASYMMETRIC_RESPONSE",
            "animation_record_assembly_identity": "MEASURED_STATE_OWNED",
            "rendered_hit_state_identity": "SOURCE_BOUND_ACCEPTED_OBJECT_AND_TILE_IDENTITY",
            "attack_rng_timer_contacts": "MEASURED_AND_CONSUMED_FROM_ORACLE05",
            "hit_ko_removal": "CONSUMED_FROM_ACCEPTED_ORACLE05_AND_SOURCE_COMBAT",
            "generic_range_threshold": "UNKNOWN_NOT_GENERALIZED",
            "generic_alien_ai": "UNKNOWN_OUT_OF_SCOPE",
            "multiplayer_targeting": "UNKNOWN_OUT_OF_SCOPE",
            "saturn_runtime": "UNRUN",
        },
    }
    validate(report)
    mutation_self_test(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == 1, "ORACLE-09 schema drift")
    require(report["classification"] ==
            "MEASURED_MAME_SOURCE_BOUNDED_ALIEN_STATE_PRESENTATION_CONTRACT",
            "ORACLE-09 classification drift")
    require(report["saturn_emulator"] == "UNRUN" and
            report["physical_saturn"] == "UNRUN", "Saturn status overclaim")
    require(report["determinism"]["cold_runs_byte_identical"] is True,
            "ORACLE-09 determinism drift")
    states = report["bounded_state_contract"]
    require(states["right_to_left_crossing_0x1a00"]["same_tick_identity"] ==
            {"action": "0x1a00", "facing": 0,
             "animation_record": "0x12d5e4", "assembly": "0x12fae8"},
            "crossing state/facing/presentation identity drift")
    require(states["rng_attack_0x1800"]["first_sample"]["assembly"] ==
            "0x12f5de" and
            states["rng_attack_0x1800"]["first_sample"]["timer"] == 120,
            "attack state presentation drift")
    require([item["animation_record"] for item in
             states["authored_approach_0x1600"]["presentation_cycle"]] ==
            ["0x12ec04", "0x12ec14", "0x12ec24", "0x12ec34",
             "0x12ec44", "0x12ec54", "0x12ec64", "0x12ec74"],
            "approach presentation cycle drift")
    require([item["animation_record"] for item in
             states["rng_attack_0x1800"]["presentation_cycle"]] ==
            ["0x12e8ec", "0x12e8fc", "0x12e90c", "0x12e91c"],
            "attack presentation cycle drift")
    require(report["counterfactuals"]["player_left"]["witness_frame"] == 4006 and
            report["counterfactuals"]["player_left"]["actor"]["facing"] == 1,
            "left-side negative control drift")
    require(report["counterfactuals"]["player_attack_during_attack"]
            ["actor_bytes_identical_full_capture"] is True,
            "attack-during-attack control drift")
    require(report["scheduler_rng_hit_ko"]["scheduler"]
            ["target_zero_based_pool_index"] == 14,
            "scheduler order drift")
    require(report["scheduler_rng_hit_ko"]["hit_recovery_ko_removal"]
            ["health_sequence"] == [87, 63, 39, 8, -1],
            "HIT/KO health sequence drift")
    rendered = report["presentation_identity"]["rendered_source_bound_hit_identities"]
    require(len(rendered) == 4 and all(
        item["source_actor_tick"]["object_identity_sha256"] and
        item["source_actor_tick"]["tile_identity_sha256"] and
        item["reaction_render"]["object_identity_sha256"] and
        item["reaction_render"]["tile_identity_sha256"] for item in rendered),
        "render identity is vacuous")
    require(report["negative_controls"]
            ["independent_random_assembly_selection_forbidden"] is True and
            report["negative_controls"]["generic_face_target_every_frame_forbidden"] is True,
            "disconnected facing/assembly behavior admitted")
    require(report["bounded_findings"]["generic_range_threshold"] ==
            "UNKNOWN_NOT_GENERALIZED" and
            report["bounded_findings"]["generic_alien_ai"] == "UNKNOWN_OUT_OF_SCOPE",
            "ORACLE-09 scope widened")
    for key, value in report["provenance"].items():
        if key.endswith("sha256") and isinstance(value, str):
            require(len(value) == 64 and all(ch in "0123456789abcdef" for ch in value),
                    f"provenance hash drift: {key}")


def mutation_self_test(report: dict[str, object]) -> None:
    mutations = []
    changed = copy.deepcopy(report)
    changed["determinism"]["cold_runs_byte_identical"] = False
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["bounded_state_contract"]["right_to_left_crossing_0x1a00"][
        "same_tick_identity"]["facing"] = 1
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["bounded_state_contract"]["rng_attack_0x1800"][
        "first_sample"]["assembly"] = "0x12fa0c"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["scheduler_rng_hit_ko"]["scheduler"]["target_zero_based_pool_index"] = 15
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["negative_controls"]["independent_random_assembly_selection_forbidden"] = False
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["presentation_identity"]["rendered_source_bound_hit_identities"][0][
        "source_actor_tick"]["object_identity_sha256"] = ""
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["physical_saturn"] = "PASS"
    mutations.append(changed)
    for index, mutant in enumerate(mutations):
        try:
            validate(mutant)
        except ValueError:
            continue
        raise ValueError(f"ORACLE-09 mutation {index} unexpectedly passed")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"ORACLE-09 PASS {OUT.relative_to(ROOT)} sha256={digest(OUT)}")


if __name__ == "__main__":
    main()
