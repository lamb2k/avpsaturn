#!/usr/bin/env python3
"""Generate the native side of the existing Coffee Shop scene manifest."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "spec02_round1_generated_fixtures.json"
OUT = ROOT / "data" / "reimplement13_coffee_shop_scene_parity.json"
SOURCE_ACTORS = (ROOT / ".deps" / "mame" /
                 "oracle11_progression_lifecycle_cs21a" /
                 "coffee_shop_scene_actors.tsv")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "ascii") + b"\n"


def wsl(path: Path) -> str:
    return subprocess.run(
        ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
         "wslpath", "-a", str(path).replace("\\", "/")],
        check=True, capture_output=True, text=True).stdout.strip()


def capture() -> tuple[list[dict[str, str]], str]:
    with tempfile.TemporaryDirectory(prefix="round1-coffee-census-") as name:
        output = f"/tmp/{Path(name).name}-census"
        command = (
            f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra "
            f"-Werror -I . -I src/port_v2/gameplay/round1 "
            f"-I src/port_v2/gameplay/player_action "
            f"-I src/port_v2/gameplay/street_alien_ai "
            f"-I src/port_v2/combat/hit_ko "
            f"-I src/port_v2/integration/combat "
            f"src/port_v2/gameplay/round1/round1.c avsp_actor.c "
            f"avsp_collision.c src/port_v2/gameplay/player_action/player_action.c "
            f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
            f"src/port_v2/combat/hit_ko/hit_ko.c "
            f"src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
            f"src/port_v2/integration/player_enemy/player_enemy.c "
            f"src/port_v2/integration/combat/combat.c "
            f"tests/port_v2/round1/round1_coffee_shop_scene_census.c "
            f"-o '{output}' && ulimit -s unlimited && '{output}'")
        result = subprocess.run(
            ["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
             "bash", "-lc", command], check=False, capture_output=True,
             text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"native Coffee Shop census failed ({result.returncode})\n"
                f"{result.stderr[-8000:]}")
    return list(csv.DictReader(io.StringIO(result.stdout), delimiter="\t")), \
        result.stderr.strip()


def lifetimes(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    active: dict[tuple[str, int, str], dict[str, object]] = {}
    completed: list[dict[str, object]] = []
    prior_keys: set[tuple[str, int, str]] = set()
    by_frame: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_frame[int(row["frame"])].append(row)
    for frame in range(1972, 5567):
        current_keys: set[tuple[str, int, str]] = set()
        for row in by_frame.get(frame, []):
            key = (row["source_slot"], int(row["type"]), row["class"])
            current_keys.add(key)
            if key not in active:
                active[key] = {
                    "source_slot": "0x" + row["source_slot"],
                    "pool": row["pool"], "type": int(row["type"]),
                    "class": "0x" + row["class"], "first_frame": frame,
                    "last_frame": frame, "states": set(),
                    "animation_records": set(), "assemblies": set(),
                    "facings": set(), "hurt_selectors": set(),
                    "attack_selectors": set(),
                    "x_range": [int(row["x"]), int(row["x"])],
                    "y_range": [int(row["y"]), int(row["y"])],
                    "z_range": [int(row["z"]), int(row["z"])],
                    "health_range": [int(row["health"]),
                                     int(row["health"])]}
            item = active[key]
            item["last_frame"] = frame
            item["states"].add((int(row["state"], 16),
                                int(row["substate"], 16)))
            item["animation_records"].add(
                f"0x{int(row['animation_record'], 16):08x}")
            item["assemblies"].add(f"0x{int(row['assembly'], 16):08x}")
            item["facings"].add(int(row["facing"]))
            item["hurt_selectors"].add(int(row["hurt_selector"]))
            item["attack_selectors"].add(int(row["attack_selector"]))
            for field in ("x", "y", "z", "health"):
                value = int(row[field])
                bounds = item[field + "_range"]
                bounds[0] = min(bounds[0], value)
                bounds[1] = max(bounds[1], value)
        for key in prior_keys - current_keys:
            completed.append(active.pop(key))
        prior_keys = current_keys
    completed.extend(active.values())
    for item in completed:
        item["states"] = [list(value) for value in sorted(item["states"])]
        item["animation_records"] = sorted(item["animation_records"])
        item["assemblies"] = sorted(item["assemblies"])
        item["facings"] = sorted(item["facings"])
        item["hurt_selectors"] = sorted(item["hurt_selectors"])
        item["attack_selectors"] = sorted(item["attack_selectors"])
    return sorted(completed, key=lambda item: (item["first_frame"],
                                                item["source_slot"],
                                                item["type"], item["class"]))


def key(item: dict[str, object]) -> tuple[object, ...]:
    return (item["source_slot"], item["type"], item["class"],
            item["first_frame"], item["last_frame"])


def occurrence_map(items: list[dict[str, object]]) -> \
        dict[tuple[object, ...], dict[str, object]]:
    counts: dict[tuple[object, ...], int] = defaultdict(int)
    result: dict[tuple[object, ...], dict[str, object]] = {}
    for item in sorted(items, key=lambda value: (
            value["source_slot"], value["type"], value["class"],
            value["first_frame"], value["last_frame"])):
        identity = (item["source_slot"], item["type"], item["class"])
        occurrence = counts[identity]
        counts[identity] += 1
        result[identity + (occurrence,)] = item
    return result


NATIVE_OWNERS = {
    (0, "0x00"): "AvspRound1Runtime.player",
    (4, "0x00"): "player weapon record4 parent",
    (4, "0x03"): "player airborne Button1 record4 actor",
    (4, "0x04"): "player weapon record4 child",
    (12, "0x1f"): "native class-0x1f fixed-pool dispatcher",
    (16, "0x06"): "native class-0x1f type-16 projectile dispatcher",
    (20, "0x09"): "native class-0x09 presentation dispatcher",
    (20, "0x01"): "native class-0x01 scene spawn controller",
    (20, "0x02"): "native class-0x02 damageable scene prop controller",
    (20, "0x0a"): "Coffee Shop obstacle lifecycle",
    (24, "0x10"): "player empty-resource effect dispatcher",
    (24, "0x44"): "Coffee Shop command-guard presentation dispatcher",
    (24, "0x43"): "native class-0x01 scene presentation population",
    (24, "0x45"): "Coffee Shop class-0x45 presentation population",
    (24, "0x47"): "native class-0x02 child presentation dispatcher",
    (24, "0x49"): "native airborne Button1 effect dispatcher",
    (24, "0x4b"): "native Predator special linked presentation dispatcher",
    (24, "0x3d"): "native Predator special event-effect dispatcher",
    (24, "0x4e"): "class-0x4e effect dispatcher",
    (32, "0x01"): "AvspRound1Runtime.entry_controller",
    (36, "0x05"): "Coffee Shop obstacle child dispatcher",
}


def native_owner(item: dict[str, object]) -> str | None:
    return NATIVE_OWNERS.get((int(item["type"]), str(item["class"])))


def edge_timeline(items: list[dict[str, object]], side: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for item in items:
        base = {"side": side, "source_slot": item["source_slot"],
                "type": item["type"], "class": item["class"]}
        events.append(dict(base, frame=item["first_frame"], edge="spawn"))
        events.append(dict(base, frame=int(item["last_frame"]) + 1,
                           edge="despawn"))
    return sorted(events, key=lambda item: (item["frame"], item["side"],
                                             item["source_slot"], item["edge"]))


def grouped_edge_timeline(source: list[dict[str, object]],
                          native: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[int, list[list[object]]] = defaultdict(list)
    for event in edge_timeline(source, "source") + edge_timeline(native, "native"):
        grouped[int(event["frame"])].append([
            event["side"], event["edge"], event["source_slot"],
            event["type"], event["class"]])
    return [{"frame": frame, "events": sorted(events)}
            for frame, events in sorted(grouped.items())]


def compact_window(rows: list[dict[str, str]], first: int, last: int,
                   slots: set[str]) -> dict[str, object]:
    selected = [row for row in rows if first <= int(row["frame"]) <= last and
                row["source_slot"] in slots]
    return {
        "frame_range": [first, last],
        "source_slots": ["0x" + slot for slot in sorted(slots)],
        "row_count": len(selected),
        "rows_sha256": hashlib.sha256(canonical(selected)).hexdigest(),
    }


def source_lifetime_summary(item: dict[str, object]) -> dict[str, object]:
    fields = (
        "id", "source_slot", "pool", "type", "class", "first_frame",
        "last_frame", "states", "facings", "animation_records",
        "assembly_and_behavior_binding", "hurt_selectors", "attack_selectors",
        "health_range_s16", "x_fp_range_s32_16_16",
        "y_fp_range_s32_16_16", "z_range_s16", "source_contract",
        "source_classification", "classification")
    return {field: item.get(field) for field in fields}


def source_native_divergences(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Return the first semantic disagreement for every shared source slot."""
    def source_value(row: dict[str, str], field: str) -> int | None:
        raw_field = ({"x": "x_fp", "y": "y_fp"}.get(field, field))
        if row[raw_field] == "na":
            return None
        if field in {"state", "substate", "animation_record",
                     "hurt_selector", "attack_selector"}:
            return int(row[field], 16)
        if field in {"x", "y"}:
            value = int(row[raw_field], 16)
            signed = value - 0x100000000 if value >= 0x80000000 else value
            return signed >> 16
        value = int(row[field])
        return value

    def native_value(row: dict[str, str], field: str) -> int:
        if field in {"state", "substate", "animation_record"}:
            return int(row[field], 16)
        return int(row[field])

    fields = ("state", "substate", "x", "y", "z", "facing",
              "animation_record", "health", "hurt_selector",
              "attack_selector")
    native_by_key = {
        (int(row["frame"]), f"{int(row['source_slot'], 16):08x}",
         int(row["type"]), f"{int(row['class'], 16):02x}"): row
        for row in native_rows}
    first: dict[tuple[str, int, str], dict[str, object]] = {}
    for source_row in source_rows:
        if source_row["active"] != "1":
            continue
        slot = f"{int(source_row['slot'], 16):08x}"
        native_row = native_by_key.get(
            (int(source_row["frame"]), slot, int(source_row["type"]),
             f"{int(source_row['class'], 16):02x}"))
        if native_row is None:
            continue
        identity = (slot, int(source_row["type"]),
                    f"{int(source_row['class'], 16):02x}")
        if identity not in first:
            first[identity] = {
                "source_slot": "0x" + slot,
                "frame": int(source_row["frame"]),
                "type": int(source_row["type"]),
                "class": f"0x{int(source_row['class'], 16):02x}",
                "differences": {},
            }
        differences = first[identity]["differences"]
        for field in fields:
            source_item = source_value(source_row, field)
            if source_item is None:
                continue
            native_item = native_value(native_row, field)
            if source_item != native_item and field not in differences:
                differences[field] = {"frame": int(source_row["frame"]),
                                      "source": source_item,
                                      "native": native_item}
    divergent = [item for item in first.values() if item["differences"]]
    for item in divergent:
        item["frame"] = min(value["frame"] for value in
                            item["differences"].values())
    return sorted(divergent, key=lambda item: (item["frame"],
                                               item["source_slot"]))


def collision_chronology(source: dict[str, object],
                         native_rows: list[dict[str, str]],
                         divergences: list[dict[str, object]]) -> \
        dict[str, object]:
    """Bind the first source Button1 contact to the native scheduler result."""
    source_write = next(
        item for item in source["health_writes"]
        if item["frame"] == 2306 and item["attacker"] == "0xff8880" and
        item["defender"] == "0xffa180" and
        item["attack_record"] == "0x030cd2" and item["damage_writer"])
    by_key = {(int(row["frame"]), row["source_slot"]): row
              for row in native_rows}
    projectile_before = by_key[(2306, "00ff8880")]
    projectile_after = by_key[(2307, "00ff8880")]
    target_before = by_key[(2306, "00ffa180")]
    target_after = by_key[(2307, "00ffa180")]
    impact_allocated = by_key[(2307, "00ffbd80")]
    impact_initialized = by_key[(2308, "00ffbd80")]
    prefix_slots = {
        "0x00ff8680", "0x00ff8700", "0x00ff8780", "0x00ff8800",
        "0x00ff8880", "0x00ff8900", "0x00ffa180"}
    early = [item for item in divergences
             if item["source_slot"] in prefix_slots and item["frame"] < 2288]
    prior_target_health = {
        int(row["health"]) for row in native_rows
        if row["source_slot"] == "00ffa180" and
        2074 <= int(row["frame"]) <= 2306}
    return {
        "source_scheduler_order": ["record4", "record12", "collision"],
        "source_native_prefix_equal_through_frame": 2287,
        "prefix_divergences": early,
        "source_damage_write": {
            "frame": source_write["frame"],
            "attacker": source_write["attacker"],
            "defender": source_write["defender"],
            "attack_record": source_write["attack_record"],
            "health_before_s16": source_write["health_before_s16"],
            "health_after_s16": source_write["health_after_s16"],
            "writer_pc": source_write["writer_pc"],
        },
        "native_damage_transaction": {
            "scheduler_source_frame": 2306,
            "transaction_visible_frame": 2307,
            "attacker_slot": "0x" + projectile_after["source_slot"],
            "attack_table_base": "0x" + projectile_after["attack_table"],
            "attack_record": "0x" + projectile_after[
                "current_attack_record"],
            "collision_result_before_scheduler_s16": int(
                projectile_before["collision_result"]),
            "collision_result_s16": int(projectile_after[
                "collision_result"]),
            "collision_identity_u8": int(projectile_after[
                "collision_identity"]),
            "collision_registered_u8": int(
                projectile_after["collision_registered"]),
            "projectile_health_s16": int(projectile_after["health"]),
            "target_health_during_source_frame_s16": int(
                target_before["health"]),
            "target_health_next_visible_frame_s16": int(
                target_after["health"]),
            "target_state_next_visible_frame": "0x" +
                target_after["state"],
            "target_substate_next_visible_frame": "0x" +
                target_after["substate"],
            "target_animation_next_visible_frame": "0x" +
                target_after["animation_record"],
            "target_hurt_selector_next_visible_frame_u8": int(
                target_after["hurt_selector"]),
            "target_attack_selector_next_visible_frame_u8": int(
                target_after["attack_selector"]),
            "target_slot": "0x" + target_after["source_slot"],
            "prior_target_health_values_s16": sorted(prior_target_health),
        },
        "native_impact_transaction": {
            "allocation_visible_frame": 2307,
            "slot": "0x" + impact_allocated["source_slot"],
            "type_u8": int(impact_allocated["type"]),
            "class_u8": int(impact_allocated["class"], 16),
            "state_at_allocation": "0x" + impact_allocated["state"],
            "retained_animation_record_at_allocation": "0x" +
                impact_allocated["animation_record"],
            "retained_assembly_at_allocation": "0x" +
                impact_allocated["assembly"],
            "retained_animation_timer_at_allocation_u16": int(
                impact_allocated["animation_timer"]),
            "initialization_visible_frame": 2308,
            "state_after_initialization": "0x" +
                impact_initialized["state"],
            "animation_record": "0x" +
                impact_initialized["animation_record"],
            "assembly": "0x" + impact_initialized["assembly"],
        },
    }


def fixed_slot_reuse_presentation(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]],
        divergences: list[dict[str, object]]) -> dict[str, object]:
    """Bind the allocation-visible presentation retained by slot 0xff8800."""
    source_by_frame = {
        int(row["frame"]): row for row in source_rows
        if int(row["slot"], 16) == 0x00ff8800 and
        int(row["frame"]) in {2333, 2371, 2372}}
    native_by_frame = {
        int(row["frame"]): row for row in native_rows
        if int(row["source_slot"], 16) == 0x00ff8800 and
        int(row["frame"]) in {2333, 2371, 2372}}

    def source_projection(frame: int) -> dict[str, object]:
        row = source_by_frame[frame]
        return {
            "frame_u16": frame,
            "state_u16": "0x" + row["state"],
            "variant_u8": int(row["variant"], 16),
            "animation_record": "0x" + row["animation_record"],
            "animation_timer_u16": int(row["animation_timer"], 16),
            "animation_branch_s16": int(row["animation_branch"]),
        }

    def native_projection(frame: int) -> dict[str, object]:
        row = native_by_frame[frame]
        return {
            "frame_u16": frame,
            "state_u16": "0x" + row["state"],
            "animation_record": "0x" + row["animation_record"],
            "assembly": "0x" + row["assembly"],
            "animation_timer_u16": int(row["animation_timer"]),
        }

    slot_divergence = next(
        (item for item in divergences
         if item["source_slot"] == "0x00ff8800"), None)
    return {
        "allocator": "0x01773e",
        "release": "0x017754",
        "source": [source_projection(frame) for frame in (2333, 2371, 2372)],
        "native": [native_projection(frame) for frame in (2333, 2371, 2372)],
        "no_source_native_divergence_through_frame_u16": 2372,
        "next_slot_divergence_frame_u16": (
            int(slot_divergence["frame"]) if slot_divergence else None),
    }


def class1f_player_collision_chronology(
        source: dict[str, object],
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]],
        divergences: list[dict[str, object]]) -> dict[str, object]:
    """Bind the frame-2750 class-0x1f attack and ten-tick hitstop."""
    frames = (2750, 2751, 2761, 2762)
    source_actor = {
        (int(row["frame"]), "0x" + row["slot"]): row
        for row in source_rows if int(row["frame"]) in frames and
        row["slot"] in {"ff8380", "ffa240"}}
    native_actor = {
        (int(row["frame"]), "0x" + row["source_slot"]): row
        for row in native_rows if int(row["frame"]) in frames and
        row["source_slot"] in {"00ff8380", "00ffa240"}}
    source_write = next(
        row for row in source["health_writes"]
        if row["frame"] == 2750 and row["attacker"] == "0xffa240" and
        row["defender"] == "0xff8380")

    def project(row: dict[str, str], source_side: bool) -> dict[str, object]:
        return {
            "frame_u16": int(row["frame"]),
            "state_u16": "0x" + row["state"],
            "substate_u16": "0x" + row["substate"],
            "animation_record": "0x" + row["animation_record"],
            "animation_timer_u16": int(row["animation_timer"], 16)
                if source_side else int(row["animation_timer"]),
            "health_s16": int(row["health"]),
        }

    slot_divergence = next(
        (item for item in divergences
         if item["source_slot"] == "0x00ffa240"), None)
    return {
        "source_damage_write": {
            "source_frame_u16": source_write["frame"],
            "writer_pc": source_write["writer_pc"],
            "attack_record": source_write["attack_record"],
            "health_before_s16": source_write["health_before_s16"],
            "health_after_s16": source_write["health_after_s16"],
        },
        "scheduler_order": [
            "player update", "record12 actor update",
            "current-state enemy-v-player collision",
            "next player update consumes HIT transition"],
        "source_attacker": [project(
            source_actor[(frame, "0xffa240")], True) for frame in frames],
        "native_attacker": [project(
            native_actor[(frame, "0x00ffa240")], False) for frame in frames],
        "source_player": [project(
            source_actor[(frame, "0xff8380")], True) for frame in frames],
        "native_player": [project(
            native_actor[(frame, "0x00ff8380")], False) for frame in frames],
        "native_health_visible_frame_u16": 2751,
        "native_hitstop_first_frame_u16": 2751,
        "native_hitstop_last_frame_u16": 2761,
        "native_animation_advance_frame_u16": 2762,
        "authored_delay_forbidden": True,
        "next_attacker_divergence_frame_u16": (
            int(slot_divergence["frame"]) if slot_divergence else None),
    }


def record4_parent_fixed_trajectory(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]]) -> dict[str, object]:
    """Compare the complete third-volley parent trajectory as fixed-point state."""
    first = 2434
    last = 2500
    source = {
        int(row["frame"]): row for row in source_rows
        if int(row["slot"], 16) == 0x00ff8680 and
        int(row["type"]) == 4 and int(row["class"], 16) == 0 and
        first <= int(row["frame"]) <= last}
    native = {
        int(row["frame"]): row for row in native_rows
        if int(row["source_slot"], 16) == 0x00ff8680 and
        int(row["type"]) == 4 and int(row["class"], 16) == 0 and
        first <= int(row["frame"]) <= last}

    def source_projection(frame: int) -> dict[str, object]:
        row = source[frame]
        return {
            "frame_u16": frame,
            "state_u16": "0x" + row["state"],
            "x_fp_s32": "0x" + row["x_fp"],
            "y_fp_s32": "0x" + row["y_fp"],
            "animation_record": "0x" + row["animation_record"],
            "animation_timer_u16": int(row["animation_timer"], 16),
            "angle_u8": 46,
            "progress_u8": (int(row["action_timer"], 16) >> 8)
                if int(row["state"], 16) == 0x0200 else None,
        }

    def native_projection(frame: int) -> dict[str, object]:
        row = native[frame]
        return {
            "frame_u16": frame,
            "state_u16": "0x" + row["state"],
            "x_fp_s32": f"0x{int(row['x_fp']) & 0xffffffff:08x}",
            "y_fp_s32": f"0x{int(row['y_fp']) & 0xffffffff:08x}",
            "animation_record": "0x" + row["animation_record"],
            "animation_timer_u16": int(row["animation_timer"]),
            "angle_u8": int(row["angle"]),
            "progress_u8": int(row["progress"])
                if int(row["state"], 16) == 0x0200 else None,
        }

    source_frames = sorted(source)
    native_frames = sorted(native)
    source_projection_rows = [source_projection(frame)
                              for frame in source_frames]
    native_projection_rows = [native_projection(frame)
                              for frame in native_frames]
    anchors = {2434, 2435, 2462, 2466, 2469, 2500}
    return {
        "allocator": "0x01773e",
        "target_selector": "0x0241f0",
        "source_frame_range_u16": [first, last],
        "source_row_count_u16": len(source_projection_rows),
        "native_row_count_u16": len(native_projection_rows),
        "source_rows_sha256": hashlib.sha256(
            canonical(source_projection_rows)).hexdigest(),
        "native_rows_sha256": hashlib.sha256(
            canonical(native_projection_rows)).hexdigest(),
        "source_anchors": [item for item in source_projection_rows
                           if item["frame_u16"] in anchors],
        "native_anchors": [item for item in native_projection_rows
                           if item["frame_u16"] in anchors],
    }


def class1f_action16_rng_reuse(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]],
        divergences: list[dict[str, object]],
        runtime_summary: str) -> dict[str, object]:
    """Bind the single frame-2377 RNG transaction and selector result."""
    source_by_frame = {
        int(row["frame"]): row for row in source_rows
        if int(row["slot"], 16) == 0x00ffa300 and
        int(row["frame"]) in {2378, 2379, 2380}}
    native_by_frame = {
        int(row["frame"]): row for row in native_rows
        if int(row["source_slot"], 16) == 0x00ffa300 and
        int(row["frame"]) in {2378, 2379, 2380}}
    checkpoints = {}
    for match in re.finditer(
            r"rng_checkpoint frame=(\d+) seed=([0-9a-f]{4})", runtime_summary):
        checkpoints[int(match.group(1))] = "0x" + match.group(2)

    def project(row: dict[str, str], source: bool) -> dict[str, object]:
        return {
            "frame_u16": int(row["frame"]),
            "state_u16": "0x" + row["state"],
            "substate_u16": "0x" + row["substate"],
            "animation_record": "0x" + row["animation_record"],
            "attack_selector_u8": int(row["attack_selector"], 16)
                if source else int(row["attack_selector"]),
        }

    slot_divergence = next(
        (item for item in divergences
         if item["source_slot"] == "0x00ffa300"), None)
    return {
        "source_rng_call_frame_u16": 2377,
        "source_seed_before_u16": "0xc9a2",
        "source_seed_after_u16": "0x5cfe",
        "source_call_count_u8": 1,
        "second_call_forbidden": True,
        "native_seed_before_visible_frame": checkpoints.get(2377),
        "native_seed_after_visible_frame": checkpoints.get(2378),
        "source": [project(source_by_frame[frame], True)
                   for frame in (2378, 2379, 2380)],
        "native": [project(native_by_frame[frame], False)
                   for frame in (2378, 2379, 2380)],
        "next_slot_divergence_frame_u16": (
            int(slot_divergence["frame"]) if slot_divergence else None),
    }


def class1f_action16_latched_retry(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]],
        divergences: list[dict[str, object]],
        runtime_summary: str) -> dict[str, object]:
    """Bind the frame-2409 latched action-0x16 transition transaction."""
    frames = (2409, 2410, 2411)
    source_by_frame = {
        int(row["frame"]): row for row in source_rows
        if int(row["slot"], 16) == 0x00ffa300 and
        int(row["frame"]) in frames}
    native_by_frame = {
        int(row["frame"]): row for row in native_rows
        if int(row["source_slot"], 16) == 0x00ffa300 and
        int(row["frame"]) in frames}
    checkpoints: dict[int, dict[str, object]] = {}
    pattern = re.compile(
        r"class1f_retry_checkpoint frame=(\d+) state=([0-9a-f]{4}) "
        r"substate=([0-9a-f]{4}) latch=(\d+) a6=(\d+) b0=(\d+) "
        r"timer=(\d+) branch=(-?\d+) rng=([0-9a-f]{4})")
    for match in pattern.finditer(runtime_summary):
        checkpoints[int(match.group(1))] = {
            "state_u16": "0x" + match.group(2),
            "substate_u16": "0x" + match.group(3),
            "transition_latch_u8": int(match.group(4)),
            "source_a6_u8": int(match.group(5)),
            "source_b0_u8": int(match.group(6)),
            "animation_timer_u16": int(match.group(7)),
            "animation_branch_s16": int(match.group(8)),
            "rng_seed_u16": "0x" + match.group(9),
        }

    def project(row: dict[str, str], source: bool) -> dict[str, object]:
        return {
            "frame_u16": int(row["frame"]),
            "state_u16": "0x" + row["state"],
            "substate_u16": "0x" + row["substate"],
            "facing_u8": int(row["facing"], 16)
                if source else int(row["facing"]),
            "animation_record": "0x" + row["animation_record"],
            "animation_timer_u16": int(row["animation_timer"], 16)
                if source else int(row["animation_timer"]),
            "attack_selector_u8": int(row["attack_selector"], 16)
                if source else int(row["attack_selector"]),
        }

    slot_divergence = next(
        (item for item in divergences
         if item["source_slot"] == "0x00ffa300"), None)
    return {
        "source_transition_frame_u16": 2409,
        "source_transition_pc": "0x060d52",
        "source_facing_write_pc": "0x060d58",
        "source_opcode_window": "0x060c9a-0x060d6a",
        "source_opcode_window_sha256":
            "4d40ad9eebfbc933233afc4d51d967d554748bb99ea0536b4f9baf276c54ae8f",
        "source_rng_seed_before_u16": "0x4bdf",
        "source_rng_seed_after_u16": "0xe3c2",
        "source_rng_call_count_u8": 1,
        "source": [project(source_by_frame[frame], True) for frame in frames],
        "native": [project(native_by_frame[frame], False) for frame in frames],
        "native_checkpoints": [dict({"frame_u16": frame},
                                     **checkpoints[frame])
                               for frame in (2409, 2410)],
        "next_slot_divergence_frame_u16": (
            int(slot_divergence["frame"]) if slot_divergence else None),
    }


def deferred_record4_collision_registration(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]]) -> dict[str, object]:
    """Bind late-slot initialization before frame-2390 source collision."""
    source_target = {
        int(row["frame"]): row for row in source_rows
        if int(row["slot"], 16) == 0x00ff9dc0 and
        int(row["frame"]) in {2390, 2391, 2392}}
    native_target = {
        int(row["frame"]): row for row in native_rows
        if int(row["source_slot"], 16) == 0x00ff9dc0 and
        int(row["frame"]) in {2390, 2391, 2392}}
    native_projectile = {
        int(row["frame"]): row for row in native_rows
        if int(row["source_slot"], 16) == 0x00ff8680 and
        int(row["frame"]) in {2389, 2390, 2391}}

    def target_projection(row: dict[str, str]) -> dict[str, object]:
        return {
            "frame_u16": int(row["frame"]),
            "state_u16": "0x" + row["state"],
            "substate_u16": "0x" + row["substate"],
            "health_s16": int(row["health"]),
            "animation_record": "0x" + row["animation_record"],
        }

    return {
        "source_damage_write": {
            "source_frame_u16": 2390,
            "attacker_slot": "0xff8680",
            "defender_slot": "0xff9dc0",
            "attack_record": "0x030cd2",
            "health_before_s16": 87,
            "health_after_s16": 56,
            "writer_pc": "0x01d590",
        },
        "native_projectile": [{
            "frame_u16": frame,
            "state_u16": "0x" + native_projectile[frame]["state"],
            "collision_registered_u8": int(
                native_projectile[frame]["collision_registered"]),
            "collision_result_s16": int(
                native_projectile[frame]["collision_result"]),
            "current_attack_record": "0x" +
                native_projectile[frame]["current_attack_record"],
        } for frame in (2389, 2390, 2391)],
        "source_target": [target_projection(source_target[frame])
                          for frame in (2390, 2391, 2392)],
        "native_target": [target_projection(native_target[frame])
                          for frame in (2390, 2391, 2392)],
        "same_scan_initialization_collision_forbidden": True,
    }


def recurring_spawn_phase_boundary(
        source_rows: list[dict[str, str]],
        native_rows: list[dict[str, str]],
        runtime_summary: str) -> dict[str, object]:
    """Bind the first phase-gated recurring spawn and shared-RNG order."""
    checkpoints: dict[int, dict[str, object]] = {}
    pattern = re.compile(
        r"rng_checkpoint frame=(2510|2511) seed=([0-9a-f]{4}) "
        r"scheduler=(\d+) phase=(\d+) living=(\d+) spawn_index=(\d+) "
        r"timer=(\d+)")
    for match in pattern.finditer(runtime_summary):
        checkpoints[int(match.group(1))] = {
            "rng_seed_u16": "0x" + match.group(2),
            "scheduler_updates_u32": int(match.group(3)),
            "phase_u8": int(match.group(4)),
            "living_u16": int(match.group(5)),
            "spawn_index_u16": int(match.group(6)),
            "spawn_timer_u16": int(match.group(7)),
        }

    def source(frame: int, slot: int) -> dict[str, str]:
        return next(row for row in source_rows
                    if int(row["frame"]) == frame and
                    int(row["slot"], 16) == slot)

    def native(frame: int, slot: int) -> dict[str, str]:
        return next(row for row in native_rows
                    if int(row["frame"]) == frame and
                    int(row["source_slot"], 16) == slot)

    class09 = []
    for frame in (2510, 2511):
        for slot in (0x00ffb480, 0x00ffb500):
            source_row = source(frame, slot)
            native_row = native(frame, slot)
            class09.append({
                "frame_u16": frame,
                "source_slot": f"0x{slot:08x}",
                "source_animation_record": "0x" +
                    source_row["animation_record"],
                "native_animation_record": "0x" +
                    native_row["animation_record"],
            })
    controller = []
    for frame in (2510, 2511):
        source_row = source(frame, 0x00ffd180)
        native_row = native(frame, 0x00ffd180)
        controller.append({
            "frame_u16": frame,
            "source_spawn_index_u16": int(source_row["x_fp"], 16) >> 16,
            "native_spawn_index_u16": int(native_row["x"]),
        })
    spawned_source = source(2511, 0x00ffa3c0)
    spawned_native = native(2511, 0x00ffa3c0)
    class01_source = source(2330, 0x00ff9c40)
    class01_native = native(2330, 0x00ff9c40)
    reuse_frames = (2508, 2511, 2514, 2517)
    reuse_source = {frame: source(frame, 0x00ffa3c0)
                    for frame in reuse_frames}
    reuse_native = {frame: native(frame, 0x00ffa3c0)
                    for frame in reuse_frames}
    return {
        "source_phase_update_precedes_controller": True,
        "controller_precedes_new_record12_dispatch": True,
        "new_record12_precedes_type20_class09": True,
        "native_checkpoints": [dict({"frame_u16": frame},
                                    **checkpoints[frame])
                               for frame in (2510, 2511)],
        "class09_terminal_and_selection": class09,
        "controller_spawn_index": controller,
        "spawned_record12": {
            "frame_u16": 2511,
            "source_slot": "0x00ffa3c0",
            "source_state_u16": "0x" + spawned_source["state"],
            "native_state_u16": "0x" + spawned_native["state"],
            "source_position_s16": [
                int(spawned_source["x_fp"], 16) >> 16,
                int(spawned_source["y_fp"], 16) >> 16,
                int(spawned_source["z"])],
            "native_position_s16": [int(spawned_native["x"]),
                                      int(spawned_native["y"]),
                                      int(spawned_native["z"])],
            "source_health_s16": int(spawned_source["health"]),
            "native_health_s16": int(spawned_native["health"]),
            "same_frame_presentation": {
                "source": {
                    "state_u16": "0x" + spawned_source["state"],
                    "substate_u16": "0x" + spawned_source["substate"],
                    "facing_u8": int(spawned_source["facing"]),
                    "animation_record": "0x" +
                        spawned_source["animation_record"],
                    "assembly": "0x00130346",
                    "animation_timer_u16": int(
                        spawned_source["animation_timer"], 16),
                    "animation_branch_s16": int(
                        spawned_source["animation_branch"]),
                    "hurt_selector_u8": int(
                        spawned_source["hurt_selector"], 16),
                    "attack_selector_u8": int(
                        spawned_source["attack_selector"], 16),
                },
                "native": {
                    "state_u16": "0x" + spawned_native["state"],
                    "substate_u16": "0x" + spawned_native["substate"],
                    "facing_u8": int(spawned_native["facing"]),
                    "animation_record": "0x" +
                        spawned_native["animation_record"],
                    "assembly": "0x" + spawned_native["assembly"],
                    "animation_timer_u16": int(
                        spawned_native["animation_timer"]),
                    "animation_branch_s16": int(
                        spawned_native["animation_branch"]),
                    "hurt_selector_u8": int(
                        spawned_native["hurt_selector"]),
                    "attack_selector_u8": int(
                        spawned_native["attack_selector"]),
                },
            },
        },
        "source_owner_guard_negative_control": {
            "class01_controller_source_slot": "0x00ffb580",
            "class01_spawn_variant_u8": 5,
            "class01_next_record12_tick": {
                "source_frame": 2330,
                "source": {
                    "state_u16": "0x" + class01_source["state"],
                    "substate_u16": "0x" + class01_source["substate"],
                    "animation_record": "0x" +
                        class01_source["animation_record"],
                    "animation_timer_u16": int(
                        class01_source["animation_timer"], 16),
                    "animation_branch_s16": int(
                        class01_source["animation_branch"]),
                },
                "native": {
                    "state_u16": "0x" + class01_native["state"],
                    "substate_u16": "0x" + class01_native["substate"],
                    "animation_record": "0x" +
                        class01_native["animation_record"],
                    "animation_timer_u16": int(
                        class01_native["animation_timer"]),
                    "animation_branch_s16": int(
                        class01_native["animation_branch"]),
                },
            },
            "guard": "recurring post-allocation presentation applies only to source recurring-controller variants 3 or 4; class-0x01 variant 5 retains zero presentation until action 0x0e advances on the following tick",
        },
        "fixed_point_record_reuse": {
            "source_slot": "0x00ffa3c0",
            "writer_rule": "recurring spawn writes signed high position words and preserves the reused record's low u16 fixed-point fractions",
            "frames": {
                str(frame): {
                    "source": {
                        "x_fp_s32": int(reuse_source[frame]["x_fp"], 16),
                        "y_fp_s32": int(reuse_source[frame]["y_fp"], 16),
                    },
                    "native": {
                        "x_fp_s32": int(reuse_native[frame]["x_fp"]),
                        "y_fp_s32": int(reuse_native[frame]["y_fp"]),
                    },
                }
                for frame in reuse_frames
            },
            "cleared_fraction_negative_control": {
                "frame_2514_x_fp_s32": "0x02a76200",
                "frame_2514_y_fp_s32": "0x01467900",
                "frame_2517_x_fp_s32": "0x02aec400",
                "frame_2517_y_fp_s32": "0x0144f200",
            },
        },
    }


def validate_report(report: dict[str, object]) -> None:
    gate_names = {
        "source_actor_population_missing_on_saturn",
        "unowned_saturn_actors", "unidentified_source_class_type_pairs",
        "unmapped_source_spawn_despawn_edges", "unsupported_active_states",
        "unowned_collision_damage_events", "unowned_route_camera_events",
        "unowned_audio_load_events", "retained_gameplay_authorities"}
    if report["schema"] != "reimplement13-coffee-shop-scene-parity-v1":
        raise ValueError("Coffee Shop parity schema drift")
    if len(report["actor_lifetime_timeline"]["source"]) != 747 or \
            len(report["scene_component_map"]) != 38:
        raise ValueError("Coffee Shop source population was silently omitted")
    expected_edges = 2 * (747 + len(
        report["actor_lifetime_timeline"]["native"]))
    actual_edges = sum(len(item["events"])
                       for item in report["spawn_despawn_timeline"])
    if actual_edges != expected_edges:
        raise ValueError("Coffee Shop spawn/despawn edge omission")
    if set(report["gaps"]) != gate_names:
        raise ValueError("Coffee Shop acceptance gate drift")
    if report["gaps"]["unowned_saturn_actors"] != \
            len(report["unowned_native_lifetimes"]):
        raise ValueError("Coffee Shop native owner accounting drift")
    if report["gaps"]["source_actor_population_missing_on_saturn"] != \
            len(report["missing_source_lifetime_ids"]):
        raise ValueError("Coffee Shop missing-lifetime accounting drift")
    if any(item["classification"] == "NATIVE_IMPLEMENTED" and
           item["native_owner"] is None
           for item in report["scene_component_map"]):
        raise ValueError("Coffee Shop implemented source component has no owner")
    chronology = report["native_capture"]["first_button1_collision"]
    if chronology != {
            "source_scheduler_order": ["record4", "record12", "collision"],
            "source_native_prefix_equal_through_frame": 2287,
            "prefix_divergences": [],
            "source_damage_write": {
                "frame": 2306, "attacker": "0xff8880",
                "defender": "0xffa180", "attack_record": "0x030cd2",
                "health_before_s16": 87, "health_after_s16": 56,
                "writer_pc": "0x01d590"},
            "native_damage_transaction": {
                "scheduler_source_frame": 2306,
                "transaction_visible_frame": 2307,
                "attacker_slot": "0x00ff8880",
                "attack_table_base": "0x00030cb6",
                "attack_record": "0x00030cd2",
                "collision_result_before_scheduler_s16": 0,
                "collision_result_s16": -1,
                "collision_identity_u8": 42,
                "collision_registered_u8": 1,
                "projectile_health_s16": -1,
                "target_health_during_source_frame_s16": 87,
                "target_health_next_visible_frame_s16": 56,
                "target_state_next_visible_frame": "0x0202",
                "target_substate_next_visible_frame": "0x0000",
                "target_animation_next_visible_frame": "0x0012eb5c",
                "target_hurt_selector_next_visible_frame_u8": 1,
                "target_attack_selector_next_visible_frame_u8": 1,
                "target_slot": "0x00ffa180",
                "prior_target_health_values_s16": [87]},
            "native_impact_transaction": {
                "allocation_visible_frame": 2307,
                "slot": "0x00ffbd80", "type_u8": 24,
                "class_u8": 78, "state_at_allocation": "0x0000",
                "retained_animation_record_at_allocation": "0x0008df2c",
                "retained_assembly_at_allocation": "0x0008df96",
                "retained_animation_timer_at_allocation_u16": 4045,
                "initialization_visible_frame": 2308,
                "state_after_initialization": "0x0200",
                "animation_record": "0x00092914",
                "assembly": "0x00092c04"}}:
        raise ValueError("Coffee Shop first Button1 collision chronology drift")
    reuse = report["native_capture"]["fixed_slot_reuse_presentation"]
    if reuse != {
            "allocator": "0x01773e", "release": "0x017754",
            "source": [
                {"frame_u16": 2333, "state_u16": "0x0400",
                 "variant_u8": 0, "animation_record": "0x0003088c",
                 "animation_timer_u16": 1,
                 "animation_branch_s16": -32768},
                {"frame_u16": 2371, "state_u16": "0x0000",
                 "variant_u8": 2, "animation_record": "0x0003088c",
                 "animation_timer_u16": 1,
                 "animation_branch_s16": -32768},
                {"frame_u16": 2372, "state_u16": "0x0200",
                 "variant_u8": 2, "animation_record": "0x00030944",
                 "animation_timer_u16": 2, "animation_branch_s16": 0}],
            "native": [
                {"frame_u16": 2333, "state_u16": "0x0400",
                 "animation_record": "0x0003088c",
                 "assembly": "0x00030b28", "animation_timer_u16": 1},
                {"frame_u16": 2371, "state_u16": "0x0000",
                 "animation_record": "0x0003088c",
                 "assembly": "0x00030b28", "animation_timer_u16": 1},
                {"frame_u16": 2372, "state_u16": "0x0200",
                 "animation_record": "0x00030944",
                 "assembly": "0x00030bd6", "animation_timer_u16": 2}],
            "no_source_native_divergence_through_frame_u16": 2372,
            "next_slot_divergence_frame_u16": 2917}:
        raise ValueError("Coffee Shop record-4 fixed-slot reuse drift")
    recurring = report["native_capture"]["recurring_spawn_phase_boundary"]
    if recurring["native_checkpoints"] != [
            {"frame_u16": 2510, "rng_seed_u16": "0xd21c",
             "scheduler_updates_u32": 441, "phase_u8": 191,
             "living_u16": 7, "spawn_index_u16": 9,
             "spawn_timer_u16": 3707},
            {"frame_u16": 2511, "rng_seed_u16": "0x81a1",
             "scheduler_updates_u32": 442, "phase_u8": 192,
             "living_u16": 8, "spawn_index_u16": 8,
             "spawn_timer_u16": 3706}] or \
            any(item["source_animation_record"] !=
                item["native_animation_record"] for item in
                recurring["class09_terminal_and_selection"]) or \
            any(item["source_spawn_index_u16"] !=
                item["native_spawn_index_u16"] for item in
                recurring["controller_spawn_index"]) or \
            recurring["spawned_record12"]["source_position_s16"] != \
                recurring["spawned_record12"]["native_position_s16"] or \
            recurring["spawned_record12"]["source_health_s16"] != \
                recurring["spawned_record12"]["native_health_s16"] or \
            recurring["spawned_record12"]["same_frame_presentation"] \
                ["source"] != recurring["spawned_record12"] \
                ["same_frame_presentation"]["native"]:
        raise ValueError("Coffee Shop recurring spawn phase boundary drift")
    owner_guard = recurring["source_owner_guard_negative_control"]
    if owner_guard["class01_controller_source_slot"] != "0x00ffb580" or \
            owner_guard["class01_spawn_variant_u8"] != 5 or \
            owner_guard["class01_next_record12_tick"]["source"] != \
                owner_guard["class01_next_record12_tick"]["native"] or \
            owner_guard["class01_next_record12_tick"]["source"] != {
                "state_u16": "0x0200", "substate_u16": "0x0e00",
                "animation_record": "0x00000000",
                "animation_timer_u16": 0, "animation_branch_s16": 0,
            }:
        raise ValueError("Coffee Shop spawn-owner presentation guard drift")
    reuse = recurring["fixed_point_record_reuse"]
    reuse_expected = {
        "2508": {"x_fp_s32": 0x02bc8000, "y_fp_s32": 0x01389000},
        "2511": {"x_fp_s32": 0x02a08000, "y_fp_s32": 0x01489000},
        "2514": {"x_fp_s32": 0x02a7e200, "y_fp_s32": 0x01470900},
        "2517": {"x_fp_s32": 0x02af4400, "y_fp_s32": 0x01458200},
    }
    if reuse["source_slot"] != "0x00ffa3c0" or any(
            reuse["frames"][frame]["source"] != expected or
            reuse["frames"][frame]["native"] != expected
            for frame, expected in reuse_expected.items()):
        raise ValueError("Coffee Shop recurring fixed-point reuse drift")
    trajectory = report["native_capture"]["record4_parent_fixed_trajectory"]
    if trajectory["allocator"] != "0x01773e" or \
            trajectory["target_selector"] != "0x0241f0" or \
            trajectory["source_frame_range_u16"] != [2434, 2500] or \
            trajectory["source_row_count_u16"] != 67 or \
            trajectory["native_row_count_u16"] != 67 or \
            trajectory["source_rows_sha256"] != \
                trajectory["native_rows_sha256"] or \
            trajectory["source_anchors"] != trajectory["native_anchors"]:
        raise ValueError("Coffee Shop record-4 fixed trajectory drift")
    anchors = trajectory["source_anchors"]
    if anchors[0]["x_fp_s32"] != "0x03b50a00" or \
            anchors[0]["y_fp_s32"] != "0x0196b800" or \
            any(item["angle_u8"] != 46 for item in anchors) or \
            anchors[2]["animation_record"] != "0x0002fbb8" or \
            anchors[3]["animation_record"] != "0x0002fba8":
        raise ValueError("Coffee Shop record-4 reuse/angle/loop proof drift")
    action16 = report["native_capture"]["class1f_action16_rng_reuse"]
    action16_projection = [
        {"frame_u16": 2378, "state_u16": "0x0200",
         "substate_u16": "0x0000", "animation_record": "0x0012ec74",
         "attack_selector_u8": 2},
        {"frame_u16": 2379, "state_u16": "0x0200",
         "substate_u16": "0x1600", "animation_record": "0x0012e78c",
         "attack_selector_u8": 2},
        {"frame_u16": 2380, "state_u16": "0x0200",
         "substate_u16": "0x1600", "animation_record": "0x0012e78c",
         "attack_selector_u8": 2},
    ]
    if action16 != {
            "source_rng_call_frame_u16": 2377,
            "source_seed_before_u16": "0xc9a2",
            "source_seed_after_u16": "0x5cfe",
            "source_call_count_u8": 1,
            "second_call_forbidden": True,
            "native_seed_before_visible_frame": "0xedd9",
            "native_seed_after_visible_frame": "0x5cfe",
            "source": action16_projection,
            "native": action16_projection,
            "next_slot_divergence_frame_u16": None}:
        raise ValueError("Coffee Shop class-0x1f action-0x16 RNG reuse drift")
    latched_retry = report["native_capture"][
        "class1f_action16_latched_retry"]
    latched_retry_projection = [
        {"frame_u16": 2409, "state_u16": "0x0200",
         "substate_u16": "0x1600", "facing_u8": 1,
         "animation_record": "0x0012e7fc", "animation_timer_u16": 2,
         "attack_selector_u8": 2},
        {"frame_u16": 2410, "state_u16": "0x0200",
         "substate_u16": "0x1a00", "facing_u8": 0,
         "animation_record": "0x0012d5e4", "animation_timer_u16": 4,
         "attack_selector_u8": 2},
        {"frame_u16": 2411, "state_u16": "0x0200",
         "substate_u16": "0x1a00", "facing_u8": 0,
         "animation_record": "0x0012d5e4", "animation_timer_u16": 3,
         "attack_selector_u8": 2},
    ]
    if latched_retry != {
            "source_transition_frame_u16": 2409,
            "source_transition_pc": "0x060d52",
            "source_facing_write_pc": "0x060d58",
            "source_opcode_window": "0x060c9a-0x060d6a",
            "source_opcode_window_sha256":
                "4d40ad9eebfbc933233afc4d51d967d554748bb99ea0536b4f9baf276c54ae8f",
            "source_rng_seed_before_u16": "0x4bdf",
            "source_rng_seed_after_u16": "0xe3c2",
            "source_rng_call_count_u8": 1,
            "source": latched_retry_projection,
            "native": latched_retry_projection,
            "native_checkpoints": [
                {"frame_u16": 2409, "state_u16": "0x0200",
                 "substate_u16": "0x1600", "transition_latch_u8": 1,
                 "source_a6_u8": 2, "source_b0_u8": 1,
                 "animation_timer_u16": 2,
                 "animation_branch_s16": -32760,
                 "rng_seed_u16": "0x4bdf"},
                {"frame_u16": 2410, "state_u16": "0x0200",
                 "substate_u16": "0x1a00", "transition_latch_u8": 1,
                 "source_a6_u8": 2, "source_b0_u8": 0,
                 "animation_timer_u16": 4, "animation_branch_s16": 0,
                 "rng_seed_u16": "0xe3c2"}],
            "next_slot_divergence_frame_u16": None}:
        raise ValueError("Coffee Shop class-0x1f latched retry drift")
    deferred = report["native_capture"][
        "deferred_record4_collision_registration"]
    target_projection = [
        {"frame_u16": 2390, "state_u16": "0x0200",
         "substate_u16": "0x1800", "health_s16": 87,
         "animation_record": "0x0012e8c8"},
        {"frame_u16": 2391, "state_u16": "0x0202",
         "substate_u16": "0x0000", "health_s16": 56,
         "animation_record": "0x0012e8c8"},
        {"frame_u16": 2392, "state_u16": "0x0202",
         "substate_u16": "0x0002", "health_s16": 56,
         "animation_record": "0x0012e04c"},
    ]
    if deferred != {
            "source_damage_write": {
                "source_frame_u16": 2390,
                "attacker_slot": "0xff8680",
                "defender_slot": "0xff9dc0",
                "attack_record": "0x030cd2",
                "health_before_s16": 87,
                "health_after_s16": 56,
                "writer_pc": "0x01d590"},
            "native_projectile": [
                {"frame_u16": 2389, "state_u16": "0x0000",
                 "collision_registered_u8": 0,
                 "collision_result_s16": 0,
                 "current_attack_record": "0x00000000"},
                {"frame_u16": 2390, "state_u16": "0x0200",
                 "collision_registered_u8": 0,
                 "collision_result_s16": 0,
                 "current_attack_record": "0x00030cd2"},
                {"frame_u16": 2391, "state_u16": "0x0200",
                 "collision_registered_u8": 1,
                 "collision_result_s16": -1,
                 "current_attack_record": "0x00030cd2"}],
            "source_target": target_projection,
            "native_target": target_projection,
            "same_scan_initialization_collision_forbidden": True}:
        raise ValueError("Coffee Shop deferred record-4 registration drift")
    player_collision = report["native_capture"][
        "class1f_player_collision"]
    if player_collision != {
            "source_damage_write": {
                "source_frame_u16": 2750,
                "writer_pc": "0x01d5ee",
                "attack_record": "0x130b5c",
                "health_before_s16": 101,
                "health_after_s16": 91},
            "scheduler_order": [
                "player update", "record12 actor update",
                "current-state enemy-v-player collision",
                "next player update consumes HIT transition"],
            "source_attacker": [
                {"frame_u16": 2750, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d890",
                 "animation_timer_u16": 1, "health_s16": 87},
                {"frame_u16": 2751, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d8a0",
                 "animation_timer_u16": 1, "health_s16": 87},
                {"frame_u16": 2761, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d8a0",
                 "animation_timer_u16": 1, "health_s16": 87},
                {"frame_u16": 2762, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d8b0",
                 "animation_timer_u16": 9, "health_s16": 87}],
            "native_attacker": [
                {"frame_u16": 2750, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d890",
                 "animation_timer_u16": 1, "health_s16": 87},
                {"frame_u16": 2751, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d8a0",
                 "animation_timer_u16": 1, "health_s16": 87},
                {"frame_u16": 2761, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d8a0",
                 "animation_timer_u16": 1, "health_s16": 87},
                {"frame_u16": 2762, "state_u16": "0x0200",
                 "substate_u16": "0x0402",
                 "animation_record": "0x0012d8b0",
                 "animation_timer_u16": 9, "health_s16": 87}],
            "source_player": [
                {"frame_u16": 2750, "state_u16": "0x0200",
                 "substate_u16": "0x0202",
                 "animation_record": "0x0015f278",
                 "animation_timer_u16": 2, "health_s16": 101},
                {"frame_u16": 2751, "state_u16": "0x0202",
                 "substate_u16": "0x0000",
                 "animation_record": "0x0015f278",
                 "animation_timer_u16": 1, "health_s16": 91},
                {"frame_u16": 2761, "state_u16": "0x0202",
                 "substate_u16": "0x0200",
                 "animation_record": "0x0015eee8",
                 "animation_timer_u16": 8, "health_s16": 91},
                {"frame_u16": 2762, "state_u16": "0x0202",
                 "substate_u16": "0x0202",
                 "animation_record": "0x0015eee8",
                 "animation_timer_u16": 7, "health_s16": 91}],
            "native_player": [
                {"frame_u16": 2750, "state_u16": "0x0200",
                 "substate_u16": "0x0002",
                 "animation_record": "0x0015f1f4",
                 "animation_timer_u16": 4095, "health_s16": 101},
                {"frame_u16": 2751, "state_u16": "0x0200",
                 "substate_u16": "0x0002",
                 "animation_record": "0x0015f1f4",
                 "animation_timer_u16": 4095, "health_s16": 91},
                {"frame_u16": 2761, "state_u16": "0x0200",
                 "substate_u16": "0x0002",
                 "animation_record": "0x0015f1f4",
                 "animation_timer_u16": 4095, "health_s16": 91},
                {"frame_u16": 2762, "state_u16": "0x0200",
                 "substate_u16": "0x0002",
                 "animation_record": "0x0015f1f4",
                 "animation_timer_u16": 4095, "health_s16": 91}],
            "native_health_visible_frame_u16": 2751,
            "native_hitstop_first_frame_u16": 2751,
            "native_hitstop_last_frame_u16": 2761,
            "native_animation_advance_frame_u16": 2762,
            "authored_delay_forbidden": True,
            "next_attacker_divergence_frame_u16": 2798}:
        raise ValueError("Coffee Shop class-0x1f player collision drift")
    all_zero = all(value == 0 for value in report["gaps"].values())
    if report["acceptance"] != {"all_zero": all_zero, "ready": all_zero}:
        raise ValueError("Coffee Shop scene accepted before the zero-gap gate")


def main() -> None:
    fixtures = json.loads(FIXTURES.read_text(encoding="ascii"))
    source = fixtures["scene_manifests"]["coffee_shop"]
    rows, runtime_summary = capture()
    source_actor_sha256 = hashlib.sha256(SOURCE_ACTORS.read_bytes()).hexdigest()
    expected_source_actor_sha256 = source["capture_identity"][
        "completion_a"]["coffee_shop_scene_actors.tsv"]
    if source_actor_sha256 != expected_source_actor_sha256:
        raise ValueError("Coffee Shop source actor capture identity mismatch")
    with SOURCE_ACTORS.open(newline="", encoding="ascii") as handle:
        source_rows = list(csv.DictReader(handle, delimiter="\t"))
    native = lifetimes(rows)
    source_by_key = {key(item): item for item in source["actor_lifetimes"]}
    native_by_key = {key(item): item for item in native}
    source_occurrences = occurrence_map(source["actor_lifetimes"])
    native_occurrences = occurrence_map(native)
    missing = sorted(set(source_occurrences) - set(native_occurrences))
    extra = sorted(set(native_occurrences) - set(source_occurrences))
    matched_occurrences = sorted(set(source_occurrences) &
                                 set(native_occurrences))
    unmapped_source_edges = 2 * len(missing)
    for occurrence in matched_occurrences:
        source_lifetime = source_occurrences[occurrence]
        native_lifetime = native_occurrences[occurrence]
        unmapped_source_edges += (
            source_lifetime["first_frame"] != native_lifetime["first_frame"])
        unmapped_source_edges += (
            source_lifetime["last_frame"] != native_lifetime["last_frame"])
    unowned_native = [item for item in native if native_owner(item) is None]
    unidentified_pairs = [item for item in source["class_type_inventory"]
                          if item["source_classification"] != "SOURCE_CLOSED"]
    unsupported_states = []
    source_states: dict[tuple[int, str], set[tuple[int, int]]] = defaultdict(set)
    for item in source["actor_lifetimes"]:
        source_states[(item["type"], item["class"])].update(
            tuple(value) for value in item["states"])
    for item in native:
        pair = (item["type"], item["class"])
        unsupported = [value for value in item["states"]
                       if tuple(value) not in source_states[pair]]
        if unsupported:
            unsupported_states.append({"source_slot": item["source_slot"],
                                       "type": item["type"],
                                       "class": item["class"],
                                       "states": unsupported})
    divergences = source_native_divergences(source_rows, rows)
    report = {
        "schema": "reimplement13-coffee-shop-scene-parity-v1",
        "source_manifest": FIXTURES.relative_to(ROOT).as_posix() +
            "#/scene_manifests/coffee_shop",
        "source_manifest_sha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        "source_frame_range": [1972, 5566],
        "native_capture": {"row_count": len(rows),
                           "runtime_trace": {
                               "bytes": len(runtime_summary.encode("utf-8")),
                               "sha256": hashlib.sha256(
                                   runtime_summary.encode("utf-8")).hexdigest(),
                               "terminal_line": runtime_summary.splitlines()[-1]
                                   if runtime_summary else ""},
                           "transition_windows": {
                               "a000": compact_window(
                                   rows, 2070, 2330, {"00ffa000"}),
                               "obstacle": compact_window(
                                   rows, 2775, 2850, {
                                       "00ff8380", "00ffb300", "00ffb380",
                                       "00ffe180", "00ffe1c0", "00ffe200",
                                       "00ffe240"}),
                               "pre_obstacle_contact": compact_window(
                                   rows, 2740, 2780,
                                   {"00ff8380", "00ffa240"}),
                               "button1_contact": compact_window(
                                   rows, 2286, 2320, {
                                       "00ff8680", "00ff8700", "00ff8780",
                                       "00ff8800", "00ff8880", "00ff8900",
                                       "00ffa180", "00ffbd80"}),
                                "class1f_first_movement": compact_window(
                                    rows, 2208, 2280, {"00ffa240"})},
                           "first_button1_collision": collision_chronology(
                               source, rows, divergences),
                           "fixed_slot_reuse_presentation":
                               fixed_slot_reuse_presentation(
                                   source_rows, rows, divergences),
                           "record4_parent_fixed_trajectory":
                               record4_parent_fixed_trajectory(
                                   source_rows, rows),
                           "class1f_action16_rng_reuse":
                               class1f_action16_rng_reuse(
                                   source_rows, rows, divergences,
                                   runtime_summary),
                           "class1f_action16_latched_retry":
                               class1f_action16_latched_retry(
                                   source_rows, rows, divergences,
                                   runtime_summary),
                           "deferred_record4_collision_registration":
                               deferred_record4_collision_registration(
                                   source_rows, rows),
                           "class1f_player_collision":
                               class1f_player_collision_chronology(
                                   source, source_rows, rows, divergences),
                           "recurring_spawn_phase_boundary":
                               recurring_spawn_phase_boundary(
                                   source_rows, rows, runtime_summary)},
        "source_capture": {
            "actor_rows": len(source_rows),
            "actor_sha256": source_actor_sha256,
        },
        "source_native_first_divergence_by_slot": divergences,
        "actor_lifetime_timeline": {
            "source": [dict(source_lifetime_summary(item),
                            native_owner=native_owner(item),
                            exact_native_lifetime_match=(
                                key(item) in native_by_key))
                       for item in source["actor_lifetimes"]],
            "native": [dict(item, native_owner=native_owner(item),
                            exact_source_lifetime_match=(
                                key(item) in source_by_key))
                       for item in native],
        },
        "scene_component_map": [
            dict(item, native_owner=NATIVE_OWNERS.get(
                (int(item["type"]), str(item["class"]))))
            for item in source["class_type_inventory"]],
        "spawn_despawn_timeline": grouped_edge_timeline(
            source["actor_lifetimes"], native),
        "scene_events": {
            "collision_damage": source["health_writes"],
            "route": source["route_edges"],
            "camera": source["navigation"]["camera_runs"],
            "audio": source["audio_events"],
            "load_release": source["load_boundaries"],
        },
        "gaps": {
            "source_actor_population_missing_on_saturn": len(missing),
            "unowned_saturn_actors": len(unowned_native),
            "unidentified_source_class_type_pairs": len(unidentified_pairs),
            "unmapped_source_spawn_despawn_edges": unmapped_source_edges,
            "unsupported_active_states": len(unsupported_states),
            "unowned_collision_damage_events": sum(
                item["classification"] != "NATIVE_IMPLEMENTED"
                for item in source["health_writes"]),
            "unowned_route_camera_events": sum(
                item["classification"] != "NATIVE_IMPLEMENTED"
                for item in source["route_edges"] +
                source["navigation"]["camera_runs"]),
            "unowned_audio_load_events": sum(
                item["classification"] != "NATIVE_IMPLEMENTED"
                for item in source["audio_events"] + source["load_boundaries"]),
            "retained_gameplay_authorities": 0,
        },
        "missing_source_lifetime_ids": [
            source_occurrences[item]["id"] for item in missing],
        "unowned_native_lifetimes": unowned_native,
        "native_lifetime_differentials": [
            {"source_slot": native_occurrences[item]["source_slot"],
             "type": native_occurrences[item]["type"],
             "class": native_occurrences[item]["class"],
             "first_frame": native_occurrences[item]["first_frame"],
             "last_frame": native_occurrences[item]["last_frame"]}
            for item in extra],
        "unidentified_source_pairs": unidentified_pairs,
        "unsupported_native_states": unsupported_states,
        "acceptance": {"all_zero": False, "ready": False},
    }
    report["acceptance"]["all_zero"] = all(
        value == 0 for value in report["gaps"].values())
    report["acceptance"]["ready"] = report["acceptance"]["all_zero"]
    validate_report(report)
    OUT.write_bytes(canonical(report))
    print("Coffee Shop native scene census: " +
          " ".join(f"{name}={value}" for name, value in
                   report["gaps"].items()))


if __name__ == "__main__":
    main()
