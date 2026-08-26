#!/usr/bin/env python3
"""Close Round 1 stage clear, failure/continue, and stable Round 2 handoff."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps/mame/oracle11_round1_handoff_a"
RAW_B = ROOT / ".deps/mame/oracle11_round1_handoff_b"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ROUTE = ROOT / "data/oracle10_round1_route.json"
PLAYER = ROOT / "data/oracle11_predator_warrior_authority.json"
BOSS = ROOT / "data/oracle11_round1_boss_orchestration.json"
LOAD = ROOT / "data/oracle11_global_load_release_boundaries.json"
OUT = ROOT / "data/oracle11_round1_handoff.json"
FILES = ("handoff_samples.tsv", "handoff_writes.tsv", "samples.tsv",
         "dispatches.tsv", "projectiles.tsv", "score_writes.tsv", "result.tsv")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def identity(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    require(manifest["authority_family"] ==
            "stage-clear-failure-continue-round2-handoff", "family drift")
    require(manifest["variant"] == "baseline", "variant drift")
    for name in FILES:
        require(digest(path / name) == manifest["sha256"][name],
                f"{path.name}: {name} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "variant": manifest["variant"], "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def source_window(image: bytes, pc: int) -> dict[str, object]:
    first, last = max(0, pc - 24), min(len(image), pc + 16)
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(image[first:last]).hexdigest()}


def at(samples: dict[int, dict[str, str]], frame: int) -> dict[str, str]:
    require(frame in samples, f"missing handoff frame {frame}")
    return samples[frame]


def write_at(writes: list[dict[str, str]], frame: int, domain: str,
             pc: str, offset: str | None = None) -> dict[str, str]:
    found = [row for row in writes if row["frame"] == str(frame) and
             row["domain"] == domain and row["pc"] == pc and
             (offset is None or row["offset"] == offset)]
    require(len(found) == 1, f"writer cardinality drift {frame}/{domain}/{pc}/{offset}")
    return found[0]


def build_report() -> dict[str, object]:
    id_a, id_b = identity(RAW_A), identity(RAW_B)
    require(id_a["files"] == id_b["files"], "handoff completions differ")
    image = OPCODES.read_bytes()
    sample_rows = rows(RAW_A / "handoff_samples.tsv")
    write_rows = rows(RAW_A / "handoff_writes.tsv")
    require(len(sample_rows) == 4101 and len(write_rows) == 69260,
            "handoff census size drift")
    samples = {int(row["frame"]): row for row in sample_rows}

    expected = {
        14355: (4, 0, 1, 512, 4096, 1, "02", 522, 512),
        14356: (4, 0, 1, 512, 4098, 1, "02", 522, 512),
        14357: (4, 0, 1, 512, 4100, 1, "02", 522, 512),
        15018: (4, 1, 1, 512, 4100, 1, "02", 1536, 0),
        15019: (6, 1, 1, 2048, 0, 1, "02", 1536, 0),
        15021: (0, 1, 1, 2048, 0, 1, "02", 1536, 0),
        15048: (0, 0, 1, 2048, 0, 0, "00", 0, 0),
        15089: (2, 0, 1, 2048, 0, 0, "00", 0, 0),
        15193: (2, 0, 1, 2048, 0, 1, "03", 512, 0),
        15194: (2, 0, 1, 2048, 0, 1, "03", 514, 0),
        15195: (2, 0, 1, 2048, 0, 1, "03", 516, 0),
        15332: (4, 0, 1, 512, 0, 1, "03", 516, 0),
    }
    fields = ("route_state", "clear_flag", "player_active", "player_state",
              "player_action", "controller_active", "controller_class",
              "controller_state", "controller_phase")
    for frame, wanted in expected.items():
        row = at(samples, frame)
        got = tuple(row[field] if field == "controller_class" else int(row[field])
                    for field in fields)
        require(got == wanted, f"handoff state drift at {frame}: {got}")

    action_writers = [
        write_at(write_rows, 14354, "player", "01b60c", "06"),
        write_at(write_rows, 14355, "player", "019bb4", "06"),
        write_at(write_rows, 14356, "player", "019bfa", "06"),
    ]
    route_writers = [
        write_at(write_rows, 15017, "clear-flag", "028ea2"),
        write_at(write_rows, 15018, "route-state", "008418"),
        write_at(write_rows, 15020, "route-state", "00c886"),
        write_at(write_rows, 15047, "clear-flag", "0083a6"),
        write_at(write_rows, 15061, "transition-countdown", "003c28"),
        write_at(write_rows, 15077, "transition-countdown", "00188c"),
        write_at(write_rows, 15088, "route-state", "0083d4"),
        write_at(write_rows, 15088, "clear-flag", "0083dc"),
        write_at(write_rows, 15331, "route-state", "00c37a"),
        write_at(write_rows, 15331, "player", "01a3fa", "04"),
    ]

    boss = json.loads(BOSS.read_text(encoding="ascii"))
    require(boss["status"] == "SOURCE_CLOSED" and
            boss["boss_clear_guard"]["write_tap_pc"] == "0x028ea2",
            "accepted boss-clear edge drift")
    player = json.loads(PLAYER.read_text(encoding="ascii"))
    failure = player["hit_ko_failure_continue_respawn"]
    require(failure["failure_continue"]["classification"] == "SOURCE_CLOSED" and
            failure["respawn_return"]["classification"] == "SOURCE_CLOSED",
            "accepted failure/continue boundary drift")
    load = json.loads(LOAD.read_text(encoding="ascii"))
    require(load["status"] == "SOURCE_CLOSED" and len(load["boundaries"]) == 4 and
            all(boundary["legal_read_window"]["last_frame_inclusive"] <= 15193
                for boundary in load["boundaries"]), "load ownership drift")
    route = json.loads(ROUTE.read_text(encoding="ascii"))
    controls = route["targeted_counterfactuals"]
    require(controls["route_perturbed"]["completed_round1"] is True and
            controls["suppress_boss_offense"]["completed_round1"] is True and
            controls["remove_class_06"]["completed_round1"] is False and
            controls["no_continue"]["completed_round1"] is False,
            "handoff counterfactual universe drift")
    clear_control = boss["counterfactuals"]["suppress_exact_clear_writer"]
    require(clear_control["completed_round1"] is False and
            clear_control["round1_state_at_frame_18000"] == 4,
            "clear suppression control drift")

    route_edges = [
        {"source_frame": 15018, "visible_frame": 15019, "from": 4, "to": 6,
         "guard": "u8(0xff81f3) != 0", "tap_pc": "0x008418",
         "writer": "0x008410 move.w #6,0x08(A5)", "reads": ["0xff81f3:u8"],
         "writes": ["0xff8008:u16=6"]},
        {"source_frame": 15020, "visible_frame": 15021, "from": 6, "to": 0,
         "guard": "round-index second transition body", "tap_pc": "0x00c886",
         "writer": "0x00c880 clr.w 0x08(A5)", "reads": ["route transition dispatch"],
         "writes": ["0xff8008:u16=0"]},
        {"source_frame": 15088, "visible_frame": 15089, "from": 0, "to": 2,
         "guard": "s16(0xff837c) == 0", "tap_pc": "0x0083d4",
         "writer": "0x0083ce addq.w #2,0x08(A5)", "reads": ["0xff837c:s16"],
         "writes": ["0xff8008:u16=2"]},
        {"source_frame": 15331, "visible_frame": 15332, "from": 2, "to": 4,
         "guard": "u8(0xff8236) & u8(0xff81af) == 0", "tap_pc": "0x00c37a",
         "writer": "0x00c374 addq.w #2,0x08(A5)",
         "reads": ["0xff8236:u8", "0xff81af:u8"],
         "writes": ["0xff8008:u16=4"]},
    ]
    for edge in route_edges:
        edge["source_window"] = source_window(image, int(edge["tap_pc"], 16))
        edge["classification"] = "SOURCE_CLOSED"

    handoff_writer_pcs = sorted({f"0x{row['pc']}" for row in
                                 action_writers + route_writers})
    report = {
        "schema": "oracle11-round1-stage-clear-handoff-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": ("Round 1 stage-clear player phases, accepted failure/continue, "
                  "post-clear route reset, intermission ownership, Round 2 route "
                  "entry and first stable return to interactive control"),
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True, "sample_rows": len(sample_rows),
                             "write_rows": len(write_rows),
                             "opcode_sha256": digest(OPCODES)},
        "accepted_incoming_edges": {
            "boss_clear": "data/oracle11_round1_boss_orchestration.json",
            "failure_continue_respawn_return":
                "data/oracle11_predator_warrior_authority.json",
            "load_release": "data/oracle11_global_load_release_boundaries.json",
            "classifications": "SOURCE_CLOSED_CONSUMED_NOT_REOPENED",
        },
        "stage_clear_player_action": {
            "record": "0xff8380", "state": "0x0200",
            "phases": ["0x1000", "0x1002", "0x1004"],
            "timeline_frames": [14355, 14356, 14357],
            "entry_guard": ("controller state 0x020a/substate 0x0200 dispatches "
                            "the source stage-clear action initializer"),
            "writers": [
                {"tap_pc": "0x01b60c", "source_writer":
                 "0x01b604 move.l #0x02001000,0x04(A6)",
                 "writes": ["player state:u16=0x0200", "player action:u16=0x1000"]},
                {"tap_pc": "0x019bb4", "source_writer":
                 "stage-clear action dispatch increments low phase byte",
                 "writes": ["player action:u16=0x1002"]},
                {"tap_pc": "0x019bfa", "source_writer":
                 "0x019bf4 addq.b #2,0x07(A6)",
                 "writes": ["player action:u16=0x1004"]},
            ],
            "classification": "SOURCE_CLOSED",
        },
        "route_edges": route_edges,
        "transition_countdown": {
            "initialization": {"frame": 15061, "tap_pc": "0x003c28",
                               "value": 16},
            "decrement": {"first_frame": 15062, "last_frame": 15077,
                          "tap_pc": "0x00188c", "values": [15, 0],
                          "source_writer": "0x001886 subq.w #1,0x037c(A5)"},
            "classification": "SOURCE_CLOSED",
        },
        "round2_handoff": {
            "round2_controller": {"record": "0xffd180", "class": "0x03",
                                  "states": ["0x0200", "0x0202", "0x0204"],
                                  "frames": [15193, 15194, 15195],
                                  "authority": "presentation dependency only"},
            "live_route_state": {"frame": 15332, "route_state": 4,
                                 "player_state": "0x0200", "player_action": "0x0000"},
            "stable_round2_signature_frame": 16425,
            "stable_round2_route_state": 4,
            "continued_capture_through_frame": 18000,
            "fixed_frame_substitute": False,
            "presentation_label_used_as_guard": False,
            "classification": "SOURCE_CLOSED",
        },
        "load_release_ownership": {
            "boundaries": 4, "new_unowned_events": 0,
            "legal_round1_read_window_last_frame": 15193,
            "contract": "data/oracle11_global_load_release_boundaries.json",
            "classification": "SOURCE_CLOSED_CONSUMED_NOT_REOPENED",
        },
        "counterfactuals": {
            "route_perturbed_completes": True,
            "suppress_boss_offense_completes": True,
            "remove_class_06_completes": False,
            "no_continue_completes": False,
            "suppress_exact_clear_writer_completes": False,
            "suppressed_clear_holds_round1_through_frame": 18000,
        },
        "coverage": {
            "stage_clear_phases_required": 3, "stage_clear_phases_closed": 3,
            "handoff_route_edges_required": 4, "handoff_route_edges_closed": 4,
            "load_release_boundaries_consumed": 4,
            "orphan_stage_clear_phases": 0, "orphan_handoff_route_edges": 0,
            "orphan_load_release_events": 0, "orphan_handoff_writers": 0,
            "fixed_frame_authorities": 0, "presentation_label_authorities": 0,
        },
        "owned_authoritative_writer_pcs": handoff_writer_pcs,
        "scope_boundary": {"stage_clear_and_round2_handoff": "SOURCE_CLOSED",
                           "global_rng_ownership": "PENDING_GLOBAL_RNG_FAMILY"},
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED", "user09": "CHANGES_REQUESTED",
            "spec02_active": False, "production_runtime_writes": 0,
            "yaba_runs": 0, "physical_saturn": "UNRUN",
        },
    }
    for item in report["stage_clear_player_action"]["writers"]:
        item["source_window"] = source_window(image, int(item["tap_pc"], 16))
        item["classification"] = "SOURCE_CLOSED"
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED", "handoff status drift")
    require(report["capture_identity"]["byte_identical"] is True,
            "handoff repeatability drift")
    coverage = report["coverage"]
    require(all(value == 0 for key, value in coverage.items()
                if key.startswith("orphan_")), "handoff orphan drift")
    require(coverage["fixed_frame_authorities"] == 0 and
            coverage["presentation_label_authorities"] == 0,
            "unsourced handoff authority accepted")
    require(report["counterfactuals"]["suppress_exact_clear_writer_completes"]
            is False, "clear suppression fabricated completion")
    require(report["round2_handoff"]["stable_round2_route_state"] == 4 and
            report["round2_handoff"]["continued_capture_through_frame"] >= 18000,
            "stable Round 2 handoff missing")
    require(report["load_release_ownership"]["new_unowned_events"] == 0,
            "unowned handoff load event accepted")
    require(report["scope_boundary"]["global_rng_ownership"] ==
            "PENDING_GLOBAL_RNG_FAMILY", "global RNG silently absorbed")
    require(report["protected_boundaries"]["spec02_active"] is False and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN",
            "protected handoff boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes((json.dumps(report, sort_keys=True, indent=2) + "\n").encode("ascii"))
    print("ORACLE-11 Round 1 handoff: SOURCE_CLOSED; 3 stage-clear phases, "
          "4 route edges, 4 consumed load boundaries and stable Round 2 control")


if __name__ == "__main__":
    main()
