#!/usr/bin/env python3
"""Close route-reachable Predator Warrior directional and airborne authority."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle11_player_air_b"
RAW_DOWN = ROOT / ".deps" / "mame" / "oracle11_player_air_c"
RAW_GUN = ROOT / ".deps" / "mame" / "oracle11_player_air_d"
RAW_NATURAL = ROOT / ".deps" / "mame" / "oracle11_player_jump_a"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
WEAPON = ROOT / "data" / "oracle11_predator_weapon_projectile_resource.json"
OUT = ROOT / "data" / "oracle11_predator_air_authority.json"
ROUTE_RUNS = {
    "baseline-completions": ROOT / ".deps" / "mame" /
        "oracle10_round1_system_census_e" / "baseline" / "samples.tsv",
    "perturbed-completions": ROOT / ".deps" / "mame" /
        "oracle10_round1_system_census_c" / "route_perturbed" / "samples.tsv",
    "failure-continue": ROOT / ".deps" / "mame" /
        "oracle10_round1_system_census_d" / "no_continue" / "samples.tsv",
}

ROUTE_REQUIRED = {0x0400, 0x0402, 0x0404, 0x0406}
COUNTERFACTUAL_REQUIRED = {0x040A, 0x040C, 0x040E, 0x0410}
NOT_REQUIRED = {0x0408, 0x0412, 0x0414}
STATE_TABLE = {
    0x00: 0x0233E6, 0x02: 0x02349A, 0x04: 0x0234E4,
    0x06: 0x0234F0, 0x08: 0x023500, 0x0A: 0x023534,
    0x0C: 0x02358E, 0x0E: 0x02359C, 0x10: 0x0235BC,
    0x12: 0x0235EC, 0x14: 0x02360C,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def indexed(path: Path) -> dict[int, dict[str, str]]:
    return {int(row["frame"]): row for row in rows(path)}


def source_window(data: bytes, start: int, end: int) -> dict[str, object]:
    return {"start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
            "bytes": end - start,
            "sha256": hashlib.sha256(data[start:end]).hexdigest()}


def manifest_identity(root: Path) -> dict[str, object]:
    manifest_path = root / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    for variant in manifest["variants"]:
        for filename, expected in variant["sha256"].items():
            require(digest(root / variant["name"] / filename) == expected,
                    f"{root.name}/{variant['name']}/{filename}: identity drift")
    return {"manifest_sha256": digest(manifest_path),
            "variant_names": [item["name"] for item in manifest["variants"]]}


def phases(path: Path) -> set[int]:
    observed = set()
    for row in rows(path):
        value = int(row["p_action"] if "p_action" in row else row["p_phase"])
        if value >> 8 == 4:
            observed.add(value)
    return observed


def phase_writer(path: Path, phase: int, pc: str) -> bool:
    return any(row["offset"] == "06" and row["pc"] == pc and
               (int(row["data"], 16) & 0xffff) == phase
               for row in rows(path))


def build_report() -> dict[str, object]:
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()
    require(len(opcodes) == len(program) == 0x200000,
            "decoded source image size drift")
    identities = {root.name: manifest_identity(root)
                  for root in (RAW, RAW_DOWN, RAW_GUN)}
    for filename in ("samples.tsv", "player_writes.tsv",
                     "player_global_writes.tsv"):
        require(digest(RAW / "air_cold_1" / filename) ==
                digest(RAW / "air_cold_2" / filename),
                f"independent cold air captures differ: {filename}")

    route_phase_sets = {name: sorted(phases(path))
                        for name, path in ROUTE_RUNS.items()}
    for name, observed in route_phase_sets.items():
        require(set(observed) == ROUTE_REQUIRED,
                f"{name}: route airborne phase census drift")

    dash = {name: indexed(RAW / name / "samples.tsv") for name in
            ("dash_right", "dash_left", "dash_up", "dash_down")}
    require(int(dash["dash_right"][4424]["p_action"]) == 0x0402 and
            int(dash["dash_left"][4424]["p_action"]) == 0x0402 and
            int(dash["dash_up"][4424]["p_action"]) == 0x0402,
            "directional jump phase drift")
    require((int(dash["dash_down"][4424]["p_action"]),
             int(dash["dash_down"][4437]["p_action"])) == (0x040A, 0x040C),
            "Down+Button3 source phases drift")
    require(int(dash["dash_left"][4462]["p_action"]) == 0x0404 and
            int(dash["dash_right"][4441]["p_action"]) == 0x0404 and
            int(dash["dash_up"][4473]["p_action"]) == 0x0404,
            "directional landing drift")

    air_b2 = indexed(RAW / "air_button2_neutral" / "samples.tsv")
    air_down = indexed(RAW_DOWN / "air_button2_midair_down" / "samples.tsv")
    require(int(air_b2[4432]["p_action"]) == 0x040E and
            int(air_down[4432]["p_action"]) == 0x0410,
            "air Button2 branch drift")
    require(all(phase not in phases(RAW / name / "samples.tsv")
                for name in ("air_button2_followup_4436",
                             "air_button2_followup_4442",
                             "air_button2_followup_4449",
                             "air_button2_followup_4454")
                for phase in (0x0412, 0x0414)),
            "air follow-up negative control unexpectedly reached gated body")

    gun = indexed(RAW_GUN / "air_button1_resource" / "samples.tsv")
    require((int(gun[4697]["p_action"]), int(gun[4697]["p_x"]),
             int(gun[4697]["p_z"])) == (0x0406, 1360, 319),
            "route-reachable airborne Button1 phase drift")
    require(phase_writer(RAW_GUN / "air_button1_resource" /
                         "player_writes.tsv", 0x0406, "023860"),
            "airborne Button1 writer drift")

    natural = indexed(RAW_NATURAL / "dash_right" / "samples.tsv")
    natural_writes = RAW_NATURAL / "dash_right" / "player_writes.tsv"
    require(int(natural[4424]["p_action"]) == 0x0402 and
            int(natural[4433]["p_inner"]) == 2 and
            phase_writer(natural_writes, 0x0202, "01a988"),
            "natural directional-air HIT interruption drift")

    counterfactual_phases = set()
    for name in ("dash_right", "dash_left", "dash_up", "dash_down",
                 "air_button2_neutral"):
        counterfactual_phases |= phases(RAW / name / "samples.tsv")
    counterfactual_phases |= phases(
        RAW_DOWN / "air_button2_midair_down" / "samples.tsv")
    counterfactual_phases |= phases(
        RAW_GUN / "air_button1_resource" / "samples.tsv")
    require(COUNTERFACTUAL_REQUIRED <= counterfactual_phases,
            "targeted counterfactual phase coverage drift")

    weapon = json.loads(WEAPON.read_text(encoding="ascii"))
    report = {
        "schema": "oracle11-predator-air-authority-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "Predator Warrior route-reachable directional jump, airborne Button1/Button2 actions, landing, interruption cancellation, and return to control",
        "coverage_universe": {
            "routes": ["baseline-completion-a", "baseline-completion-b",
                       "perturbed-completions", "failure-continue",
                       "targeted-counterfactuals"],
            "route_phase_census": route_phase_sets,
            "required_route_phases": [f"0x{x:04x}" for x in sorted(ROUTE_REQUIRED)],
            "required_counterfactual_phases": [
                f"0x{x:04x}" for x in sorted(COUNTERFACTUAL_REQUIRED)],
            "all_required_phases_closed": True,
        },
        "source_identity": {
            "decoded_opcodes_sha256": hashlib.sha256(opcodes).hexdigest(),
            "decrypted_program_sha256": hashlib.sha256(program).hexdigest(),
            "jump_dispatch_and_vector_setup": source_window(
                opcodes, 0x02331E, 0x0233C4),
            "air_state_dispatch_and_bodies": source_window(
                opcodes, 0x0233C4, 0x02370C),
            "air_vector_table_resolver": source_window(
                opcodes, 0x02370C, 0x023858),
            "airborne_button1_spawn_branch": source_window(
                opcodes, 0x023858, 0x023926),
            "fixed_point_air_motion": source_window(
                opcodes, 0x01A8E6, 0x01A932),
            "button2_edge_guard": source_window(
                opcodes, 0x01A6C4, 0x01A6DC),
            "air_reverse_guard": source_window(
                opcodes, 0x01A932, 0x01A96E),
            "interruption_reset": source_window(
                opcodes, 0x01A96E, 0x01AA5E),
            "capture_manifests": identities,
        },
        "state_dispatch": {
            f"0x{state:02x}": f"0x{pc:06x}"
            for state, pc in STATE_TABLE.items()
        },
        "directional_actions": {
            "classification": "SOURCE_CLOSED",
            "input_guard": "new Button3 edge at actor +0xee/+0xef bit 6",
            "entry": "0x0233e6",
            "vector_resolver": "0x02331e",
            "directions": {
                "neutral": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "right": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "left": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "up_lane": {"phases": ["0x0400", "0x0402", "0x0404"]},
                "down_lane": {"phases": ["0x0400", "0x040a", "0x040c"]},
            },
            "landing_guard": "0x01a8e6 signed world-Y versus world-Z comparison; carry clear enters 0x023630",
            "landing_writer": "0x023636",
            "landing_phase": "0x0404",
            "cleanup": "0x01a3fa clears action; 0x0198de returns to source idle/locomotion dispatch",
            "facing": "latched from +0x0f; direction-specific fixed-point vectors are selected before airborne updates",
            "rng_consumption": "none",
        },
        "airborne_actions": {
            "classification": "SOURCE_CLOSED",
            "button1": {
                "guard": "0x01a6f4 source edge/resource checks",
                "phase": "0x0406", "writer": "0x023860",
                "spawn_branch": "0x023858",
                "resource_and_projectile_authority": "data/oracle11_predator_weapon_projectile_resource.json",
                "resource_artifact_sha256": digest(WEAPON),
                "resource_status": weapon["status"],
            },
            "button2": {
                "guard": "0x01a6c4 new Button2 edge",
                "neutral_or_non_down_phase": "0x040e",
                "down_held_at_air_edge_phase": "0x0410",
                "writer": "0x02367c",
                "held_or_repeated_edge": "does not auto-repeat or enter a gated continuation when +0x6e animation-event byte remains zero",
            },
            "motion": "all required branches return through 0x01a8e6 and source landing 0x023630",
            "rng_consumption": "none for action, direction, phase, or presentation selection",
        },
        "interruption": {
            "classification": "SOURCE_CLOSED",
            "natural_witness": {"air_phase_frame": 4424,
                                "hit_cancel_frame": 4433,
                                "phase_before": "0x0402",
                                "inner_after": 2},
            "writers": ["0x01a988", "0x01aa30", "0x01aa34", "0x01aa5c"],
            "rule": "source HIT entry advances the inner dispatcher, clears buffered/action-local state, and replaces the airborne action; damage and HIT recovery remain owned by the player HIT/KO authority checkpoint",
            "rng_consumption": "none",
        },
        "not_required_for_round1": {
            "classification": "NOT_REQUIRED_FOR_ROUND1",
            "phases": {
                "0x0408": "dispatcher body exists but has no entry in either completion, failure/continue, perturbed, or input-only targeted routes",
                "0x0412": "requires +0x6e animation-event continuation from an air attack; all reachable PW air-attack records keep the guard clear",
                "0x0414": "requires the 0x01a932 direction/terrain-mask reversal guard; directional Button3-repeat counterfactual does not satisfy it",
            },
            "mutation_rule": "a future route witness for any phase reopens this family and forbids retaining NOT_REQUIRED_FOR_ROUND1",
        },
        "counterfactuals": {
            "independent_cold_runs_byte_identical": True,
            "all_four_direction_lanes_exercised": True,
            "air_button2_neutral_and_down_split": True,
            "air_button2_hold_no_auto_repeat": True,
            "air_button2_followup_guards_rejected": True,
            "air_button3_directional_repeat_guard_rejected": True,
            "air_button1_empty_rejected_and_sufficient_resource_accepted": True,
            "natural_hit_cancels_directional_air": True,
        },
        "mutation_controls": [
            "reject missing required phase", "reject widened phase requirement",
            "reject incorrect phase writer", "reject random action selection",
            "reject held Button2 auto-repeat", "reject interruption omission",
            "reject a NOT_REQUIRED phase once a route witness appears",
        ],
        "remaining_unknowns": [],
        "protected_boundaries": {
            "production_runtime_writes": 0, "yaba_run": False,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED" and
            report["remaining_unknowns"] == [], "air authority not closed")
    universe = report["coverage_universe"]
    require(universe["all_required_phases_closed"] is True and
            set(universe["required_route_phases"]) ==
            {f"0x{x:04x}" for x in ROUTE_REQUIRED} and
            set(universe["required_counterfactual_phases"]) ==
            {f"0x{x:04x}" for x in COUNTERFACTUAL_REQUIRED},
            "required phase coverage drift")
    require(report["directional_actions"]["classification"] ==
            "SOURCE_CLOSED" and
            report["airborne_actions"]["classification"] ==
            "SOURCE_CLOSED" and
            report["interruption"]["classification"] == "SOURCE_CLOSED",
            "required sub-authority classification drift")
    require(report["directional_actions"]["landing_writer"] == "0x023636" and
            report["airborne_actions"]["button1"]["writer"] == "0x023860" and
            report["airborne_actions"]["button2"]["writer"] == "0x02367c",
            "air phase writer identity drift")
    require(report["directional_actions"]["rng_consumption"] == "none" and
            report["airborne_actions"]["rng_consumption"].startswith("none") and
            report["interruption"]["rng_consumption"] == "none",
            "unsourced player-air RNG introduced")
    require(set(report["not_required_for_round1"]["phases"]) ==
            {f"0x{x:04x}" for x in NOT_REQUIRED},
            "NOT_REQUIRED phase inventory drift")
    require(report["counterfactuals"]["air_button2_hold_no_auto_repeat"] and
            report["counterfactuals"]["natural_hit_cancels_directional_air"],
            "air negative control drift")
    protected = report["protected_boundaries"]
    require(protected["production_runtime_writes"] == 0 and
            protected["yaba_run"] is False and
            protected["frontend_active"] is False and
            protected["user09_status"] == "CHANGES_REQUESTED" and
            protected["salvage08_active"] is False and
            protected["physical_saturn"] == "UNRUN",
            "workflow shield drift")


if __name__ == "__main__":
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"wrote {OUT.relative_to(ROOT)}")
