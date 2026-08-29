#!/usr/bin/env python3
"""Generate the native side of the existing Coffee Shop scene manifest."""
from __future__ import annotations

import csv
import hashlib
import io
import json
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
    first: dict[str, dict[str, object]] = {}
    for source_row in source_rows:
        if source_row["active"] != "1":
            continue
        slot = f"{int(source_row['slot'], 16):08x}"
        native_row = native_by_key.get(
            (int(source_row["frame"]), slot, int(source_row["type"]),
             f"{int(source_row['class'], 16):02x}"))
        if native_row is None:
            continue
        if slot not in first:
            first[slot] = {
                "source_slot": "0x" + slot,
                "frame": int(source_row["frame"]),
                "type": int(source_row["type"]),
                "class": f"0x{int(source_row['class'], 16):02x}",
                "differences": {},
            }
        differences = first[slot]["differences"]
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
                               source, rows, divergences)},
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
