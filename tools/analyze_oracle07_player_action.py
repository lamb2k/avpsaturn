#!/usr/bin/env python3
"""Derive the bounded Predator Warrior action/equipment source contract.

The private MAME traces stay under .deps.  This analyzer checks their paired
cold-run identity, input perturbations, actor-field writers, and frame-indexed
state changes, then emits only the engineering contract needed by the first
live encounter.  It does not modify or validate the Saturn runtime.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame"
PRIMARY = RAW / "oracle07_player_action_equipment"
EQUIPMENT = RAW / "oracle07_player_equipment_probe"
CLOSE = RAW / "oracle07_player_close_combo_probe"
JUMP = RAW / "oracle07_player_jump_probe"
PROGRAM = RAW / "actorprobe" / "decrypted_program_2m.bin"
SOURCE_COMBAT = ROOT / "data" / "avsp_source_combat_presentation_contract.json"
ORACLE04 = ROOT / "data" / "oracle04_predator_warrior_control_actions.json"
PLAYER_HUD = ROOT / "data" / "player_hud_capture.json"
HIT_KO = ROOT / "data" / "avsp_hit_ko_writer_set.json"
OUT = ROOT / "data" / "oracle07_predator_warrior_action_graph_equipment.json"

SAMPLE_REQUIRED = (
    "frame", "variant", "input_word", "p_active", "p_class", "p_state",
    "p_inner", "p_action", "p_phase", "p_type", "p_facing", "p_x",
    "p_y", "p_z", "p_anim", "p_timer", "p_hit", "p_source",
    "p_health", "p_latched_health", "p_hurt", "p_attack", "actor_hex",
)

ANIMATION_SEQUENCES = {
    "idle": [0x15F1F4],
    "walk": [0x15F208, 0x15F218, 0x15F228, 0x15F238, 0x15F248,
             0x15F258, 0x15F268],
    "jump": [0x15F2CC, 0x15F2DC, 0x15F2F0, 0x15F300, 0x15F310,
             0x15F320, 0x15F330],
    "dash_right_observed_before_hit": [0x15F2CC, 0x15F2DC, 0x15F43C,
                                        0x15F44C],
    "gun_observed_before_hit": [0x15FCFC],
    "contextual_button2": [0x160288, 0x160298, 0x1602A8, 0x1602B8,
                            0x1602C8],
    "special": [0x15FD10, 0x15FD20, 0x15FD30, 0x15FD40, 0x15FD50,
                0x15FD60, 0x15FD70, 0x15FD80, 0x15FD90, 0x15FDA0,
                0x15FDB0, 0x15FDC0, 0x15FDD0, 0x15FDE0, 0x15FDF0,
                0x15FE00, 0x15FE10],
    "close_1": [0x1600E8, 0x1600F8, 0x160108, 0x160118],
    "close_2": [0x16012C, 0x16013C, 0x16014C, 0x16015C, 0x16016C,
                0x16017C],
    "close_3": [0x160190, 0x1601A0, 0x1601B0, 0x1601C0, 0x1601D0,
                0x1601E0],
    "close_4": [0x1601F4, 0x160204, 0x160214, 0x160224, 0x160234,
                0x160244, 0x160254, 0x160264, 0x160274],
    "hit": [0x15F054],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii") + b"\n"


def manifest(root: Path) -> dict:
    return json.loads((root / "input_manifest.json").read_text(
        encoding="utf-8-sig"))


def parse_tsv(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    require(bool(lines), f"empty trace: {path}")
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line:
            continue
        values = line.split("\t")
        require(len(values) == len(header), f"incomplete trace row: {path}")
        rows.append(dict(zip(header, values)))
    return rows


def samples(root: Path, variant: str) -> list[dict[str, int | str]]:
    raw = parse_tsv(root / variant / "samples.tsv")
    require(all(field in raw[0] for field in SAMPLE_REQUIRED),
            f"sample schema mismatch: {root.name}/{variant}")
    rows: list[dict[str, int | str]] = []
    for row in raw:
        converted: dict[str, int | str] = {}
        for key, value in row.items():
            if key in ("variant", "actor_hex", "player_header_hex"):
                converted[key] = value
            elif key == "p_anim":
                converted[key] = int(value, 16)
            else:
                converted[key] = int(value)
        rows.append(converted)
    require(rows[0]["frame"] == 2400 and rows[-1]["frame"] == 5469 and
            len(rows) == 3070, f"sample window mismatch: {root.name}/{variant}")
    return rows


def indexed(rows: list[dict[str, int | str]]) -> dict[int, dict[str, int | str]]:
    return {int(row["frame"]): row for row in rows}


def writes(root: Path, variant: str) -> list[dict[str, str]]:
    return parse_tsv(root / variant / "player_writes.tsv")


def has_write(rows: list[dict[str, str]], *, frame: int, offset: str,
              pc: str, data: str | None = None, mask: str | None = None) -> bool:
    return any(int(row["frame"]) == frame and row["offset"].lower() == offset and
               row["pc"].lower() == pc and
               (data is None or row["data"].lower() == data) and
               (mask is None or row["mask"].lower() == mask)
               for row in rows)


def actor_byte(row: dict[str, int | str], offset: int) -> int:
    blob = bytes.fromhex(str(row["actor_hex"]))
    require(len(blob) >= 0xC0, "actor snapshot is shorter than 0xc0 bytes")
    return blob[offset]


def actor_u16(row: dict[str, int | str], offset: int) -> int:
    blob = bytes.fromhex(str(row["actor_hex"]))
    return int.from_bytes(blob[offset:offset + 2], "big")


def u32(blob: bytes, offset: int) -> int:
    return int.from_bytes(blob[offset:offset + 4], "big")


def animation_contract(program: bytes) -> dict[str, list[dict[str, object]]]:
    result = {}
    for name, sequence in ANIMATION_SEQUENCES.items():
        entries = []
        for record in sequence:
            require(record + 10 <= len(program), f"record outside program: {record:#x}")
            entries.append({
                "record": f"0x{record:06x}",
                "assembly": f"0x{u32(program, record + 4):06x}",
                "hurt_selector": program[record + 8],
                "attack_selector": program[record + 9],
            })
        result[name] = entries
    return result


def verify_determinism() -> dict[str, object]:
    primary_files = ("samples.tsv", "player_writes.tsv")
    equipment_files = ("samples.tsv", "player_writes.tsv",
                       "player_global_writes.tsv")
    for filename in primary_files:
        require(digest(PRIMARY / "cold_run_1" / filename) ==
                digest(PRIMARY / "cold_run_2" / filename),
                f"primary cold runs differ: {filename}")
    for filename in equipment_files:
        require(digest(EQUIPMENT / "cold_run_1" / filename) ==
                digest(EQUIPMENT / "cold_run_2" / filename),
                f"equipment cold runs differ: {filename}")
    return {
        "primary_cold_runs_byte_identical": True,
        "equipment_cold_runs_byte_identical": True,
        "sample_frames_each": 3070,
        "primary_files": {name: digest(PRIMARY / "cold_run_1" / name)
                          for name in primary_files},
        "equipment_files": {name: digest(EQUIPMENT / "cold_run_1" / name)
                            for name in equipment_files},
    }


def verify_action_paths() -> dict[str, object]:
    gun = indexed(samples(PRIMARY, "gun_only"))
    special = indexed(samples(PRIMARY, "special_only"))
    movement = indexed(samples(PRIMARY, "movement_attack"))
    reverse = indexed(samples(PRIMARY, "reverse_attack"))
    jump = indexed(samples(JUMP, "jump_only"))
    dash = indexed(samples(JUMP, "dash_right"))
    baseline = indexed(samples(PRIMARY, "cold_run_1"))

    require([gun[f]["p_action"] for f in (4422, 4423)] == [0x1A00, 0x1A02],
            "gun action dispatch drift")
    require(actor_byte(gun[4423], 0xAD) == 1, "gun action flag was not set")
    require([special[f]["p_action"] for f in (4422, 4423, 4435)] ==
            [0x0800, 0x0802, 0x0804], "special action phases drift")
    require(actor_byte(special[4423], 0xAD) == 1 and
            actor_byte(special[4497], 0xAD) == 0,
            "special action-local flag lifecycle drift")
    require([jump[f]["p_action"] for f in (4422, 4424, 4459, 4461, 4462)] ==
            [0x0400, 0x0402, 0x0404, 0x0000, 0x0002],
            "jump dispatch/return drift")
    require((jump[4424]["p_x"], jump[4424]["p_y"], jump[4424]["p_z"]) ==
            (1360, 319, 319) and jump[4440]["p_y"] == 395 and
            (jump[4459]["p_x"], jump[4459]["p_y"], jump[4459]["p_z"]) ==
            (1360, 319, 319), "jump movement arc drift")
    require(dash[4424]["p_action"] == 0x0402 and dash[4433]["p_inner"] == 2,
            "direction+jump or its HIT interruption drift")
    require(movement[4422]["p_action"] == 0x1400 and
            movement[4423]["p_action"] == 0x1402 and
            movement[4424]["p_attack"] == 21,
            "contextual Button-2 dispatch drift")
    require(movement[4433]["p_inner"] == 2 and
            movement[4433]["p_action"] == 0,
            "HIT cancellation drift")
    require(reverse[4423]["p_facing"] == 0 and reverse[4441]["p_facing"] == 0 and
            reverse[4442]["p_facing"] == 1 and reverse[4468]["p_facing"] == 1,
            "facing latch/reversal drift")
    require([baseline[f]["p_attack"] for f in (5190, 5236, 5283, 5329)] ==
            [1, 2, 3, 4], "close-combo selector sequence drift")
    return {
        "idle": {"action_phase": ["0x0000", "0x0002"],
                 "returns_to_control": True},
        "walk": {"action_phase": ["0x0200", "0x0202"],
                 "source": "ORACLE-04 directional traces"},
        "jump": {"input": "Button3 edge", "input_frame": 4420,
                 "action_phase": ["0x0400", "0x0402", "0x0404"],
                 "dispatch_frame": 4422, "control_return_frame": 4462,
                 "world_arc": {"start_y": 319, "apex_y": 395,
                               "return_y": 319, "x_fixed": 1360,
                               "z_fixed": 319}},
        "direction_plus_jump": {"input": "Right+Button3 edge",
                                "action_phase": ["0x0400", "0x0402"],
                                "result": "alternate dash presentation then HIT interruption"},
        "gun": {"input": "Button1 edge", "action_phase": ["0x1a00", "0x1a02"],
                "action_local_flag_offset": "0xad",
                "observed_end": "HIT_INTERRUPTED"},
        "button2_contextual": {
            "input": "Button2 edge", "common_dispatch": "0x0600",
            "context_override": ["0x1400", "0x1402"],
            "observed_attack_selectors": [21, 20],
            "selection_rule": "context/distance dependent; never arbitrary selector cycling",
        },
        "close_button2": {
            "input": "Button2 edges near target",
            "action_phase": ["0x0600", "0x0602", "0x0604", "0x0606", "0x0608"],
            "attack_selectors": [1, 2, 3, 4],
        },
        "special": {"input": "Button1+Button2 edge",
                    "action_phase": ["0x0800", "0x0802", "0x0804"],
                    "attack_selector": 11, "health_cost": 6,
                    "control_return_frame": 4498},
        "hit": {"inner_state": 2, "entry_frame": 4433,
                "clears_action_local_state": True,
                "observed_animation_record": "0x15f054"},
        "ko": {"binding": "data/avsp_hit_ko_writer_set.json",
               "coverage": "prior accepted writer/record boundary; not re-triggered by ORACLE-07"},
    }


def verify_writers() -> dict[str, object]:
    gun = writes(EQUIPMENT, "gun_only")
    special = writes(EQUIPMENT, "special_only")
    close = writes(CLOSE, "close_combo_recovery_repeat")
    movement = writes(PRIMARY, "movement_attack")
    jump = writes(JUMP, "jump_only")
    dash = writes(JUMP, "dash_right")
    expected = [
        (gun, 4421, "06", "01a7ce", "1a00", "ffff"),
        (gun, 4422, "06", "019f4a", "0202", "00ff"),
        (gun, 4422, "ac", "019f54", "0101", "00ff"),
        (special, 4421, "06", "01a89a", "0800", "ffff"),
        (special, 4422, "06", "023154", "0202", "00ff"),
        (special, 4422, "ac", "023158", "0101", "00ff"),
        (special, 4434, "06", "0231f8", "0404", "00ff"),
        (special, 4496, "ac", "01a41c", "0000", "00ff"),
        (close, 5186, "06", "01a6e4", "0600", "ffff"),
        (close, 5187, "06", "02258e", "0202", "00ff"),
        (close, 5205, "82", "0226e0", "1e1e", "ff00"),
        (close, 5206, "82", "01982a", "1d1d", "ff00"),
        (movement, 4421, "06", "01a6e4", "0600", "ffff"),
        (movement, 4422, "06", "022edc", "0202", "00ff"),
        (movement, 4433, "06", "01a988", "0202", "ff00"),
        (movement, 4433, "82", "01a9d2", "0000", "ff00"),
        (jump, 4421, "06", "01a6ba", "0400", "ffff"),
        (jump, 4423, "06", "0233f4", "0202", "00ff"),
        (dash, 4421, "06", "01a6ba", "0400", "ffff"),
    ]
    for rows, frame, offset, pc, data, mask in expected:
        require(has_write(rows, frame=frame, offset=offset, pc=pc,
                          data=data, mask=mask),
                f"missing writer {pc} offset {offset} frame {frame}")
    return {
        "dispatch": {
            "jump": ["0x01a6ba", "0x0233f4"],
            "button2_common": "0x01a6e4",
            "button2_close": "0x02258e",
            "button2_context_override": ["0x01a6f2", "0x022edc"],
            "gun": ["0x01a7ce", "0x019f4a"],
            "special": ["0x01a89a", "0x023154", "0x0231f8"],
        },
        "close_combo": {
            "phase_advance": ["0x0225ea", "0x022708"],
            "finish": ["0x0226d6", "0x0226dc", "0x0226e0"],
            "followup_counter_decrement": "0x01982a",
            "return_low_byte_clear": "0x0198e2",
            "frame_input_counter": "0x01a7e0",
        },
        "contextual_button2_finish": ["0x022f6e", "0x022f74", "0x022f78"],
        "action_local_flag": {"set_gun": "0x019f54",
                              "set_special": "0x023158",
                              "clear": "0x01a41c"},
        "hit_interruption": ["0x01a988", "0x01a98c", "0x01a9ce", "0x01a9d2"],
    }


def verify_combo() -> dict[str, object]:
    baseline = indexed(samples(PRIMARY, "cold_run_1"))
    hold = indexed(samples(CLOSE, "close_combo_hold"))
    startup = indexed(samples(CLOSE, "close_combo_startup_repeat"))
    recovery = indexed(samples(CLOSE, "close_combo_recovery_repeat"))
    delay50 = indexed(samples(CLOSE, "close_combo_delay_50"))
    delay51 = indexed(samples(CLOSE, "close_combo_delay_51"))

    events = []
    for step, (input_frame, start, contact, end, selector, records) in enumerate((
        (5185, 5187, 5190, 5206, 1, ANIMATION_SEQUENCES["close_1"]),
        (5230, 5232, 5236, 5251, 2, ANIMATION_SEQUENCES["close_2"]),
        (5275, 5277, 5283, 5301, 3, ANIMATION_SEQUENCES["close_3"]),
        (5320, 5322, 5329, 5353, 4, ANIMATION_SEQUENCES["close_4"]),
    ), start=1):
        observed = []
        for frame in range(start, end):
            record = int(baseline[frame]["p_anim"])
            if record in records and (not observed or observed[-1] != record):
                observed.append(record)
        require(observed == records, f"close step {step} animation sequence drift")
        require(baseline[contact]["p_attack"] == selector,
                f"close step {step} selector drift")
        events.append({"step": step, "input_frame": input_frame,
                       "action_start_frame": start, "contact_frame": contact,
                       "return_frame": end, "attack_selector": selector,
                       "animation_records": [f"0x{value:06x}" for value in records]})

    require(max(int(row["p_attack"]) for frame, row in hold.items()
                if frame >= 5185) == 1,
            "held Button2 unexpectedly auto-chained")
    require(actor_byte(startup[5198], 0x95) == 0x20 and
            max(int(row["p_attack"]) for frame, row in startup.items()
                if frame >= 5185) == 1,
            "startup repeat unexpectedly chained or was not latched")
    require(recovery[5213]["p_attack"] == 2,
            "recovery edge did not dispatch close step 2")
    require(delay50[5240]["p_attack"] == 1 and delay51[5241]["p_attack"] == 1,
            "expired follow-up did not restart at close step 1")
    require(actor_u16(recovery[5207], 0x82) >> 8 == 29 and
            actor_u16(recovery[5208], 0x82) >> 8 == 28,
            "follow-up counter witness drift")
    return {
        "events": events,
        "state_fields": {
            "completed_step": {"offset": "0x81", "values": [0, 1, 2, 3]},
            "followup_counter": {"offset": "0x82 high", "reset_frames": 30,
                                 "decrement_writer": "0x01982a"},
            "frame_input_counter": {"offset": "0x82 low",
                                    "writer": "0x01a7e0",
                                    "return_clear_writer": "0x0198e2"},
            "buffered_buttons": {"offset": "0x95", "startup_repeat_value": "0x20"},
        },
        "edge_semantics": {
            "held_button": "one action only; no auto-repeat",
            "startup_repeat": "latched at +0x95 but does not cancel, chain, or auto-dispatch",
            "recovery_edge_counter_28": "accepted and dispatched step 2",
            "edge_at_counter_1_or_after_zero": "chain expired; dispatch restarts at step 1",
            "implementation_guard": "require a new Button2 edge while the follow-up counter remains live before its final countdown tick",
        },
    }


def build_report() -> dict[str, object]:
    determinism = verify_determinism()
    action_graph = verify_action_paths()
    writer_map = verify_writers()
    combo = verify_combo()
    source_combat = json.loads(SOURCE_COMBAT.read_text(encoding="utf-8"))
    hud = json.loads(PLAYER_HUD.read_text(encoding="utf-8"))
    program = PROGRAM.read_bytes()
    primary_manifest = manifest(PRIMARY)
    equipment_manifest = manifest(EQUIPMENT)
    close_manifest = manifest(CLOSE)
    jump_manifest = manifest(JUMP)
    require(primary_manifest["mame"] == equipment_manifest["mame"] ==
            close_manifest["mame"] == jump_manifest["mame"],
            "capture MAME identity differs")
    require(primary_manifest["roms"] == equipment_manifest["roms"] ==
            close_manifest["roms"] == jump_manifest["roms"],
            "capture ROM identity differs")
    require(hud["emergency_attack_health_cost"] == 6 and
            hud["meter_cost"] == 40 and hud["weapon_meter_capacity"] == 64,
            "player HUD resource contract drift")

    close_identity = []
    for event in source_combat["events"]:
        close_identity.append({
            "step": event["attack_sequence_step"],
            "contact_frame": event["contact_frame"],
            "attack_selector": event["attack_selector"],
            "animation_record": event["player"]["animation_record"],
            "assembly": event["player"]["assembly"],
            "object_identity_sha256": event["player"]["object_identity_sha256"],
            "tile_identity_sha256": event["player"]["tile_identity_sha256"],
            "tile_codes": event["player"]["tile_codes"],
            "palettes": event["player"]["palettes"],
            "collision": copy.deepcopy(event["collision"]),
            "health_before": event["health_before"],
            "health_after": event["health_after"],
        })

    report: dict[str, object] = {
        "schema": 1,
        "task": "ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT",
        "classification": "MEASURED_MAME_SOURCE_BOUNDED_CONTROLLER_CONTRACT",
        "target": {"set": "avspu", "revision": "USA 940520",
                   "actor_slot": "0xff8380", "character": "Predator Warrior"},
        "scope": "one-player first-live-encounter controller subset; not a complete character move set or legal clean-room opinion",
        "evidence_tier": "MAME_TRACE_PROGRAM_TABLE_AND_FRAME_INDEXED_CAPTURE",
        "saturn_emulator": "UNRUN",
        "physical_saturn": "UNRUN",
        "provenance": {
            "mame": primary_manifest["mame"],
            "nvram_baseline_sha256": primary_manifest["nvram_baseline_sha256"],
            "rom_sha256": {item["name"]: item["sha256"]
                           for item in primary_manifest["roms"]},
            "decrypted_program_sha256": digest(PROGRAM),
            "capture_manifest_sha256": {
                "primary": digest(PRIMARY / "input_manifest.json"),
                "equipment": digest(EQUIPMENT / "input_manifest.json"),
                "close_combo": digest(CLOSE / "input_manifest.json"),
                "jump": digest(JUMP / "input_manifest.json"),
            },
            "source_combat_contract_sha256": digest(SOURCE_COMBAT),
            "oracle04_sha256": digest(ORACLE04),
            "player_hud_capture_sha256": digest(PLAYER_HUD),
            "hit_ko_writer_set_sha256": digest(HIT_KO),
        },
        "declared_capture_mutations": primary_manifest["declared_mutations"] + [
            "equipment/close/jump recaptures also declare class-0x1f actor removal only for isolated_combo variants; those variants do not authorize combo behavior"],
        "determinism": determinism,
        "input_map": {"left": 4, "right": 8, "button1_gun": 16,
                      "button2_attack": 32, "button3_jump": 64,
                      "up_lane": 128, "down_lane": 256,
                      "semantics": "active-high decoded trace word; action dispatch uses new edges"},
        "actor_layout": {
            "active": {"offset": "0x00", "width": 1},
            "class": {"offset": "0x02", "width": 1},
            "state_inner": {"offset": "0x04", "width": 2},
            "action_phase": {"offset": "0x06", "width": 2},
            "facing": {"offset": "0x0f", "width": 1},
            "world_x": {"offset": "0x10", "width": 2, "signed": True},
            "world_y": {"offset": "0x14", "width": 2, "signed": True},
            "world_z": {"offset": "0x18", "width": 2, "signed": True},
            "animation_record": {"offset": "0x1c", "width": 4},
            "animation_timer": {"offset": "0x2a", "width": 2},
            "health": {"offset": "0x40", "width": 2, "signed": True},
            "combo_step": {"offset": "0x81", "width": 1},
            "combo_window_and_frame_counter": {"offset": "0x82", "width": 2},
            "buffered_buttons": {"offset": "0x95", "width": 1},
            "action_local_equipment_word": {"offset": "0xac", "width": 2,
                                            "observed_flag_byte": "0xad"},
        },
        "source_routines": writer_map,
        "action_graph": action_graph,
        "combo_contract": combo,
        "equipment_contract": {
            "finding": "gun and special dispatch set actor byte +0xad to 1 through distinct source writers; common action cleanup clears the containing +0xac word; this is an action-local equipment/resource flag, not permission to infer a visible weapon sprite",
            "gun": {"set_writer": "0x019f54", "observed_value": 1,
                    "resource": {"meter_capacity": 64, "meter_cost": 40,
                                 "recharge_cadence_frames": 3}},
            "special": {"set_writer": "0x023158", "observed_value": 1,
                        "health_cost": 6},
            "cleanup_writer": "0x01a41c",
            "random_selection": False,
        },
        "interruption_cancellation": {
            "gun_by_hit": {"action_before": "0x1a02", "hit_frame": 4433,
                           "result": "inner state 2; action-local fields cleared"},
            "contextual_button2_by_hit": {"action_before": "0x1402",
                                         "hit_frame": 4433,
                                         "result": "inner state 2; action-local fields cleared"},
            "direction_plus_jump_by_hit": {"action_before": "0x0402",
                                          "hit_frame": 4433,
                                          "result": "inner state 2"},
            "startup_repeat": "does not cancel or advance current close action",
            "held_button": "does not auto-repeat",
            "hit_overlap": "player attack can shift/prevent the otherwise expected incoming HIT; context only, not a universal priority rule",
        },
        "facing_and_movement": {
            "action_facing": "latched for the active action; opposite direction does not flip it mid-action",
            "control_return": "facing updates when locomotion resumes; a later action uses the new facing",
            "jump_coordinate_note": "source actor world-y increases from 319 to 395 while airborne and returns to 319; this is not screen-y semantics",
            "directional_signs": "bound by ORACLE-04; screen-space inversion belongs to the later executable specification",
        },
        "presentation_identity": {
            "animation_record_layout": {"assembly_pointer": "record+0x04",
                                        "hurt_selector": "record+0x08",
                                        "attack_selector": "record+0x09"},
            "sequences": animation_contract(program),
            "close_contact_source_bound_identity": close_identity,
        },
        "collision_damage_hit_ko": {
            "close_contacts": "four selector/object/tile/collision/damage events copied by identity from the accepted source-combat contract",
            "player_hit": "ORACLE-07 directly measures HIT cancellation into inner state 2",
            "player_ko": "bound to the accepted HIT/KO writer-set artifact; not re-triggered in this capture set",
            "enemy_hit_ko": "outside ORACLE-07 ownership; preserved from REPAIR-09/ORACLE-05 evidence",
        },
        "negative_controls": {
            "held_input_must_not_auto_chain": True,
            "startup_repeat_must_not_chain": True,
            "expired_combo_window_must_restart_at_step_1": True,
            "recovery_edge_inside_window_must_advance": True,
            "random_selector_cycle_forbidden": True,
            "visible_weapon_inference_from_equipment_flag_forbidden": True,
            "isolated_combo_enemy_removal_cannot_authorize_combo_semantics": True,
        },
        "bounded_findings": {
            "input_edges_action_dispatch_and_return": "MEASURED",
            "close_combo_window_and_step_advance": "MEASURED",
            "equipment_action_flag_writers": "MEASURED_NOT_VISUAL_WEAPON_STATE",
            "animation_record_and_assembly_selection": "MEASURED",
            "movement_and_facing": "MEASURED_BOUNDED",
            "attack_hurt_collision_damage": "SOURCE_BOUND_PRIOR_ACCEPTED_CONTRACT",
            "hit_interruption": "MEASURED",
            "ko": "SOURCE_BOUND_PRIOR_ACCEPTED_WRITER_SET",
            "complete_move_set": "UNKNOWN_OUT_OF_SCOPE",
            "player_rng": "NOT_A_CONTROLLER_AUTHORITY_FOR_ATTACK_SELECTION",
            "multiplayer": "UNKNOWN_OUT_OF_SCOPE",
            "saturn_runtime": "UNRUN",
        },
    }
    validate(report)
    mutation_self_test(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == 1, "ORACLE-07 schema drift")
    require(report["classification"] ==
            "MEASURED_MAME_SOURCE_BOUNDED_CONTROLLER_CONTRACT",
            "ORACLE-07 classification drift")
    require(report["saturn_emulator"] == "UNRUN" and
            report["physical_saturn"] == "UNRUN", "Saturn status overclaim")
    determinism = report["determinism"]
    require(determinism["primary_cold_runs_byte_identical"] is True and
            determinism["equipment_cold_runs_byte_identical"] is True,
            "ORACLE-07 determinism drift")
    graph = report["action_graph"]
    require(graph["close_button2"]["attack_selectors"] == [1, 2, 3, 4],
            "close selector order drift")
    require(graph["button2_contextual"]["selection_rule"].endswith(
        "never arbitrary selector cycling"), "random attack selection admitted")
    combo = report["combo_contract"]
    require([event["contact_frame"] for event in combo["events"]] ==
            [5190, 5236, 5283, 5329], "close contact frames drift")
    require(combo["edge_semantics"]["held_button"].startswith("one action"),
            "held-button negative control drift")
    require(report["equipment_contract"]["random_selection"] is False,
            "equipment randomness admitted")
    require(report["negative_controls"]["visible_weapon_inference_from_equipment_flag_forbidden"] is True,
            "visible-weapon inference admitted")
    identities = report["presentation_identity"]["close_contact_source_bound_identity"]
    require(len(identities) == 4 and
            all(item["object_identity_sha256"] and item["tile_identity_sha256"]
                for item in identities), "presentation identity is vacuous")
    routines = report["source_routines"]
    require(routines["hit_interruption"] ==
            ["0x01a988", "0x01a98c", "0x01a9ce", "0x01a9d2"],
            "HIT cleanup writer set drift")
    findings = report["bounded_findings"]
    require(findings["complete_move_set"] == "UNKNOWN_OUT_OF_SCOPE" and
            findings["multiplayer"] == "UNKNOWN_OUT_OF_SCOPE",
            "bounded scope widened")


def mutation_self_test(report: dict[str, object]) -> None:
    mutations = []
    changed = copy.deepcopy(report)
    changed["determinism"]["primary_cold_runs_byte_identical"] = False
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["action_graph"]["close_button2"]["attack_selectors"] = [4, 3, 2, 1]
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["equipment_contract"]["random_selection"] = True
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["saturn_emulator"] = "PASS"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["presentation_identity"]["close_contact_source_bound_identity"][0]["object_identity_sha256"] = ""
    mutations.append(changed)
    for index, mutant in enumerate(mutations):
        try:
            validate(mutant)
        except ValueError:
            continue
        raise ValueError(f"ORACLE-07 mutation {index} unexpectedly passed")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"ORACLE-07 PASS {OUT.relative_to(ROOT)} sha256={digest(OUT)}")


if __name__ == "__main__":
    main()
