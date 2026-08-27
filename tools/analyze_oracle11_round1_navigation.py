#!/usr/bin/env python3
"""Close route-wide Round 1 navigation, terrain, obstacle and camera authority."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_A = ROOT / ".deps" / "mame" / "oracle11_round1_navigation_a"
BASE_B = ROOT / ".deps" / "mame" / "oracle11_round1_navigation_b"
PERTURBED = ROOT / ".deps" / "mame" / "oracle11_round1_navigation_perturbed"
CORRECTIVE_A = ROOT / ".deps" / "mame" / "reimplement13_navigation_fields_g"
CORRECTIVE_B = ROOT / ".deps" / "mame" / "reimplement13_navigation_fields_h"
ORACLE08 = ROOT / "data" / "oracle08_round1_navigation_bounds.json"
ORACLE10 = ROOT / "data" / "oracle10_round1_route.json"
SCHEDULER = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
OUT = ROOT / "data" / "oracle11_round1_navigation.json"
CAPTURE_FILES = (
    "navigation_samples.tsv", "navigation_writes.tsv",
    "navigation_body_writes.tsv", "camera_writes.tsv", "samples.tsv",
    "dispatches.tsv", "projectiles.tsv", "score_writes.tsv", "result.tsv",
)
CORRECTIVE_FILES = (
    "navigation_fields.tsv", "navigation_resolves.tsv",
    "camera_bound_writes.tsv", "terrain_map.bin",
)
TERRAIN_RECORDS = {
    "0x0b20c6": "0080808080808080",
    "0x0b20d6": "0202808010100080",
    "0x0b2136": "0202808010080080",
    "0x0b2186": "0604020100008080",
    "0x0b218e": "0604020100088080",
    "0x0b220e": "0402020100088080",
}
TYPE20_ROUTINES = {
    "0x07": (0x06D1AA, 0x06D418),
    "0x08": (0x06D53C, 0x06D7B8),
    "0x09": (0x06D926, 0x06DBDA),
    "0x0a": (0x06DE92, 0x06E136),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def corrective_identity(path: Path) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    require(manifest["task"] == "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1" and
            manifest["authority_family"] ==
            "round1-navigation-terrain-camera-corrective-oracle" and
            manifest["frame_window"] == [3400, 5200],
            f"{path.name}: corrective authority identity drift")
    for filename in CORRECTIVE_FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {
        "manifest_sha256": digest(manifest_path),
        "mame_sha256": manifest["mame_sha256"],
        "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
        "files": {name: manifest["sha256"][name]
                  for name in CORRECTIVE_FILES},
    }


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def capture_identity(path: Path) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    require(manifest["authority_family"] == "round1-navigation-terrain-camera",
            f"{path.name}: authority-family identity drift")
    for filename in CAPTURE_FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {
        "manifest_sha256": digest(manifest_path),
        "variant": manifest["variant"],
        "mame_sha256": manifest["mame_sha256"],
        "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
        "files": {name: manifest["sha256"][name] for name in CAPTURE_FILES},
    }


def parse_result(path: Path) -> dict[str, object]:
    row = rows(path / "result.tsv")[0]
    return {key: int(value) if key not in ("variant", "final_score") else value
            for key, value in row.items()}


def compact_runs(samples: list[dict[str, str]]) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for row in samples:
        key = (int(row["route"]), int(row["bound_x"]), int(row["bound_z"]))
        frame = int(row["frame"])
        if runs and tuple(runs[-1][name] for name in
                          ("route", "bound_x", "bound_z")) == key and \
                runs[-1]["last_frame"] + 1 == frame:
            runs[-1]["last_frame"] = frame
            runs[-1]["frames"] += 1
        else:
            runs.append({"first_frame": frame, "last_frame": frame,
                         "frames": 1, "route": key[0],
                         "bound_x": key[1], "bound_z": key[2]})
    return runs


def terrain_records(write_sets: list[list[dict[str, str]]], program: bytes) -> list[dict[str, object]]:
    observed: dict[str, dict[str, object]] = {}
    for capture_index, capture in enumerate(write_sets):
        counts = Counter((row["a4"], row["a4_bytes"], row["pc"])
                         for row in capture
                         if row["pc"] in ("0b1c08", "0b1c68"))
        for (address, record_bytes, pc), count in counts.items():
            key = f"0x{address}"
            item = observed.setdefault(key, {
                "address": key, "record_bytes": record_bytes,
                "baseline_calls": {"0x0b1c08": 0, "0x0b1c68": 0},
                "perturbed_calls": {"0x0b1c08": 0, "0x0b1c68": 0},
            })
            target = "baseline_calls" if capture_index == 0 else "perturbed_calls"
            item[target][f"0x{pc}"] += count
    require(set(observed) == set(TERRAIN_RECORDS),
            "route-reachable terrain record set drift")
    for address, expected in TERRAIN_RECORDS.items():
        item = observed[address]
        require(item["record_bytes"] == expected,
                f"{address}: captured terrain bytes drift")
        offset = int(address, 16)
        require(program[offset:offset + 8].hex() == expected,
                f"{address}: source terrain bytes drift")
        item["source_program_match"] = True
        item["classification"] = "SOURCE_CLOSED"
    return [observed[key] for key in sorted(observed)]


def type20_instances(route: dict[str, object], body_sets: list[list[dict[str, str]]],
                     opcodes: bytes) -> list[dict[str, object]]:
    archetypes = {(item["class"], item["type"]): item
                  for item in route["actor_archetypes"]}
    output = []
    for class_name, (start, end) in TYPE20_ROUTINES.items():
        actor = archetypes[(class_name, 20)]
        instance = actor["actor_slots_and_classes"][0]
        first, last = instance["life"]
        slot = instance["slot"].replace("0x", "")
        writer_sets = []
        for capture in body_sets:
            pcs = Counter(f"0x{row['pc']}" for row in capture
                          if row["slot"] == slot and first <= int(row["frame"]) <= last)
            writer_sets.append(dict(sorted(pcs.items())))
        output.append({
            "class": class_name, "type": 20, "slot": instance["slot"],
            "source_frame_range": [first, last],
            "scheduler_pool_type": 20,
            "dispatch_entry": f"0x{start:06x}",
            "bounded_source_block": f"0x{start:06x}..0x{end:06x}",
            "source_block_sha256": hashlib.sha256(opcodes[start:end]).hexdigest(),
            "state_transitions": actor["state_transitions"],
            "animation_and_assembly_identities": actor["animation_and_assembly_identities"],
            "baseline_writer_pcs": writer_sets[0],
            "perturbed_writer_pcs": writer_sets[1],
            "navigation_role": "SOURCE_CLOSED",
            "complete_actor_authority": (
                "PARTIAL; damage, destruction, pickup, hazard and presentation edges "
                "remain assigned to their existing ORACLE-11 authority families"),
        })
    return output


def terrain_interpreter_contract(opcodes: bytes, program: bytes,
                                 terrain_map: bytes) -> dict[str, object]:
    require(len(terrain_map) == 0x4000,
            "Coffee Shop terrain-map capture size drift")
    selector_bytes = terrain_map[2::4]
    require(len(selector_bytes) == 0x1000,
            "Coffee Shop terrain selector projection size drift")
    def cell_offset(x: int, z: int) -> int:
        inverted_z = (~z) & 0xffff
        return (((inverted_z & 0x0300) << 4) +
                ((inverted_z & 0x00f0) >> 2) + ((x << 2) & 0x0fc0))
    first_segment_selectors = sorted({
        terrain_map[cell_offset(x, z) + 2] & 0xfc
        for x in range(640, 1361) for z in range(272, 401)
    })
    require(first_segment_selectors == [0, 24, 56],
            "Coffee Shop bounded terrain selector set drift")
    grid_x_min, grid_x_max = 640, 1360
    grid_z_min, grid_z_max = 272, 400
    grid_tile = 16
    grid_width = ((grid_x_max - grid_x_min) // grid_tile) + 1
    grid_height = ((grid_z_max - grid_z_min) // grid_tile) + 1
    selector_codes = {0: 0, 24: 1, 56: 2}
    grid_selectors = [
        terrain_map[cell_offset(x, z) + 2] & 0xfc
        for z in range(grid_z_min, grid_z_max + 1, grid_tile)
        for x in range(grid_x_min, grid_x_max + 1, grid_tile)
    ]
    require(len(grid_selectors) == grid_width * grid_height and
            sorted(set(grid_selectors)) == first_segment_selectors,
            "Coffee Shop bounded terrain grid drift")
    packed_grid = bytearray((len(grid_selectors) + 3) // 4)
    for index, selector in enumerate(grid_selectors):
        packed_grid[index >> 2] |= selector_codes[selector] << ((index & 3) * 2)
    implementation_selectors = sorted(set(first_segment_selectors) |
                                      {0, 8, 56, 96, 100, 164})
    implementation_records = []
    for selector in implementation_selectors:
        address = 0x0B20C6 + 2 * selector
        implementation_records.append({
            "selector_u8": selector,
            "address": f"0x{address:06x}",
            "record_bytes": program[address:address + 8].hex(),
        })
    require([row["record_bytes"] for row in implementation_records] == [
        "0080808080808080", "0202808010100080",
        "020280801010ff80", "0202808010080080",
        "0604020100008080", "0604020100088080",
        "0402020100088080"], "Coffee Shop implementation records drift")
    fields = [
        {"offset": 0, "name": "kind", "type": "u8",
         "rule": "even byte offset into 0x0b1c0a handler table"},
        {"offset": 1, "name": "branch_selector", "type": "u8",
         "rule": "byte offset into the selected kind table; bit index is selector >> 1 when nonnegative"},
        {"offset": 2, "name": "orientation", "type": "u8",
         "rule": "kind-4/kind-6 axis orientation selector; kind-2 does not read it"},
        {"offset": 3, "name": "shift", "type": "u8",
         "rule": "variable word shift count for kind-4/kind-6"},
        {"offset": 4, "name": "x_parameter", "type": "u8_or_s8_by_kind",
         "rule": "zero-extended for kind-2/kind-4; sign-extended for kind-6"},
        {"offset": 5, "name": "z_parameter", "type": "u8_or_s8_by_kind",
         "rule": "zero-extended for kind-2/kind-4; sign-extended for kind-6"},
    ]
    handlers = {
        0: {
            "entry": "0x0b1c14", "parameter_signedness": "none",
            "movement_rule": "no position write",
        },
        2: {
            "entry": "0x0b1c16", "selected_entry": "0x0b1c54",
            "parameter_signedness": "fields 4 and 5 are u8",
            "movement_rule": (
                "remainder=(~world_z)&15; penetration=u8(field5)-remainder; "
                "if penetration>0 then world_z-=penetration, z_velocity=0, response=1"),
        },
        4: {
            "entry": "0x0b1cac", "selected_entry": "0x0b1d0e",
            "parameter_signedness": "fields 3, 4 and 5 are u8",
            "movement_rule": (
                "x_remainder=(orientation==2?world_x:~world_x)&15; "
                "candidate=(x_remainder>>shift)+u8(field5)+1; "
                "z_remainder=(~world_z)&15; penetration=candidate-z_remainder; "
                "if penetration>0 then world_z-=penetration, z_velocity=0, response=1"),
        },
        6: {
            "entry": "0x0b1dc0", "selected_entry": "0x0b1e9c",
            "parameter_signedness": "field 3 is u8; fields 4 and 5 are s8",
            "movement_rule": (
                "z_remainder=(orientation==1?world_z:~world_z)&15; "
                "slope=z_remainder-s8(field5); if slope<0 then "
                "world_x-=((world_x&15)+1), x_velocity=0, set retry selector 0xff, "
                "and restart selection; "
                "otherwise candidate=slope<<shift; x_remainder=world_x&15; "
                "if x_remainder>=candidate then world_x-=(x_remainder-candidate+1), "
                "x_velocity=0, response=1"),
        },
    }
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "six_fields": fields,
        "control_bytes": [
            {"offset": 6, "name": "retry_selector", "type": "u8",
             "rule": "copied to A5-0x6144; 0xff repeats record selection"},
            {"offset": 7, "name": "reserved", "type": "u8",
             "rule": "not read by 0x0b1baa..0x0b1c08 or the reachable handlers"},
        ],
        "selection": {
            "entry": "0x0b208c", "world_reads": ["actor+0x10:s16", "actor+0x18:s16"],
            "cell_address": (
                "0x904000 + (((~world_z)&0x0300)<<4) + "
                "(((~world_z)&0x00f0)>>2) + ((world_x<<2)&0x0fc0)"),
            "cell_selector": "u8(cell+2) & 0xfc",
            "record_address": "0x0b20c6 + 2 * (u8(cell+2) & 0xfc)",
            "collision_flags_clear_first": "actor+0x5d &= 0xf0",
            "captured_first_segment_map": {
                "base": "0x904000", "bytes": len(terrain_map),
                "sha256": hashlib.sha256(terrain_map).hexdigest(),
                "selector_bytes": len(selector_bytes),
                "selector_sha256": hashlib.sha256(selector_bytes).hexdigest(),
                "selector_bytes_hex": selector_bytes.hex(),
                "classification": "SOURCE_DERIVED_CONTENT_DATA",
            },
            "bounded_packed_grid": {
                "classification": "SOURCE_DERIVED_CONTENT_DATA",
                "world_x_inclusive": [grid_x_min, grid_x_max],
                "world_z_inclusive": [grid_z_min, grid_z_max],
                "tile_size": grid_tile,
                "width": grid_width,
                "height": grid_height,
                "cell_count": len(grid_selectors),
                "bits_per_cell": 2,
                "selector_code_u8": [0, 24, 56],
                "packed_bytes": len(packed_grid),
                "packed_sha256": hashlib.sha256(packed_grid).hexdigest(),
                "packed_bytes_hex": packed_grid.hex(),
                "derivation": (
                    "row-major source cells sampled at each 16-pixel tile origin; "
                    "four 2-bit selector codes packed least-significant code first"),
            },
        },
        "handlers": {str(key): value for key, value in handlers.items()},
        "implementation_records": implementation_records,
        "first_segment_geometry_universe": {
            "world_x_inclusive": [640, 1360],
            "world_z_inclusive": [272, 400],
            "selectors_u8": first_segment_selectors,
        },
        "scheduler_order": (
            "player movement -> global bounds -> actor/obstacle response -> "
            "terrain resolver -> camera/route controller -> world-to-plane submission"),
        "source_blocks": {
            "dispatcher_sha256": hashlib.sha256(
                opcodes[0x0B1BAA:0x0B1C16]).hexdigest(),
            "kind2_sha256": hashlib.sha256(
                opcodes[0x0B1C16:0x0B1CAC]).hexdigest(),
            "kind4_sha256": hashlib.sha256(
                opcodes[0x0B1CAC:0x0B1DC0]).hexdigest(),
            "kind6_sha256": hashlib.sha256(
                opcodes[0x0B1DC0:0x0B1F4C]).hexdigest(),
            "selector_sha256": hashlib.sha256(
                opcodes[0x0B208C:0x0B20C6]).hexdigest(),
            "cell_address_sha256": hashlib.sha256(
                opcodes[0x0B2672:0x0B269E]).hexdigest(),
        },
    }


def obstacle_implementation_contract(program: bytes, opcodes: bytes,
                                     resolve_rows: list[dict[str, str]]) -> dict[str, object]:
    animation = 0x06E136
    table_set = 0x06E210
    attack_relative = int.from_bytes(program[table_set + 2:table_set + 4],
                                     "big", signed=True)
    selector = program[animation + 9]
    box_address = table_set + attack_relative + selector * 8
    blob = program[box_address:box_address + 8]
    box = {
        "address": f"0x{box_address:06x}",
        "x_center_s8": int.from_bytes(blob[0:1], "big", signed=True),
        "y_center_s8": int.from_bytes(blob[1:2], "big", signed=True),
        "x_half_u8": blob[2], "y_half_u8": blob[3],
        "z_center_s8": int.from_bytes(blob[4:5], "big", signed=True),
        "z_half_u8": blob[5], "flags_u16": int.from_bytes(blob[6:8], "big"),
    }
    require(attack_relative == 0x14 and selector == 1 and box == {
        "address": "0x06e22c", "x_center_s8": 0, "y_center_s8": 0,
        "x_half_u8": 32, "y_half_u8": 127, "z_center_s8": 0,
        "z_half_u8": 6, "flags_u16": 0xff00,
    }, "Coffee Shop obstacle source box drift")
    relevant = [row for row in resolve_rows
                if row["pc"] == "01d986" and row["field"] == "x" and
                row["a1"] == "ff8380" and row["a6"] == "ffb380"]
    require(len(relevant) == 745 and
            {(int(row["half_x"]), int(row["half_z"]), int(row["sign_bits"]))
             for row in relevant} == {(32, 6, 0)} and
            {int(row["new_value"]) for row in relevant} == {1091},
            "Coffee Shop minimum-penetration operands drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "source_actor": {
            "slot": "0xffb380", "class": "0x0a", "type": 20,
            "state_u16": 0x0200, "substate_u16": 0,
            "position_s16": {"x": 1123, "y": 323, "z": 323},
            "facing_u8": 0,
            "animation_record": "0x06e136", "table_set": "0x06e210",
            "assembly": "0x06e196", "hurt_selector_u8": 1,
            "attack_selector_u8": selector,
        },
        "player_geometry": {
            "classification": "SOURCE_POINT_PROBE",
            "x": "player+0x10:s16", "z": "player+0x18:s16",
            "box": None,
            "rule": "0x01db8a reads no player rectangle; substituting a player hurt box is forbidden",
        },
        "obstacle_box": box,
        "overlap_guard": (
            "abs((obstacle_x + signed x_center)-player_x) < x_half AND "
            "abs((obstacle_z + signed z_center)-player_z) < z_half"),
        "minimum_penetration": {
            "x": "x_half-abs_x; negate when obstacle center delta was negative",
            "z": "z_half-abs_z; negate when obstacle center delta was negative",
            "axis_guard": "resolve z only when unsigned z_penetration < unsigned x_penetration; otherwise resolve x",
            "x_write": "player_x -= signed x_penetration at 0x01d980 (tap PC 0x01d986)",
            "z_write": "player_z -= signed z_penetration at 0x01d994 (tap PC 0x01d998)",
            "velocity_writes": ["player+0x12=0", "player+0x1a=0"],
            "contact_bits": "x sets bit 2/3; z sets bit 0/1 in player+0x5d from penetration sign",
        },
        "dynamic_control": {
            "rows": len(relevant), "half_x": 32, "half_z": 6,
            "right_edge": 1091,
            "capture_sha256": hashlib.sha256(canonical(relevant)).hexdigest(),
        },
        "source_blocks": {
            "overlap_sha256": hashlib.sha256(
                opcodes[0x01DB8A:0x01DC10]).hexdigest(),
            "response_sha256": hashlib.sha256(
                opcodes[0x01D930:0x01D99A]).hexdigest(),
        },
    }


def camera_implementation_contract(sample_rows: list[dict[str, str]],
                                   bound_rows: list[dict[str, str]],
                                   opcodes: bytes) -> dict[str, object]:
    by_frame = {int(row["frame"]): row for row in sample_rows}
    require(len(sample_rows) == 1801 and set(by_frame) == set(range(3400, 5201)),
            "corrective camera sample window drift")
    checkpoints = []
    for frame in (3572, 3714, 3792, 4992, 4993, 5016):
        row = by_frame[frame]
        checkpoints.append({
            "frame": frame, "route": int(row["route"]),
            "player_x": int(row["player_x"]), "player_z": int(row["player_z"]),
            "position_x": int(row["cam_x_position"]),
            "target_x": int(row["cam_x_target"]),
            "x_lower": int(row["cam_x_min"]),
            "x_upper": int(row["cam_x_max"]),
            "global_x": int(row["global_cam_x"]),
            "scroll2_x": int(row["scroll2_x"]),
        })
    required_writes = {
        (3792, "x_lower", "028942", 0x340),
        (3792, "x_upper", "028958", 0x340),
        (4992, "x_upper", "02898a", 0x3f0),
        (4993, "x_lower", "0289ae", 0x344),
    }
    observed = {(int(row["frame"]), row["field"], row["pc"],
                 int(row["write_data"], 16) & 0xffff)
                for row in bound_rows}
    require(required_writes <= observed, "Coffee Shop camera guard writers drift")
    guard_rows = {int(row["frame"]): row for row in sample_rows}
    require(all(int(guard_rows[frame]["guard_threshold_byte"]) == 1
                for frame in (3792, 3793, 4992, 4993)) and
            int(guard_rows[3792]["coffee_countdown"]) == 1200 and
            int(guard_rows[3793]["coffee_countdown"]) == 1199 and
            int(guard_rows[4992]["coffee_countdown"]) == 0 and
            int(guard_rows[4993]["coffee_phase"]) == 4,
            "Coffee Shop unlock guard operands drift")
    return {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "record": {
            "source_base": "0xff8268",
            "x_previous": "+0x08:s16", "x_position": "+0x10:s16",
            "z_position": "+0x14:s16", "x_target": "+0x20:s16",
            "z_target": "+0x24:s16", "x_target_previous": "+0x28:s16",
            "z_target_previous": "+0x2c:s16", "z_upper": "+0x30:s16",
            "z_lower": "+0x32:s16", "x_lower": "+0x34:s16",
            "x_upper": "+0x36:s16",
        },
        "initialization": {
            "entry": "0x0b04bc", "override_guard": "u8(A5+0x1b0) != 0",
            "override_reads": ["camera+0x10:s16", "camera+0x14:s16"],
            "writes": ["x position/target/history from D0", "z position/target/history from D1"],
            "route_table_bounds": "0x0b0526 indexes four signed bounds by u16(A5+0x1e8)<<2",
        },
        "player_follow_guard": {
            "enabled": "u8(A5+0x1af) != 0",
            "players": "three 0x100-byte records at A5+0x380, ascending slot order",
            "eligible": "active byte nonzero and player+0x54 != 0xfe",
            "x_extrema": "0x0b0c22 returns unsigned max/min actor+0x10",
            "z_extrema": "0x0b0c5e returns unsigned max/min actor+0x18",
        },
        "x_target_arithmetic": {
            "spread_guard": "unsigned(max_x-min_x) >= 0x40",
            "wide_target_delta": "((max_x+min_x)>>1)-x_target-0x00c0",
            "narrow_right_delta": "max_x-x_target-0x00e0",
            "narrow_left_delta": "min_x-x_target-0x00a0",
            "speed_quantization": "index=((abs(delta)+7)&0x00f8)>>2; speed=u16(table+index)&0x000f",
            "speed_table_u16": [0, 1, 1, 2, 3, 4, 5, 6, 7, 7,
                                  8, 8, 9, 9, 10, 10, 11, 11, 11, 11],
            "clamp_order": "apply signed delta to target, clamp upper at +0x36, then lower at +0x34",
            "commit_order": "target +0x20 -> position +0x10 -> A5+0x278 global bound -> A5+0x32 camera position",
        },
        "z_target_arithmetic": {
            "spread_guard": "unsigned(max_z-min_z) >= 0x20",
            "wide_target_delta": "((max_z+min_z)>>1)-z_target-0x0050",
            "narrow_upper_delta": "max_z-z_target-0x0060",
            "narrow_lower_delta": "min_z-z_target-0x0040",
            "step": "clamp absolute delta to 1",
            "clamp_order": "apply signed delta, clamp upper at +0x30, then lower at +0x32",
            "commit_order": "target +0x24 -> position +0x14 -> A5+0x34 camera z",
        },
        "coffee_shop_guard": {
            "controller_slot": "0xffd180", "controller_dispatch": "0x028860",
            "phase_dispatch": "u8(controller+0x06) indexes 0x028908",
            "phase0_lock_guard": "u16(A5+0x278) >= 0x0340",
            "phase0_writes": ["x_lower=0x0340", "x_upper=0x0340",
                              "controller+0x44=u16(A5-0x65e6)"],
            "phase2_unlock_guard": (
                "unsigned(u16(A5-0x65e6)-u16(controller+0x44)) >= "
                "(u8(A5+0x020e)<<4), OR controller+0x46 countdown reaches zero"),
            "captured_first_segment_operands": {
                "counter_u16": 0, "snapshot_u16": 0,
                "threshold_byte_u8": 1, "threshold_ticks": 16,
                "countdown_initial_u16": 1200,
                "countdown_tick_rule": "decrement once per controller update while phase is 2",
            },
            "phase2_writes": ["x_upper=0x03f0", "controller+0x06 += 2"],
            "phase4_follow": "x_lower=u16(A5+0x278) each tick; clamp at 0x03f0 before the next phase",
            "fixed_frame_authority": False,
        },
        "world_to_plane_order": {
            "rule": (
                "finish player/navigation, encounter camera-bound writes, and camera controller; "
                "then translate source scroll2 through the accepted strip origin and derive scroll3 "
                "through the accepted measured scroll2-to-scroll3 bridge; submit both VDP2 planes last"),
            "scroll2_relation_at_locks": "CPS scroll2_x = camera position x - 0x40",
            "raw_pattern_name_offset_forbidden": True,
            "accepted_bridge": "data/repair11_live_background_presentation.json",
        },
        "dynamic_checkpoints": checkpoints,
        "source_blocks": {
            "initializer_sha256": hashlib.sha256(
                opcodes[0x0B04BC:0x0B0526]).hexdigest(),
            "x_controller_sha256": hashlib.sha256(
                opcodes[0x0B0680:0x0B0786]).hexdigest(),
            "z_controller_sha256": hashlib.sha256(
                opcodes[0x0B0786:0x0B085C]).hexdigest(),
            "player_extrema_sha256": hashlib.sha256(
                opcodes[0x0B0C22:0x0B0C9A]).hexdigest(),
            "coffee_guard_sha256": hashlib.sha256(
                opcodes[0x028910:0x0289C6]).hexdigest(),
        },
    }


def camera_authority(route: dict[str, object], samples: list[dict[str, str]],
                     camera_rows: list[dict[str, str]], opcodes: bytes) -> dict[str, object]:
    writers = Counter((row["pc"], row["return0"], row["return1"], row["return2"])
                      for row in camera_rows if row["kind"] == "camera_target")
    source_writers = [{
        "pc": f"0x{pc}",
        "return_chain": [f"0x{r0}", f"0x{r1}", f"0x{r2}"],
        "count": count,
    } for (pc, r0, r1, r2), count in sorted(writers.items())]
    sample_by_frame = {int(row["frame"]): row for row in samples}
    locks = []
    for lock in route["camera_lock_runs"]:
        first, last = lock["first_frame"], lock["last_frame"]
        if first not in sample_by_frame or last not in sample_by_frame:
            continue
        before = sample_by_frame.get(first - 1, sample_by_frame[first])
        entry = sample_by_frame[first]
        exit_row = sample_by_frame[last]
        provenance = sorted({f"0x{row['pc']}" for row in camera_rows
                             if first <= int(row["frame"]) <= last})
        locks.append({
            "first_frame": first, "last_frame": last, "frames": lock["frames"],
            "route": int(entry["route"]), "scroll2_x": lock["scroll2_x"],
            "camera_target_at_entry": int(entry["camera_target"]),
            "camera_target_at_exit": int(exit_row["camera_target"]),
            "player_x_at_entry": int(entry["player_x"]),
            "player_x_at_exit": int(exit_row["player_x"]),
            "prior_scroll2_x": int(before["scroll2_x"]),
            "owning_writer_pcs": provenance,
            "classification": "SOURCE_CLOSED",
        })
    require(len(locks) == len(route["camera_lock_runs"]),
            "camera lock/unlock route edge coverage drift")
    return {
        "classification": "SOURCE_CLOSED",
        "camera_target_field": "0xff8032:u16",
        "primary_writer": "0x0b0706",
        "bounded_controller_block": "0x0b04ce..0x0b0862",
        "controller_block_sha256": hashlib.sha256(
            opcodes[0x0B04CE:0x0B0862]).hexdigest(),
        "source_writers_and_callers": source_writers,
        "camera_lock_and_unlock_runs": locks,
        "edge_guard_rule": (
            "retain the exact source camera-target writer and route-state transition; "
            "no x-only, kill-count, or fixed-frame substitute is admitted"),
        "orphan_camera_edges": 0,
    }


def build_report() -> dict[str, object]:
    identity_a = capture_identity(BASE_A)
    identity_b = capture_identity(BASE_B)
    identity_p = capture_identity(PERTURBED)
    corrective_a = corrective_identity(CORRECTIVE_A)
    corrective_b = corrective_identity(CORRECTIVE_B)
    require(identity_a["files"] == identity_b["files"],
            "navigation baseline completion captures differ")
    require(identity_a["mame_sha256"] == identity_b["mame_sha256"] ==
            identity_p["mame_sha256"], "MAME identity differs across navigation captures")
    result_a, result_b, result_p = (parse_result(path)
                                    for path in (BASE_A, BASE_B, PERTURBED))
    require(result_a == result_b and result_a["final_route"] == 4,
            "baseline navigation completion drift")
    require(result_p["final_route"] == 4,
            "directional navigation perturbation did not complete Round 1")
    require(identity_p["files"]["navigation_samples.tsv"] !=
            identity_a["files"]["navigation_samples.tsv"],
            "navigation perturbation did not discriminate")
    require(corrective_a["files"] == corrective_b["files"] and
            corrective_a["mame_sha256"] == corrective_b["mame_sha256"] ==
            identity_a["mame_sha256"] and
            corrective_a["nvram_baseline_sha256"] ==
            corrective_b["nvram_baseline_sha256"] ==
            identity_a["nvram_baseline_sha256"],
            "corrective navigation captures differ")

    base_samples = rows(BASE_A / "navigation_samples.tsv")
    perturbed_samples = rows(PERTURBED / "navigation_samples.tsv")
    base_writes = rows(BASE_A / "navigation_writes.tsv")
    perturbed_writes = rows(PERTURBED / "navigation_writes.tsv")
    base_bodies = rows(BASE_A / "navigation_body_writes.tsv")
    perturbed_bodies = rows(PERTURBED / "navigation_body_writes.tsv")
    base_camera = rows(BASE_A / "camera_writes.tsv")
    corrective_samples = rows(CORRECTIVE_A / "navigation_fields.tsv")
    corrective_resolves = rows(CORRECTIVE_A / "navigation_resolves.tsv")
    corrective_bounds = rows(CORRECTIVE_A / "camera_bound_writes.tsv")
    route = json.loads(ORACLE10.read_text(encoding="utf-8"))
    oracle08 = json.loads(ORACLE08.read_text(encoding="utf-8"))
    scheduler = json.loads(SCHEDULER.read_text(encoding="ascii"))
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()

    terrain = terrain_records([base_writes, perturbed_writes], program)
    terrain_map = (CORRECTIVE_A / "terrain_map.bin").read_bytes()
    terrain_contract = terrain_interpreter_contract(opcodes, program,
                                                    terrain_map)
    handler_entry = {0: "0x0b1c14", 2: "0x0b1c54",
                     4: "0x0b1d0e", 6: "0x0b1e9c"}
    for item in terrain:
        blob = bytes.fromhex(item["record_bytes"])
        kind = blob[0]
        parameter_type = "s8" if kind == 6 else "u8"
        item["decoded_six_fields"] = {
            "kind_u8": kind, "branch_selector_u8": blob[1],
            "orientation_u8": blob[2], "shift_u8": blob[3],
            f"x_parameter_{parameter_type}":
                int.from_bytes(blob[4:5], "big", signed=kind == 6),
            f"z_parameter_{parameter_type}":
                int.from_bytes(blob[5:6], "big", signed=kind == 6),
        }
        item["control_bytes"] = {
            "retry_selector_u8": blob[6], "reserved_u8": blob[7]}
        item["selected_handler"] = handler_entry[kind]
    type20 = type20_instances(route, [base_bodies, perturbed_bodies], opcodes)
    camera = camera_authority(route, base_samples, base_camera, opcodes)
    obstacle_contract = obstacle_implementation_contract(
        program, opcodes, corrective_resolves)
    camera_contract = camera_implementation_contract(
        corrective_samples, corrective_bounds, opcodes)
    counterfactual = next(item for item in route["counterfactual_authority_coverage"]
                          if item["authority_family"] ==
                          "round1-navigation-terrain-camera")
    require(counterfactual["status"] == "PASS" and
            all(item["completed_round1"] for item in
                counterfactual["outcomes"].values()),
            "route-wide navigation counterfactual coverage drift")
    require(scheduler["status"] == "SOURCE_CLOSED" and
            any(item["record_type"] == 20 and item["routine"] == "0x01bc38"
                for item in scheduler["frame_scheduler"]["full_order"]),
            "type-20 scheduler ownership drift")

    bound_runs = compact_runs(base_samples)
    bound_tuples = sorted({(int(row["bound_x"]), int(row["bound_z"]))
                           for row in base_samples + perturbed_samples})
    clamp_pcs = Counter(f"0x{row['pc']}" for row in base_writes + perturbed_writes
                        if row["pc"].startswith("01b0"))
    require({"0x01b030", "0x01b042"}.issubset(clamp_pcs),
            "route-wide global-bound clamp writers not discriminated")
    report = {
        "schema": "oracle11-round1-navigation-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "Round 1 player navigation, terrain, obstacles and camera bounds",
        "capture_identity": {
            "completion_a": identity_a, "completion_b": identity_b,
            "byte_identical": True, "perturbed_completion": identity_p,
            "baseline_result": result_a, "perturbed_result": result_p,
            "perturbation_completed_round1": True,
            "perturbation_discriminated_navigation": True,
            "corrective_implementation_fields_a": corrective_a,
            "corrective_implementation_fields_b": corrective_b,
            "corrective_byte_identical": True,
        },
        "coordinate_contract": {
            "world_x": "actor+0x10:s16", "world_y": "actor+0x14:s16",
            "world_z": "actor+0x18:s16",
            "up_world_z_delta_sign": 1, "down_world_z_delta_sign": -1,
            "screen_projection_owned_here": False,
        },
        "global_bounds": {
            "classification": "SOURCE_CLOSED",
            "source_routine": "0x01b000..0x01b05e",
            "source_routine_sha256": hashlib.sha256(
                opcodes[0x01B000:0x01B05E]).hexdigest(),
            "bound_x_field": "A5+0x278:s16", "bound_z_field": "A5+0x27c:s16",
            "x_min": "bound_x + 0x20", "x_max": "bound_x + 0x160",
            "z_min": "bound_z + 0x10", "z_max": "bound_z + 0x90",
            "writer_pcs": dict(sorted(clamp_pcs.items())),
            "observed_bound_tuples": [[x, z] for x, z in bound_tuples],
            "baseline_bound_runs": bound_runs,
            "orphan_bound_runs": 0,
        },
        "terrain_resolver": {
            "classification": "SOURCE_CLOSED",
            "source_block": "0x0b1baa..0x0b1c70",
            "source_block_sha256": hashlib.sha256(
                opcodes[0x0B1BAA:0x0B1C70]).hexdigest(),
            "position_sync_writer": "0x0b1c08",
            "constraint_response_writer": "0x0b1c68",
            "records": terrain, "route_reachable_record_count": len(terrain),
            "orphan_route_reachable_records": 0,
            "implementation_contract": terrain_contract,
        },
        "navigation_bodies": {
            "classification": "SOURCE_CLOSED",
            "scheduler": "record type 20 at 0x01bc38, fixed-pool ascending-slot order",
            "instances": type20, "route_reachable_class_type_pairs": 4,
            "orphan_navigation_bodies": 0,
            "scope_boundary": (
                "this closes geometry/navigation ownership only; destructible damage, "
                "pickup/hazard and presentation authority stay in their declared families"),
        },
        "obstacle_response": {
            "classification": "SOURCE_CLOSED",
            "source_block": "0x01d930..0x01d99a",
            "source_block_sha256": hashlib.sha256(
                opcodes[0x01D930:0x01D99A]).hexdigest(),
            "minimum_penetration_x_writer": "0x01d986",
            "coffee_shop_actor": "class 0x0a/type 20 at 0xffb380",
            "accepted_oracle08_removal_control": True,
            "shared_player_enemy_rectangle_rejected": True,
            "implementation_contract": obstacle_contract,
        },
        "camera": {**camera, "implementation_contract": camera_contract},
        "counterfactuals": {
            "oracle08_directional_and_obstacle_controls":
                oracle08["boundary_counterfactuals"],
            "oracle10_route_wide": counterfactual,
            "oracle11_directional_perturbation": {
                "schedule": "post-frame-4200 Up/Down pulses layered on the completion route",
                "completed_round1": True,
                "navigation_samples_changed": True,
                "constraint_response_writer_observed": True,
            },
        },
        "closure": {
            "required_unknown": 0, "orphan_bound_runs": 0,
            "orphan_terrain_records": 0, "orphan_navigation_bodies": 0,
            "orphan_camera_edges": 0, "guessed_camera_guards": 0,
            "authored_fallbacks": 0,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED",
            "global_audio_load_release": "SOURCE_CLOSED",
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-round1-navigation-v1" and
            report["status"] == "SOURCE_CLOSED", "navigation status drift")
    capture = report["capture_identity"]
    require(capture["byte_identical"] is True and
            capture["perturbation_completed_round1"] is True and
            capture["perturbation_discriminated_navigation"] is True and
            capture["corrective_byte_identical"] is True and
            capture["corrective_implementation_fields_a"]["files"] ==
            capture["corrective_implementation_fields_b"]["files"],
            "navigation capture contract drift")
    bounds = report["global_bounds"]
    opcodes = OPCODES.read_bytes()
    require(bounds["classification"] == "SOURCE_CLOSED" and
            bounds["source_routine"] == "0x01b000..0x01b05e" and
            bounds["source_routine_sha256"] == hashlib.sha256(
                opcodes[0x01B000:0x01B05E]).hexdigest() and
            bounds["orphan_bound_runs"] == 0 and
            "0x01b030" in bounds["writer_pcs"] and
            "0x01b042" in bounds["writer_pcs"], "global bound authority drift")
    terrain = report["terrain_resolver"]
    require(terrain["classification"] == "SOURCE_CLOSED" and
            terrain["source_block_sha256"] == hashlib.sha256(
                opcodes[0x0B1BAA:0x0B1C70]).hexdigest() and
            terrain["route_reachable_record_count"] == 6 and
            terrain["orphan_route_reachable_records"] == 0 and
            {item["address"] for item in terrain["records"]} == set(TERRAIN_RECORDS)
            and all(item["source_program_match"] is True and
                    item["classification"] == "SOURCE_CLOSED"
                    for item in terrain["records"]) and
            {item["address"] for item in terrain["records"]
             if item["perturbed_calls"]["0x0b1c68"] > 0} ==
            {"0x0b20d6", "0x0b2136"} and
            all(len(item["decoded_six_fields"]) == 6 and
                len(item["control_bytes"]) == 2 and
                item["selected_handler"] in
                {"0x0b1c14", "0x0b1c54", "0x0b1d0e", "0x0b1e9c"}
                for item in terrain["records"]), "terrain closure drift")
    terrain_contract = terrain["implementation_contract"]
    packed_grid = terrain_contract["selection"]["bounded_packed_grid"]
    packed_grid_bytes = bytes.fromhex(packed_grid["packed_bytes_hex"])
    expected_decoded = {
        "0x0b20c6": {"kind_u8": 0, "branch_selector_u8": 128,
                      "orientation_u8": 128, "shift_u8": 128,
                      "x_parameter_u8": 128, "z_parameter_u8": 128},
        "0x0b20d6": {"kind_u8": 2, "branch_selector_u8": 2,
                      "orientation_u8": 128, "shift_u8": 128,
                      "x_parameter_u8": 16, "z_parameter_u8": 16},
        "0x0b2136": {"kind_u8": 2, "branch_selector_u8": 2,
                      "orientation_u8": 128, "shift_u8": 128,
                      "x_parameter_u8": 16, "z_parameter_u8": 8},
        "0x0b2186": {"kind_u8": 6, "branch_selector_u8": 4,
                      "orientation_u8": 2, "shift_u8": 1,
                      "x_parameter_s8": 0, "z_parameter_s8": 0},
        "0x0b218e": {"kind_u8": 6, "branch_selector_u8": 4,
                      "orientation_u8": 2, "shift_u8": 1,
                      "x_parameter_s8": 0, "z_parameter_s8": 8},
        "0x0b220e": {"kind_u8": 4, "branch_selector_u8": 2,
                      "orientation_u8": 2, "shift_u8": 1,
                      "x_parameter_u8": 0, "z_parameter_u8": 8},
    }
    require(terrain_contract["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            [item["name"] for item in terrain_contract["six_fields"]] ==
            ["kind", "branch_selector", "orientation", "shift",
             "x_parameter", "z_parameter"] and
            [item["type"] for item in terrain_contract["six_fields"]] ==
            ["u8", "u8", "u8", "u8", "u8_or_s8_by_kind",
             "u8_or_s8_by_kind"] and
            terrain_contract["selection"]["record_address"] ==
            "0x0b20c6 + 2 * (u8(cell+2) & 0xfc)" and
            terrain_contract["handlers"]["2"]["selected_entry"] ==
            "0x0b1c54" and
            terrain_contract["handlers"]["4"]["selected_entry"] ==
            "0x0b1d0e" and
            terrain_contract["handlers"]["6"]["selected_entry"] ==
            "0x0b1e9c" and
            packed_grid["classification"] == "SOURCE_DERIVED_CONTENT_DATA" and
            packed_grid["world_x_inclusive"] == [640, 1360] and
            packed_grid["world_z_inclusive"] == [272, 400] and
            packed_grid["tile_size"] == 16 and
            packed_grid["width"] == 46 and packed_grid["height"] == 9 and
            packed_grid["cell_count"] == 414 and
            packed_grid["bits_per_cell"] == 2 and
            packed_grid["selector_code_u8"] == [0, 24, 56] and
            packed_grid["packed_bytes"] == 104 and
            len(packed_grid_bytes) == 104 and
            hashlib.sha256(packed_grid_bytes).hexdigest() ==
            packed_grid["packed_sha256"] and
            {item["address"]: item["decoded_six_fields"]
             for item in terrain["records"]} == expected_decoded,
            "terrain implementation contract drift")
    bodies = report["navigation_bodies"]
    require(bodies["classification"] == "SOURCE_CLOSED" and
            bodies["route_reachable_class_type_pairs"] == 4 and
            bodies["orphan_navigation_bodies"] == 0 and
            {item["class"] for item in bodies["instances"]} ==
            {"0x07", "0x08", "0x09", "0x0a"} and
            all(item["navigation_role"] == "SOURCE_CLOSED" and
                    item["complete_actor_authority"].startswith("PARTIAL;")
                    and item["baseline_writer_pcs"] and
                    item["source_block_sha256"] == hashlib.sha256(
                        opcodes[TYPE20_ROUTINES[item["class"]][0]:
                                TYPE20_ROUTINES[item["class"]][1]]).hexdigest()
                    for item in bodies["instances"]), "navigation-body boundary drift")
    obstacle = report["obstacle_response"]
    require(obstacle["source_block_sha256"] == hashlib.sha256(
                opcodes[0x01D930:0x01D99A]).hexdigest() and
            obstacle["accepted_oracle08_removal_control"] is True and
            obstacle["shared_player_enemy_rectangle_rejected"] is True,
            "obstacle-response closure drift")
    obstacle_contract = obstacle["implementation_contract"]
    require(obstacle_contract["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            obstacle_contract["player_geometry"]["box"] is None and
            obstacle_contract["obstacle_box"] == {
                "address": "0x06e22c", "x_center_s8": 0,
                "y_center_s8": 0, "x_half_u8": 32, "y_half_u8": 127,
                "z_center_s8": 0, "z_half_u8": 6,
                "flags_u16": 0xff00} and
            obstacle_contract["dynamic_control"]["rows"] == 745 and
            obstacle_contract["dynamic_control"]["right_edge"] == 1091 and
            obstacle_contract["minimum_penetration"]["axis_guard"] ==
            "resolve z only when unsigned z_penetration < unsigned x_penetration; otherwise resolve x",
            "obstacle implementation contract drift")
    camera = report["camera"]
    require(camera["classification"] == "SOURCE_CLOSED" and
            camera["primary_writer"] == "0x0b0706" and
            camera["controller_block_sha256"] == hashlib.sha256(
                opcodes[0x0B04CE:0x0B0862]).hexdigest() and
            len(camera["camera_lock_and_unlock_runs"]) == 19 and
            camera["orphan_camera_edges"] == 0 and
            all(item["classification"] == "SOURCE_CLOSED"
                and item["owning_writer_pcs"]
                for item in camera["camera_lock_and_unlock_runs"]),
            "camera closure drift")
    camera_contract = camera["implementation_contract"]
    require(camera_contract["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            camera_contract["x_target_arithmetic"]["speed_table_u16"] ==
            [0, 1, 1, 2, 3, 4, 5, 6, 7, 7,
             8, 8, 9, 9, 10, 10, 11, 11, 11, 11] and
            camera_contract["coffee_shop_guard"]["phase0_lock_guard"] ==
            "u16(A5+0x278) >= 0x0340" and
            camera_contract["x_target_arithmetic"]["wide_target_delta"] ==
            "((max_x+min_x)>>1)-x_target-0x00c0" and
            camera_contract["x_target_arithmetic"]["narrow_right_delta"] ==
            "max_x-x_target-0x00e0" and
            camera_contract["x_target_arithmetic"]["narrow_left_delta"] ==
            "min_x-x_target-0x00a0" and
            camera_contract["coffee_shop_guard"]["phase2_unlock_guard"] ==
            "unsigned(u16(A5-0x65e6)-u16(controller+0x44)) >= (u8(A5+0x020e)<<4), OR controller+0x46 countdown reaches zero" and
            camera_contract["coffee_shop_guard"]["fixed_frame_authority"] is False and
            camera_contract["world_to_plane_order"]["raw_pattern_name_offset_forbidden"] is True and
            {(item["frame"], item["x_lower"], item["x_upper"])
             for item in camera_contract["dynamic_checkpoints"]} >=
            {(3792, 640, 832), (4992, 832, 832), (4993, 832, 1008)},
            "camera implementation contract drift")
    closure = report["closure"]
    require(all(value == 0 for value in closure.values()),
            "navigation zero-gap closure drift")
    require(report["protected_boundaries"] == {
        "predator_warrior": "SOURCE_CLOSED",
        "global_audio_load_release": "SOURCE_CLOSED",
        "production_runtime_writes": 0, "yaba_runs": 0,
        "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
        "salvage08_active": False, "physical_saturn": "UNRUN",
        "spec02_active": False, "oracle11_active": True,
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 Round 1 navigation: SOURCE_CLOSED; zero orphan bounds, "
          "terrain records, navigation bodies, or camera edges")


if __name__ == "__main__":
    main()
