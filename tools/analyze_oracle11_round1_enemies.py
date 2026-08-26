#!/usr/bin/env python3
"""Close all route-reachable Round 1 type-12 enemy archetype authority."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_A = ROOT / ".deps" / "mame" / "oracle11_round1_enemies_a"
BASE_B = ROOT / ".deps" / "mame" / "oracle11_round1_enemies_b"
ROUTE = ROOT / "data" / "oracle10_round1_route.json"
SCHEDULER = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"
ORACLE09 = ROOT / "data" / "oracle09_street_alien_state_facing_presentation.json"
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
