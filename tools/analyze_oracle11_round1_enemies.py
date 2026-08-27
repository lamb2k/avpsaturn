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
                    len(current["mutation_controls"]) == 19,
                    "0x1f: current-state implementation contract drift")
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
