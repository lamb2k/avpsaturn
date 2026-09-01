#!/usr/bin/env python3
"""Build the cumulative P2 Round 1 census-closure report."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIRST_ROUND1 = 1972
P2_FIRST = 5567
STABLE_ROUND2_SEAM = 15193
EXTENSION_RE = re.compile(
    r"oracle10_round1_census_extension_(\d+)_(\d+)\.json$")


def load(name: str) -> dict[str, object]:
    return json.loads((DATA / name).read_text(encoding="ascii"))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) \
        .encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    route = load("oracle10_round1_route.json")
    memory = load("reimplement13_round1_memory_plan.json")

    reports: list[tuple[int, int, Path, dict[str, object]]] = []
    for path in DATA.glob("oracle10_round1_census_extension_*.json"):
        match = EXTENSION_RE.match(path.name)
        if not match:
            continue
        first, last = (int(match.group(1)), int(match.group(2)))
        if first < P2_FIRST or last > STABLE_ROUND2_SEAM:
            continue
        report = json.loads(path.read_text(encoding="ascii"))
        if report["segment"]["source_frame_range"] != [first, last]:
            raise ValueError(f"segment range mismatch: {path.name}")
        reports.append((first, last, path, report))
    reports.sort(key=lambda row: row[0])
    if not reports or reports[0][0] != P2_FIRST or \
            reports[-1][1] != STABLE_ROUND2_SEAM:
        raise ValueError("P2 endpoints are incomplete")
    for left, right in zip(reports, reports[1:]):
        if left[1] + 1 != right[0]:
            raise ValueError(f"P2 gap or overlap: {left[1]} -> {right[0]}")

    baseline_pairs = {
        (row["class"], row["type"])
        for row in route["actor_instances"]
        if row["first_frame"] <= P2_FIRST - 1 and
        row["last_frame"] >= FIRST_ROUND1
    }
    all_pairs: dict[tuple[str, int], dict[str, object]] = {}
    first_pair_frame: dict[tuple[str, int], int] = {}
    p3_pairs: dict[tuple[str, int], dict[str, object]] = {}
    route_edges: list[dict[str, object]] = []
    load_boundaries: list[dict[str, object]] = []
    audio_owner_first: dict[str, int] = {}
    coverage = Counter()
    counts = Counter()
    semantic_stream = []
    evidence = []
    archive_identities = set()

    for first, last, path, report in reports:
        semantics = report["paired_capture_ceremony"]["segment_semantics"]
        census = report["scene_census_delta"]
        if report["status"] != "CENSUS_SEGMENT_COMPLETE" or \
                not report["paired_capture_ceremony"] \
                ["raw_capture_files_byte_identical"] or \
                not report["paired_capture_ceremony"] \
                ["paired_route_ledgers_byte_identical"]:
            raise ValueError(f"unaccepted paired segment: {path.name}")
        if semantics["identity_mismatch_frames"] or \
                semantics["character_mismatch_frames"]:
            raise ValueError(f"identity mismatch: {path.name}")
        evidence.append({
            "path": f"data/{path.name}",
            "sha256": digest(path),
            "source_frame_range": [first, last],
            "semantic_sha256": semantics["canonical_semantic_sha256"],
        })
        semantic_stream.append({
            "source_frame_range": [first, last],
            "semantic_sha256": semantics["canonical_semantic_sha256"],
        })
        counts.update({
            "frames": semantics["frame_count"],
            "actor_lifetime_rows": len(census["actor_lifetimes"]),
            "spawn_edges": len(census["spawn_edges"]),
            "despawn_edges": len(census["despawn_edges"]),
            "hit_ko_transitions": len(census["hit_ko_transitions"]),
            "audio_transactions": census["audio"]["handler_transaction_count"],
            "load_release_boundaries": len(census["load_release_boundaries"]),
            "route_state_edges": len(report["route_authority_extension"]
                                     ["route_state_edges"]),
        })
        for key, value in report["coverage"].items():
            coverage[key] += value
        for row in census["class_type_inventory"]:
            key = (row["class"], row["type"])
            owner = {"class": row["class"], "type": row["type"],
                     "source_owner": row["source_owner"],
                     "classification": row["classification"]}
            if key in all_pairs and all_pairs[key] != owner:
                raise ValueError(f"contradictory pair ownership: {key}")
            all_pairs[key] = owner
            first_pair_frame[key] = min(first_pair_frame.get(key, first), first)
        for row in report["table_demand_delta"]["p3_program_families"]:
            key = (row["class"], row["type"])
            if key in p3_pairs and p3_pairs[key] != row:
                raise ValueError(f"contradictory P3 family: {key}")
            p3_pairs[key] = row
        route_edges.extend(report["route_authority_extension"]
                           ["route_state_edges"])
        load_boundaries.extend(census["load_release_boundaries"])
        for row in census["audio"]["source_owned_trigger_groups_first_seen"]:
            for owner in row["owner_families"]:
                audio_owner_first[owner] = min(
                    audio_owner_first.get(owner, row["first_frame"]),
                    row["first_frame"])
        demand = report["table_demand_delta"]
        if demand["unbound_table_identities"]:
            raise ValueError(f"unbound table demand: {path.name}")
        archive_identities.add((demand["accepted_cart_archive_table_count"],
                                demand["accepted_cart_archive_sha256"]))

    if len(archive_identities) != 1:
        raise ValueError("accepted archive identity drift")
    archive_count, archive_sha = next(iter(archive_identities))
    archive = memory["content_archive"]
    if archive_count != archive["table_count"] or \
            archive_sha != archive["sha256"]:
        raise ValueError("memory-plan archive identity drift")
    runtime = next(row for row in memory["cartridge_dram1"]["regions"]
                   if row["id"] == "round1-runtime")
    runtime_headroom = runtime["size"] - runtime["required_bytes"]

    new_pairs = []
    for key in sorted(set(all_pairs) - baseline_pairs):
        new_pairs.append({**all_pairs[key],
                          "first_p2_source_frame": first_pair_frame[key]})
    route_programs = []
    for writer in sorted({row["writer_pc"] for row in route_edges},
                         key=lambda value: int(value, 16)):
        owned = [row for row in route_edges if row["writer_pc"] == writer]
        route_programs.append({
            "writer_pc": writer,
            "source_window": owned[0]["source_window"],
            "sample_transition_frames": [row["sample_transition_frame"]
                                           for row in owned],
            "guards": sorted({row["transition_guard"] for row in owned}),
            "classification": "SOURCE_CLOSED",
        })

    raw = route["control_captures"]
    report = {
        "schema": "oracle10-round1-p2-closure-v1",
        "task": "ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS",
        "phase": "P2",
        "status": "P2_CLOSED",
        "source_coverage": {
            "accepted_pre_p2_range": [FIRST_ROUND1, P2_FIRST - 1],
            "p2_extension_range": [P2_FIRST, STABLE_ROUND2_SEAM],
            "complete_round1_route_span": [FIRST_ROUND1,
                                           STABLE_ROUND2_SEAM],
            "complete_round1_route_frames":
                STABLE_ROUND2_SEAM - FIRST_ROUND1 + 1,
            "p2_frames": STABLE_ROUND2_SEAM - P2_FIRST + 1,
            "segment_count": len(reports),
            "continuous": True,
            "non_overlapping": True,
            "round2_gameplay_census_extended": False,
            "stable_round2_handoff_frame": STABLE_ROUND2_SEAM,
            "round1_to_round2_seam_classification":
                "ADAPTED_PRESENTATION_FOR_USER_10",
        },
        "paired_full_route_identity": {
            "independently_launched": raw["independently_launched"],
            "raw_capture_files_byte_identical": raw["byte_identical"],
            "screenshot_hash_stream_sha256": raw["capture_a"]
            ["screenshot_hash_stream_sha256"],
            "segment_semantic_stream_sha256": canonical_sha(semantic_stream),
            "all_segment_semantics_byte_identical": True,
        },
        "segment_evidence": evidence,
        "cumulative_segment_rows": dict(sorted(counts.items())),
        "ownership_closure": {
            "contradictory_segment_ownership": [],
            "coverage_gaps": dict(sorted(coverage.items())),
            "zero_unidentified_or_unowned_gameplay_authority":
                all(value == 0 for value in coverage.values()),
            "all_p2_class_type_pairs": [all_pairs[key]
                                        for key in sorted(all_pairs)],
            "new_class_type_pairs_vs_frame_5566": new_pairs,
        },
        "p3_reusable_program_controller_families": {
            "actor_programs": [p3_pairs[key] for key in sorted(p3_pairs)],
            "route_transition_programs": route_programs,
            "audio_owner_families": [
                {"owner": owner, "first_p2_source_frame": audio_owner_first[owner]}
                for owner in sorted(audio_owner_first)],
            "load_release_boundaries": [
                {"id": row["id"],
                 "visible_boundary_frame": row["visible_boundary_frame"],
                 "classification": row["classification"]}
                for row in sorted(load_boundaries,
                                  key=lambda value: value["visible_boundary_frame"])],
        },
        "route_controls": {
            "paired_route_state_edges": len(route_edges),
            "accepted_route_perturbation": route["route_wide_perturbation"],
            "accepted_failure_continue": route["failure_continue_path"],
            "accepted_counterfactual_gate": route["completion_gate"],
        },
        "table_demand_delta": {
            "accepted_archive_table_count": archive_count,
            "accepted_archive_bytes": archive["bytes"],
            "accepted_archive_sha256": archive_sha,
            "new_table_count": 0,
            "new_table_bytes": 0,
            "unbound_table_identities": [],
        },
        "mutable_carve": {
            "region": runtime["id"],
            "capacity_bytes": runtime["size"],
            "required_bytes_before_p2": runtime["required_bytes"],
            "required_bytes_after_p2": runtime["required_bytes"],
            "p2_headroom_consumed_bytes": 0,
            "remaining_headroom_bytes": runtime_headroom,
        },
        "remaining_blockers": {
            "source": [], "table": [], "capacity": [],
        },
        "memory_plan_holds_without_revision": True,
        "next_phase": "P3_SPEC02_BATCHED_WHOLE_ROUTINE_BODIES",
        "physical_saturn": "UNRUN",
    }
    output = DATA / "oracle10_round1_p2_closure.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(json.dumps({
        "result": report["status"],
        "segments": len(reports),
        "source_frame_range": [P2_FIRST, STABLE_ROUND2_SEAM],
        "new_class_type_pairs": len(new_pairs),
        "p3_actor_programs": len(p3_pairs),
        "route_programs": len(route_programs),
        "unbound_tables": 0,
        "memory_plan_holds": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
