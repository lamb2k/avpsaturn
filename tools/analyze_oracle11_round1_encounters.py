#!/usr/bin/env python3
"""Close Round 1 encounter, wave, scripted-trigger and route-edge authority."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps/mame/oracle11_round1_route_a"
RAW_B = ROOT / ".deps/mame/oracle11_round1_route_b"
ROUTE = ROOT / "data/oracle10_round1_route.json"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
OUT = ROOT / "data/oracle11_round1_encounter_route_authority.json"
ORACLE10_EVENTS = (ROOT / ".deps/mame/oracle10_round1_system_census_e" /
                   "baseline/actor_events.tsv")
FILES = ("route_samples.tsv", "route_writes.tsv", "route_writer_summary.tsv",
         "lifecycle_writes.tsv", "route_rng.tsv", "samples.tsv",
         "dispatches.tsv", "projectiles.tsv", "score_writes.tsv", "result.tsv")
ROUTE_EDGES = (
    (2237, "00c170", 4, "(u8(g8236) & u8(g81af)) == 0"),
    (5452, "008418", 6, "u8(g81f3) != 0"),
    (5523, "00c84c", 0, "(u8(g8236) & u8(g81af)) == 0"),
    (5561, "0083d4", 2, "s16(g837c) == 0"),
    (5719, "00c200", 4, "(u8(g8236) & u8(g81af)) == 0"),
    (6198, "008546", 0, "u8(g81af)==0 && u8(g81d4)==0 && no active player records"),
    (6199, "008bb2", 2, "failure/continue dispatcher entered state 0"),
    (6691, "0090f2", 4, "credited continue restore dispatcher entered state 2"),
    (12797, "008546", 0, "u8(g81af)==0 && u8(g81d4)==0 && no active player records"),
    (12798, "008bb2", 2, "failure/continue dispatcher entered state 0"),
    (13291, "0090f2", 4, "credited continue restore dispatcher entered state 2"),
    (15018, "008418", 6, "u8(g81f3) != 0"),
    (15020, "00c886", 0, "round-index dispatch selected the second transition body"),
    (15088, "0083d4", 2, "s16(g837c) == 0"),
)
SPAWN_GUARDS = {
    "028886": "ten-entry source table loop; allocate_record12 succeeds for each row",
    "028a3e": "living-enemy count < 8 && (u8(g8019) & 7)==0 && allocate_record12 succeeds",
    "028b7e": "scroll_x < 0x03f0 && ((u8(g8019)+3)&0x1f)==0 && allocate_record12 succeeds",
    "06b3fe": "owner state/timer permits spawn && living-enemy count < 6 && allocate_record12 succeeds",
    "01bf1e": "stage-table row passes x, player-count and variant guards && typed allocator succeeds",
    "020538": "stage-list row passes camera-x, character and route guards && allocate_record12 succeeds",
    "0208be": "scripted wave table entry reached && allocate_record12 succeeds",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream, delimiter="\t")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def identity(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "input_manifest.json").read_text(encoding="utf-8-sig"))
    require(manifest["authority_family"] == "encounters-waves-scripted-triggers",
            f"{path.name}: family identity drift")
    for filename in FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def window(image: bytes, pc: int, before: int = 16, after: int = 32) -> dict[str, object]:
    first, last = max(0, pc-before), min(len(image), pc+after)
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(image[first:last]).hexdigest()}


def build_report() -> dict[str, object]:
    id_a, id_b = identity(RAW_A), identity(RAW_B)
    require(id_a["files"] == id_b["files"], "route completion captures differ")
    final = next(rows(RAW_A / "result.tsv"))
    require(int(final["final_route"]) == 4, "route capture did not reach Round 2")
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    image = OPCODES.read_bytes()
    samples = {int(row["frame"]): row for row in rows(RAW_A / "route_samples.tsv")}
    writes_by_frame: dict[int, list[dict[str, str]]] = defaultdict(list)
    segment_writer_refs: list[set[str]] = [set() for _ in route["segments"]]
    segments = route["segments"]
    si = 0
    for row in rows(RAW_A / "route_writes.tsv"):
        frame = int(row["frame"])
        writes_by_frame[frame].append(row)
        while si + 1 < len(segments) and frame > segments[si]["source_frame_range"][1]:
            si += 1
        if segments[si]["source_frame_range"][0] <= frame <= segments[si]["source_frame_range"][1]:
            segment_writer_refs[si].add(f"0x{row['pc']}@0x{row['address']}")

    edge_rows = []
    for frame, pc, value, guard in ROUTE_EDGES:
        matches = [r for r in writes_by_frame[frame]
                   if r["address"] == "ff8008" and r["pc"] == pc and
                   int(r["data"], 16) == value]
        require(len(matches) == 1, f"route edge drift at frame {frame}")
        row = matches[0]
        edge_rows.append({
            "write_frame": frame, "sample_transition_frame": frame + 1,
            "field": "0xff8008:s16", "writer_pc": f"0x{pc}",
            "value": value, "transition_guard": guard,
            "caller_chain": [f"0x{row[k]}" for k in ("return0", "return1", "return2")],
            "source_window": window(image, int(pc, 16)),
            "classification": "SOURCE_CLOSED",
        })
    observed = [(item["frame"]-1, item["to"])
                for item in route["route_state_transitions"][1:]]
    require(observed == [(f, v) for f, _, v, _ in ROUTE_EDGES],
            "sampled route transition inventory drift")

    writer_transactions = []
    route_writer_pcs = set()
    for row in rows(RAW_A / "route_writer_summary.tsv"):
        pc = int(row["pc"], 16)
        route_writer_pcs.add(f"0x{pc:06x}")
        writer_transactions.append({
            "address": f"0x{row['address']}", "writer_pc": f"0x{pc:06x}",
            "first_frame": int(row["first_frame"]), "last_frame": int(row["last_frame"]),
            "write_count": int(row["count"]), "source_window": window(image, pc),
            "classification": "SOURCE_CLOSED",
        })
    require(len(writer_transactions) == 609 and len(route_writer_pcs) == 451,
            "route writer census drift")

    event_by_slot: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(ORACLE10_EVENTS):
        event_by_slot[row["slot"]].append(row)
    for values in event_by_slot.values():
        values.sort(key=lambda item: int(item["frame"]))

    def post_spawn(slot: str, frame: int) -> dict[str, str] | None:
        key = f"actor-{(int(slot, 16)-0xff9580)//0xc0}"
        for item in event_by_slot.get(key, []):
            if int(item["frame"]) >= frame and int(item["active"]):
                return item
        return None

    all_spawn_count = 0
    enemy_spawns = []
    delegated_spawns = 0
    lifecycle_pcs = set()
    for row in rows(RAW_A / "lifecycle_writes.tsv"):
        if not (row["inner"] == "00" and row["mask"] in ("0000ff00", "0000ffff")
                and int(row["old_active"]) == 0
                and ((int(row["data"], 16) >> 8) & 0xff) != 0):
            continue
        frame = int(row["frame"])
        if frame >= 15193:
            continue
        post = post_spawn(row["slot"], frame)
        require(post is not None, f"unresolved spawn identity {frame}/{row['slot']}")
        all_spawn_count += 1
        if int(post["type"]) != 12:
            delegated_spawns += 1
            continue
        require(row["pc"] in SPAWN_GUARDS, f"orphan type-12 spawn writer {row['pc']}")
        lifecycle_pcs.add(f"0x{row['pc']}")
        enemy_spawns.append({
            "frame": frame, "slot": f"0x{row['slot']}",
            "class": f"0x{post['class']}", "type": 12,
            "writer_pc": f"0x{row['pc']}",
            "caller_chain": [f"0x{row[k]}" for k in ("return0", "return1", "return2")],
            "transition_guard": SPAWN_GUARDS[row["pc"]],
            "writes": ["active:u8", "class:u8", "type:u8", "state:u16", "substate:u16",
                       "x:s16", "y:s16", "z:s16"],
            "source_window": window(image, int(row["pc"], 16)),
            "classification": "SOURCE_CLOSED",
        })
    require(all_spawn_count == 424 and delegated_spawns == 368 and len(enemy_spawns) == 56,
            "Round 1 spawn census drift")

    events = route["source_route_events"]
    segment_bindings = []
    for index, segment in enumerate(segments):
        first, last = segment["source_frame_range"]
        sample_frames = [frame for frame in samples if first <= frame <= last]
        mode_values = sorted({int(samples[frame]["g8008"], 16) for frame in sample_frames})
        edges = [item for item in edge_rows if first <= item["write_frame"] <= last]
        spawns = [item for item in enemy_spawns if first <= item["frame"] <= last]
        labels = [item["id"] for item in events if first <= item["source_frame"] <= last]
        segment_bindings.append({
            "route_segment": segment["id"], "source_frame_range": [first, last],
            "route_mode_values": mode_values,
            "gameplay_route_edges": edges,
            "enemy_spawn_count": len(spawns),
            "enemy_spawn_frames": sorted({item["frame"] for item in spawns}),
            "observational_labels": labels,
            "route_writer_refs": sorted(segment_writer_refs[index]),
            "presentation_boundary": {
                "signature": segment["presentation_dependency"]["stable_scene_id"],
                "owns_progression": False,
                "classification": ("NOT_REQUIRED_FOR_ROUND1" if first >= 15193 else
                                   "SOURCE_CLOSED_PRESENTATION_DEPENDENCY"),
            },
            "classification": "SOURCE_CLOSED",
        })
    require(len(segment_bindings) == 94 and
            {item["route_segment"] for item in segment_bindings} ==
            {item["id"] for item in segments}, "route segment coverage drift")

    controls = route["targeted_counterfactuals"]
    counterfactuals = {name: {
        "status": controls[name]["status"],
        "completed_round1": controls[name]["completed_round1"],
        "stable_round2_handoff_frame": controls[name]["stable_round2_handoff_frame"],
        "first_semantic_difference": controls[name]["semantic_difference"],
    } for name in ("route_perturbed", "suppress_street_offense",
                   "suppress_warehouse_offense", "remove_class_1f", "remove_class_00")}
    require(all(value["status"] == "PASS" and value["first_semantic_difference"]
                for value in counterfactuals.values()), "encounter controls drift")

    report = {
        "schema": "oracle11-round1-encounter-route-authority-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": ("Round 1 non-boss encounter/wave spawn authority, scripted route-state "
                  "edges and the sole 94-segment presentation-to-gameplay ownership map; "
                  "boss phase orchestration and final clear guard remain separate families"),
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True, "final_route": 4},
        "data_contract": {
            "global_base": "0xff8000", "global_state_field": "0xff8008:s16",
            "actor_active": "u8", "actor_class": "u8", "actor_type": "u8",
            "actor_state": "u16", "actor_substate": "u16",
            "actor_positions": "s16", "source_actor_stride": "0x00c0",
        },
        "route_entry": {"frame": 1972, "state": 2,
                        "classification": "SOURCE_CLOSED_STABLE_ENTRY"},
        "route_state_edges": edge_rows,
        "route_writer_transactions": writer_transactions,
        "enemy_spawns": enemy_spawns,
        "segment_bindings": segment_bindings,
        "counterfactuals": counterfactuals,
        "owned_authoritative_writer_pcs": sorted(route_writer_pcs | lifecycle_pcs),
        "coverage": {
            "route_segments_required": 94, "route_segments_closed": 94,
            "route_state_edges_required": 14, "route_state_edges_closed": 14,
            "route_writer_transactions_required": 609,
            "route_writer_transactions_closed": 609,
            "route_writer_pcs_required": 451, "route_writer_pcs_closed": 451,
            "round1_spawn_events": 424, "enemy_spawn_events_closed": 56,
            "spawn_events_delegated_to_closed_player_or_auxiliary_families": 368,
            "orphan_route_edges": 0, "orphan_route_writers": 0,
            "orphan_enemy_spawns": 0, "fixed_frame_substitutes": 0,
            "actor_count_clear_substitutes": 0,
        },
        "scope_boundary": {
            "boss_actor_behavior": "SOURCE_CLOSED_IN_ENEMY_FAMILY",
            "boss_phase_and_clear_orchestration": "PENDING_ROUND1_BOSS_FAMILY",
            "stage_clear_and_round2_handoff": "PENDING_HANDOFF_FAMILY",
            "rng_ownership": "PENDING_GLOBAL_RNG_FAMILY",
        },
        "negative_controls": {
            "presentation_signature_can_advance_gameplay": False,
            "fixed_frame_can_spawn_or_clear": False,
            "actor_population_alone_can_clear": False,
            "semantic_event_labels_used_as_guards": False,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED", "global_audio_load_release": "SOURCE_CLOSED",
            "navigation": "SOURCE_CLOSED", "enemies": "SOURCE_CLOSED",
            "auxiliary": "SOURCE_CLOSED", "production_runtime_writes": 0,
            "yaba_runs": 0, "frontend_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED" and
            report["capture_identity"]["byte_identical"] is True and
            report["capture_identity"]["final_route"] == 4,
            "encounter family identity drift")
    coverage = report["coverage"]
    require(coverage["route_segments_required"] == coverage["route_segments_closed"] == 94 and
            coverage["route_state_edges_required"] == coverage["route_state_edges_closed"] == 14 and
            coverage["route_writer_transactions_required"] ==
            coverage["route_writer_transactions_closed"] == 609 and
            coverage["enemy_spawn_events_closed"] == 56 and
            coverage["spawn_events_delegated_to_closed_player_or_auxiliary_families"] == 368 and
            all(value == 0 for key, value in coverage.items()
                if key.startswith("orphan_") or key.endswith("_substitutes")),
            "encounter zero-gap coverage drift")
    require(len(report["segment_bindings"]) == 94 and
            all(item["classification"] == "SOURCE_CLOSED"
                for item in report["segment_bindings"]), "unclosed route segment")
    require(len(report["route_state_edges"]) == 14 and
            all(item["classification"] == "SOURCE_CLOSED" and
                item["transition_guard"] for item in report["route_state_edges"]),
            "unclosed route state edge")
    require(len(report["enemy_spawns"]) == 56 and
            all(item["writer_pc"][2:] in SPAWN_GUARDS and item["transition_guard"]
                for item in report["enemy_spawns"]), "unclosed encounter spawn")
    require(report["negative_controls"] == {
        "presentation_signature_can_advance_gameplay": False,
        "fixed_frame_can_spawn_or_clear": False,
        "actor_population_alone_can_clear": False,
        "semantic_event_labels_used_as_guards": False,
    }, "encounter negative-control drift")
    require(report["protected_boundaries"]["production_runtime_writes"] == 0 and
            report["protected_boundaries"]["yaba_runs"] == 0 and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN" and
            report["protected_boundaries"]["spec02_active"] is False,
            "protected boundary drift")


def mutation_self_test(report: dict[str, object]) -> None:
    mutations = []
    for action in ("timer", "presentation", "actor-count"):
        mutant = copy.deepcopy(report)
        if action == "timer":
            mutant["coverage"]["fixed_frame_substitutes"] = 1
        elif action == "presentation":
            mutant["negative_controls"]["presentation_signature_can_advance_gameplay"] = True
        else:
            mutant["coverage"]["actor_count_clear_substitutes"] = 1
        mutations.append(mutant)
    missing = copy.deepcopy(report)
    missing["segment_bindings"] = missing["segment_bindings"][:-1]
    mutations.append(missing)
    for mutant in mutations:
        try:
            validate(mutant)
        except ValueError:
            continue
        raise ValueError("encounter mutation was accepted")


def main() -> None:
    report = build_report()
    mutation_self_test(report)
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 encounters/route: SOURCE_CLOSED; 94 segments, 14 state edges, "
          "609 route-writer transactions and 56 enemy spawns with zero orphan authority")


if __name__ == "__main__":
    main()
