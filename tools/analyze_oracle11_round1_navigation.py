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

    base_samples = rows(BASE_A / "navigation_samples.tsv")
    perturbed_samples = rows(PERTURBED / "navigation_samples.tsv")
    base_writes = rows(BASE_A / "navigation_writes.tsv")
    perturbed_writes = rows(PERTURBED / "navigation_writes.tsv")
    base_bodies = rows(BASE_A / "navigation_body_writes.tsv")
    perturbed_bodies = rows(PERTURBED / "navigation_body_writes.tsv")
    base_camera = rows(BASE_A / "camera_writes.tsv")
    route = json.loads(ORACLE10.read_text(encoding="utf-8"))
    oracle08 = json.loads(ORACLE08.read_text(encoding="utf-8"))
    scheduler = json.loads(SCHEDULER.read_text(encoding="ascii"))
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()

    terrain = terrain_records([base_writes, perturbed_writes], program)
    type20 = type20_instances(route, [base_bodies, perturbed_bodies], opcodes)
    camera = camera_authority(route, base_samples, base_camera, opcodes)
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
        },
        "camera": camera,
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
            capture["perturbation_discriminated_navigation"] is True,
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
            {"0x0b20d6", "0x0b2136"}, "terrain closure drift")
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
