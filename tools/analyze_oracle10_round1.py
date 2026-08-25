#!/usr/bin/env python3
"""Derive the ORACLE-10 Round 1 census from private full-route captures.

Only source-derived semantic metadata and hashes are written to tracked data.
Raw RAM, screenshots, ROM bytes, and audio payloads remain under .deps/mame.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTROL_A = ROOT / ".deps" / "mame" / "full_route"
DEFAULT_CONTROL_B = ROOT / ".deps" / "mame" / "full_route_rerun"
DEFAULT_ROUTE_OUTPUT = ROOT / "data" / "oracle10_round1_route.json"
DEFAULT_COVERAGE_OUTPUT = ROOT / "data" / "round1_system_coverage.yaml"
WORKRAM_BASE = 0xFF0000
PLAYER_SLOT = 0xFF8380
ENEMY_POOL_BASE = 0xFF9580
ENEMY_SLOT_SIZE = 0xC0
ACTOR_SLOT_COUNT = 57
ROUND1_FIRST_FRAME = 1972
ROUND2_STABLE_FRAME = 15193


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def be16(data: bytes, offset: int, signed: bool = False) -> int:
    return int.from_bytes(data[offset:offset + 2], "big", signed=signed)


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def ram_offset(address: int) -> int:
    return address - WORKRAM_BASE


def read_index(capture: Path) -> dict[int, list[tuple[str, int, int]]]:
    result: dict[int, list[tuple[str, int, int]]] = defaultdict(list)
    with (capture / "region_index.tsv").open(encoding="ascii") as stream:
        next(stream)
        for line in stream:
            frame, region, offset, length = line.rstrip().split("\t")
            result[int(frame)].append((region, int(offset), int(length)))
    return result


def read_samples(capture: Path) -> list[tuple[int, int, int, int]]:
    rows = []
    with (capture / "samples.tsv").open(encoding="ascii") as stream:
        next(stream)
        for line in stream:
            rows.append(tuple(int(value) for value in line.split("\t")))
    return rows


def capture_identity(capture: Path) -> dict:
    names = [
        "samples.tsv", "region_index.tsv", "region_workram.bin",
        "region_cps_a.bin", "region_cps_b.bin", "region_objram1.bin",
        "region_objram2.bin", "region_qsound.bin",
    ]
    files = {}
    for name in names:
        path = capture / name
        files[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    screenshot_names = sorted(capture.glob("reference_*.png"))
    screenshot_stream = hashlib.sha256()
    for path in screenshot_names:
        screenshot_stream.update(bytes.fromhex(sha256(path)))
    return {
        "capture": capture.name,
        "files": files,
        "screenshot_count": len(screenshot_names),
        "screenshot_hash_stream_sha256": screenshot_stream.hexdigest(),
    }


def actor_snapshot(workram: bytes, address: int) -> dict:
    offset = ram_offset(address)
    return {
        "active": workram[offset],
        "class": workram[offset + 0x02],
        "state_inner": be16(workram, offset + 0x04),
        "action_phase": be16(workram, offset + 0x06),
        "type": workram[offset + 0x08],
        "facing": workram[offset + 0x0F],
        "world_x": be16(workram, offset + 0x10, True),
        "world_y": be16(workram, offset + 0x14, True),
        "world_z": be16(workram, offset + 0x18, True),
        "animation_record": be32(workram, offset + 0x1C),
        "target_pointer": be16(workram, offset + 0x28),
        "animation_timer": be16(workram, offset + 0x2A),
        "health": be16(workram, offset + 0x40, True),
    }


def close_instance(instance: dict, frame: int) -> None:
    instance["last_frame"] = frame
    instance["source_frame_range"] = [instance["first_frame"], frame]
    for key in ("states", "facings", "animation_records", "target_pointers"):
        instance[key] = sorted(instance[key])
    for key in ("world_x", "world_y", "world_z", "health"):
        values = instance.pop(key + "_values")
        instance[key + "_range"] = [min(values), max(values)]
    instance["state_transitions"] = [
        {"from": before, "to": after, "first_frame": first, "count": count}
        for (before, after), (first, count) in sorted(
            instance.pop("transition_counts").items(), key=lambda row: row[1][0])
    ]


def update_instance(instance: dict, actor: dict, frame: int) -> None:
    current_state = [actor["state_inner"], actor["action_phase"]]
    previous_state = instance.get("previous_state")
    if previous_state is not None and previous_state != current_state:
        key = (tuple(previous_state), tuple(current_state))
        first, count = instance["transition_counts"].get(key, (frame, 0))
        instance["transition_counts"][key] = (first, count + 1)
    instance["previous_state"] = current_state
    instance["states"].add(tuple(current_state))
    instance["facings"].add(actor["facing"])
    instance["animation_records"].add(f"0x{actor['animation_record']:08x}")
    instance["target_pointers"].add(f"0x{actor['target_pointer']:04x}")
    for key in ("world_x", "world_y", "world_z", "health"):
        instance[key + "_values"].append(actor[key])
    instance["last_observed_frame"] = frame


def new_instance(slot_kind: str, slot_index: int, address: int,
                 actor: dict, frame: int) -> dict:
    instance = {
        "id": f"{slot_kind}-{slot_index}-life-{frame}",
        "slot_kind": slot_kind,
        "slot_index": slot_index,
        "slot_address": f"0x{address:06x}",
        "first_frame": frame,
        "class": f"0x{actor['class']:02x}",
        "type": actor["type"],
        "fields_read": [
            "active+0x00:u8", "class+0x02:u8", "state+0x04:u16",
            "phase+0x06:u16", "type+0x08:u8", "facing+0x0f:u8",
            "world_x+0x10:s16", "world_y+0x14:s16",
            "world_z+0x18:s16", "animation_record+0x1c:u32",
            "target_pointer+0x28:u16", "animation_timer+0x2a:u16",
            "health+0x40:s16",
        ],
        "fields_written": "UNKNOWN_PENDING_ORACLE_11_WRITER_CLOSURE",
        "states": set(), "facings": set(), "animation_records": set(),
        "target_pointers": set(), "transition_counts": {},
        "world_x_values": [], "world_y_values": [], "world_z_values": [],
        "health_values": [],
        "rng_consumption": "OBSERVED_ROUTE_STREAM_NOT_YET_BOUND_TO_ACTOR",
        "update_scheduler_order": (
            "player-slot-before-enemy-pool" if slot_kind == "player" else
            f"enemy-pool-index-{slot_index}"
        ),
        "animation_and_assembly_identity": (
            "animation record observed; assembly pointer requires source table closure"
        ),
        "collision_selectors": "UNKNOWN_PENDING_ORACLE_11",
        "presentation_dependency": "active object list and animation record",
        "source_closure_status": "OBSERVED",
        "responsible_source_routine_or_table": "UNKNOWN_PENDING_STATIC_BINDING",
        "exact_next_experiment": (
            "Bind this class/type lifetime to its dispatcher, writer set, "
            "animation/assembly table, collision selectors, and RNG calls."
        ),
    }
    update_instance(instance, actor, frame)
    return instance


def analyze_frames(capture: Path) -> dict:
    index = read_index(capture)
    samples = read_samples(capture)
    needed = ("workram", "cps_a", "cps_b")
    streams = {name: (capture / f"region_{name}.bin").open("rb")
               for name in needed}
    current: dict[str, bytes] = {}
    active_instances: dict[tuple[str, int], dict] = {}
    instances: list[dict] = []
    route_state_transitions = []
    rng_changes = []
    qsound_change_frames = []
    gfx_rewrite_frames = []
    camera_runs = []
    previous_route_state = None
    previous_rng = None
    previous_scroll2 = None
    camera_run_start = None
    last_frame = None
    input_counter = Counter()
    round2_stable_video_signature = None

    for frame, input_word, _bank, _writes in samples:
        changed_regions = set()
        gfx_changes = 0
        for region, offset, length in index.get(frame, ()):
            changed_regions.add(region)
            if region.startswith("gfxram"):
                gfx_changes += 1
            if region in streams:
                stream = streams[region]
                stream.seek(offset)
                current[region] = stream.read(length)
        if "qsound" in changed_regions:
            qsound_change_frames.append(frame)
        if gfx_changes >= 2:
            gfx_rewrite_frames.append(frame)
        if frame < ROUND1_FIRST_FRAME:
            continue
        if frame > ROUND2_STABLE_FRAME:
            break
        workram = current["workram"]
        cps_a = [be16(current["cps_a"], offset)
                 for offset in range(0, len(current["cps_a"]), 2)]
        if frame == ROUND2_STABLE_FRAME:
            round2_stable_video_signature = {
                "frame": frame,
                "cps_a": current["cps_a"].hex(),
                "cps_b": current["cps_b"].hex(),
            }
        input_counter[input_word] += 1

        route_state = workram[0x8009]
        if route_state != previous_route_state:
            route_state_transitions.append({
                "frame": frame, "from": previous_route_state,
                "to": route_state, "field": "0xff8009:u8",
                "responsible_source_routine_or_table": "UNKNOWN_PENDING_ORACLE_11",
                "source_closure_status": "OBSERVED",
                "exact_next_experiment": "Bind the write PC and transition guard.",
            })
            previous_route_state = route_state

        rng = be16(workram, 0x81A8)
        if previous_rng is not None and rng != previous_rng:
            rng_changes.append({"frame": frame, "from": previous_rng, "to": rng})
        previous_rng = rng

        scroll2 = cps_a[8]
        if scroll2 != previous_scroll2:
            if previous_scroll2 is not None:
                camera_runs.append({
                    "first_frame": camera_run_start, "last_frame": frame - 1,
                    "frames": frame - camera_run_start, "scroll2_x": previous_scroll2,
                })
            camera_run_start = frame
            previous_scroll2 = scroll2

        slots = [("player", 0, PLAYER_SLOT)] + [
            ("actor", index, ENEMY_POOL_BASE + index * ENEMY_SLOT_SIZE)
            for index in range(ACTOR_SLOT_COUNT)
        ]
        for slot_kind, slot_index, address in slots:
            actor = actor_snapshot(workram, address)
            key = (slot_kind, slot_index)
            live = actor["active"] != 0
            instance = active_instances.get(key)
            identity = (f"0x{actor['class']:02x}", actor["type"])
            if instance and (not live or
                             (instance["class"], instance["type"]) != identity):
                close_instance(instance, frame - 1)
                instances.append(instance)
                del active_instances[key]
                instance = None
            if live and instance is None:
                instance = new_instance(slot_kind, slot_index, address, actor, frame)
                active_instances[key] = instance
            elif live:
                update_instance(instance, actor, frame)
        last_frame = frame

    if previous_scroll2 is not None and camera_run_start is not None:
        camera_runs.append({
            "first_frame": camera_run_start, "last_frame": last_frame,
            "frames": last_frame - camera_run_start + 1,
            "scroll2_x": previous_scroll2,
        })
    for instance in active_instances.values():
        close_instance(instance, last_frame)
        instances.append(instance)
    for stream in streams.values():
        stream.close()

    archetypes: dict[tuple[str, int], dict] = {}
    for instance in instances:
        key = (instance["class"], instance["type"])
        row = archetypes.setdefault(key, {
            "id": f"actor-class-{instance['class'][2:]}-type-{instance['type']}",
            "class": instance["class"], "type": instance["type"],
            "source_frame_range": [instance["first_frame"], instance["last_frame"]],
            "actor_slots_and_classes": [], "instance_count": 0,
            "responsible_source_routine_or_table": "UNKNOWN_PENDING_STATIC_BINDING",
            "fields_read": instance["fields_read"],
            "fields_written": "UNKNOWN_PENDING_ORACLE_11_WRITER_CLOSURE",
            "state_transitions": [],
            "rng_consumption": "OBSERVED_ROUTE_STREAM_NOT_YET_BOUND_TO_ARCHETYPE",
            "update_scheduler_order": "fixed actor pool; exact class dispatch pending",
            "animation_and_assembly_identities": [],
            "collision_selectors": "UNKNOWN_PENDING_ORACLE_11",
            "presentation_dependency": "active object list and animation record",
            "source_closure_status": "OBSERVED",
            "exact_next_experiment": (
                "Recover the bounded class/type dispatcher, states, writers, "
                "RNG, animation/assembly table, and collision selectors."
            ),
        })
        row["instance_count"] += 1
        row["source_frame_range"][0] = min(row["source_frame_range"][0],
                                            instance["first_frame"])
        row["source_frame_range"][1] = max(row["source_frame_range"][1],
                                            instance["last_frame"])
        row["actor_slots_and_classes"].append({
            "slot": instance["slot_address"], "class": instance["class"],
            "life": instance["source_frame_range"],
        })
        row["state_transitions"].extend(instance["state_transitions"])
        row["animation_and_assembly_identities"].extend(
            instance["animation_records"])
    for row in archetypes.values():
        row["animation_and_assembly_identities"] = sorted(set(
            row["animation_and_assembly_identities"]))

    return {
        "actor_instances": instances,
        "actor_archetypes": sorted(archetypes.values(),
                                   key=lambda row: (row["class"], row["type"])),
        "route_state_transitions": route_state_transitions,
        "rng_change_count": len(rng_changes),
        "rng_changes": rng_changes,
        "camera_lock_runs": [row for row in camera_runs if row["frames"] >= 30],
        "audio_change_frames": [frame for frame in qsound_change_frames
                                if ROUND1_FIRST_FRAME <= frame <= ROUND2_STABLE_FRAME],
        "load_release_boundary_frames": [frame for frame in gfx_rewrite_frames
                                         if ROUND1_FIRST_FRAME <= frame <= ROUND2_STABLE_FRAME],
        "input_word_frame_counts": {str(key): value
                                    for key, value in sorted(input_counter.items())},
        "round2_stable_video_signature": round2_stable_video_signature,
    }


def scene_segments() -> list[dict]:
    manifest = json.loads((ROOT / "data" / "avsp_scene_manifest.json").read_text())
    segments = []
    for scene in manifest["scenes"]:
        first = scene["first_frame"]
        last = scene["last_frame"]
        if last < ROUND1_FIRST_FRAME or first > ROUND2_STABLE_FRAME:
            continue
        segments.append({
            "id": scene.get("label") or scene["stable_id"],
            "source_frame_range": [first, last],
            "route_state_and_substate": "UNKNOWN_PENDING_GLOBAL_WRITER_CENSUS",
            "actor_slots_and_classes": "see actor_instances overlapping this range",
            "responsible_source_routine_or_table": "UNKNOWN_PENDING_ORACLE_11",
            "fields_read": "UNKNOWN_PENDING_ORACLE_11",
            "fields_written": "UNKNOWN_PENDING_ORACLE_11",
            "state_transitions": scene["transition"],
            "rng_consumption": "see route RNG stream within this range",
            "update_scheduler_order": "fixed actor pool; class dispatch pending",
            "animation_and_assembly_identities": "see overlapping actor instances",
            "collision_selectors": "see overlapping actor instances",
            "presentation_dependency": {
                "stable_scene_id": scene["stable_id"],
                "layer_bases": scene["composition"]["layer_bases"],
                "boundary_reason": scene["boundary_reason"],
            },
            "source_closure_status": "OBSERVED",
            "exact_next_experiment": (
                "Bind the route controller state, trigger guard, load ownership, "
                "and every overlapping actor dispatcher without visual inference."
            ),
        })
    return segments


def authority_families() -> list[dict]:
    return [
        {"id": "predator-warrior-player-authority", "status": "PARTIAL",
         "accepted_evidence": ["data/oracle07_predator_warrior_action_graph_equipment.json"],
         "counterfactual": "bounded action/equipment mutations accepted; full-route completion perturbation pending",
         "exact_next_experiment": "Close locomotion-to-neutral, complete actions/equipment/projectiles, HIT/KO/continue, and return to control."},
        {"id": "round1-navigation-terrain-camera", "status": "PARTIAL",
         "accepted_evidence": ["data/oracle08_round1_navigation_bounds.json", "data/repair11_live_background_presentation.json"],
         "counterfactual": "Coffee Shop bounds mutations accepted; all later geometry and route camera guards pending",
         "exact_next_experiment": "Bind every later terrain/obstacle/destructible and camera lock/unlock source guard."},
        {"id": "actor-scheduler-allocation-lifecycle", "status": "OBSERVED",
         "accepted_evidence": ["data/oracle09_street_alien_state_facing_presentation.json"],
         "counterfactual": "class-0x1F scheduler mutation accepted; route-wide allocation/lifecycle controls pending",
         "exact_next_experiment": "Recover pool allocator, scheduler loop, class dispatch order, spawn, despawn, and cleanup writers."},
        {"id": "round1-enemy-archetypes", "status": "OBSERVED",
         "accepted_evidence": ["data/oracle09_street_alien_state_facing_presentation.json", "data/stalker_action_capture.json"],
         "counterfactual": "class-0x1F controls accepted; each additional observed class/type requires targeted control",
         "exact_next_experiment": "Bind and counterfactually test each required class/type dispatcher."},
        {"id": "pickups-equipment-weapons-projectiles-hazards-destructibles", "status": "OBSERVED",
         "accepted_evidence": ["data/oracle07_predator_warrior_action_graph_equipment.json"],
         "counterfactual": "bounded action-local equipment mutation accepted; route bodies pending",
         "exact_next_experiment": "Identify each actor class/type by source table and test its resource/collision/lifecycle authority."},
        {"id": "encounters-waves-scripted-triggers", "status": "PARTIAL",
         "accepted_evidence": ["data/oracle06_round1_encounter.json"],
         "counterfactual": "first street entry/withdrawal controls accepted; later route controllers pending",
         "exact_next_experiment": "Bind every spawn/wave/script trigger and reject fixed-frame or presentation-owned clear."},
        {"id": "round1-boss", "status": "OBSERVED",
         "accepted_evidence": ["data/boss_action_capture.json", "data/boss_ko_capture.json"],
         "counterfactual": "action/KO captures exist; boss phase and encounter authority controls pending",
         "exact_next_experiment": "Recover boss dispatcher, phase guards, RNG, attacks, collision, damage, KO, and encounter clear."},
        {"id": "stage-clear-failure-continue-round2-handoff", "status": "OBSERVED",
         "accepted_evidence": ["data/round1_route_census.json"],
         "counterfactual": "two source continues are captured; completing route-wide perturbation and clear/handoff controls pending",
         "exact_next_experiment": "Bind failure/credit/continue, boss-clear, Round 2 title/load, and first stable Round 2 gameplay state."},
        {"id": "gameplay-audio-load-release", "status": "OBSERVED",
         "accepted_evidence": ["data/stage1_route.json"],
         "counterfactual": "event changes are observed; gameplay-owner suppression controls pending",
         "exact_next_experiment": "Bind each route-required QSound/load/release event to its gameplay writer and guard."},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-a", type=Path, default=DEFAULT_CONTROL_A)
    parser.add_argument("--control-b", type=Path, default=DEFAULT_CONTROL_B)
    parser.add_argument("--route-output", type=Path, default=DEFAULT_ROUTE_OUTPUT)
    parser.add_argument("--coverage-output", type=Path,
                        default=DEFAULT_COVERAGE_OUTPUT)
    args = parser.parse_args()

    identity_a = capture_identity(args.control_a)
    identity_b = capture_identity(args.control_b)
    identical = (identity_a["files"] == identity_b["files"] and
                 identity_a["screenshot_hash_stream_sha256"] ==
                 identity_b["screenshot_hash_stream_sha256"])
    if not identical:
        raise SystemExit("independent control captures are not byte-identical")

    analysis = analyze_frames(args.control_a)
    segments = scene_segments()
    route = {
        "schema": "oracle10-round1-route-v1",
        "task": "ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS",
        "status": "IN_PROGRESS",
        "source_set": "avspu",
        "scope": {
            "reference_character": "predator_warrior", "players": 1,
            "first_round1_title_frame": ROUND1_FIRST_FRAME,
            "round2_stable_handoff_frame": ROUND2_STABLE_FRAME,
        },
        "control_captures": {
            "independently_launched": True, "byte_identical": identical,
            "capture_a": identity_a, "capture_b": identity_b,
        },
        "route_wide_perturbation": {"status": "PENDING"},
        "failure_continue_path": {
            "status": "OBSERVED",
            "continue_scene_ranges": [[6201, 6692], [12800, 13292]],
            "completion_after_continue": True,
            "stable_round2_handoff_frame": ROUND2_STABLE_FRAME,
        },
        "segments": segments,
        **analysis,
        "authority_families": authority_families(),
        "completion_gate": {
            "two_independent_identical_completions": "PASS",
            "route_wide_completing_perturbation": "PENDING",
            "targeted_counterfactuals_all_discovered_authorities": "PENDING",
            "bounded_failure_continue": "PASS",
            "production_runtime_writes": 0,
        },
        "physical_saturn": "UNRUN",
    }

    coverage = {
        "schema": "round1-system-coverage-v1",
        "task": route["task"], "status": "IN_PROGRESS",
        "classification_vocabulary": [
            "SOURCE_CLOSED", "PARTIAL", "OBSERVED", "ADAPTED", "UNKNOWN",
            "NOT_REQUIRED_FOR_ROUND1",
        ],
        "source_set": "avspu", "route": route["scope"],
        "control_capture_identity": {
            "byte_identical": identical,
            "samples_sha256": identity_a["files"]["samples.tsv"]["sha256"],
            "region_index_sha256": identity_a["files"]["region_index.tsv"]["sha256"],
            "screenshot_hash_stream_sha256": identity_a["screenshot_hash_stream_sha256"],
        },
        "counts": {
            "segments": len(segments),
            "actor_instances": len(analysis["actor_instances"]),
            "actor_archetypes": len(analysis["actor_archetypes"]),
            "route_state_transitions": len(analysis["route_state_transitions"]),
            "camera_lock_runs": len(analysis["camera_lock_runs"]),
            "rng_changes": analysis["rng_change_count"],
            "audio_change_frames": len(analysis["audio_change_frames"]),
            "load_release_boundaries": len(analysis["load_release_boundary_frames"]),
        },
        "bodies": authority_families(),
        "required_unknown_count": sum(
            1 for body in authority_families() if body["status"] == "UNKNOWN"),
        "pending_oracle10_controls": [
            "route-wide completing input perturbation",
            "targeted counterfactual for every newly observed authority family",
            "static routine/table binding where already known",
        ],
        "production_runtime_writes": 0,
        "frontend_active": False,
        "user09_status": "CHANGES_REQUESTED",
        "physical_saturn": "UNRUN",
    }

    args.route_output.write_text(json.dumps(route, indent=2, sort_keys=True) + "\n")
    args.coverage_output.write_text(
        json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    print("ORACLE-10 initial census: PASS")
    print(f"segments={len(segments)} actor_instances={len(analysis['actor_instances'])} "
          f"actor_archetypes={len(analysis['actor_archetypes'])}")


if __name__ == "__main__":
    main()
