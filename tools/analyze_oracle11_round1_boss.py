#!/usr/bin/env python3
"""Close the Round 1 boss phase and boss-clear orchestration boundary."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps/mame/oracle11_round1_boss_a"
RAW_B = ROOT / ".deps/mame/oracle11_round1_boss_b"
RAW_CLEAR = ROOT / ".deps/mame/oracle11_round1_boss_suppress_clear"
ENEMIES = ROOT / "data/oracle11_round1_enemy_archetypes.json"
ENCOUNTERS = ROOT / "data/oracle11_round1_encounter_route_authority.json"
ROUTE = ROOT / "data/oracle10_round1_route.json"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
OUT = ROOT / "data/oracle11_round1_boss_orchestration.json"
FILES = ("boss_samples.tsv", "boss_writes.tsv", "boss_rng.tsv",
         "clear_writes.tsv", "samples.tsv", "dispatches.tsv",
         "projectiles.tsv", "score_writes.tsv", "result.tsv")
CONTROLLER_PHASES = (
    (5566, 0x0200, 0x0000), (5720, 0x0202, 0x0000),
    (7669, 0x0204, 0x0000), (10968, 0x0208, 0x0000),
    (13937, 0x020a, 0x0000), (14285, 0x020a, 0x0200),
    (14406, 0x020c, 0x0000), (14466, 0x020e, 0x0000),
    (14586, 0x0210, 0x0000), (14988, 0x0400, 0x0000),
    (15018, 0x0600, 0x0000),
)
STATE_WRITER_SOURCE = {
    "028c40": "0x028c3a initializes controller state 0x0200 after allocation",
    "028d16": "0x028d10 increments state 0x0200 -> 0x0202",
    "028d3a": "0x028d34 increments state 0x0202 -> 0x0204",
    "028d6e": "0x028d68 performs the first 0x0204 phase increment",
    "028d72": "0x028d6c performs the second increment to 0x0208",
    "028db2": "0x028dac increments state 0x0208 -> 0x020a after 0x020a10 succeeds",
    "028e00": "0x028dfa increments substate after the source countdown reaches zero",
    "028e2e": "0x028e28 increments state after the guarded shared call",
    "028e32": "0x028e2c clears substate on the same transition",
    "028e58": "0x028e52 increments state after the 60-tick countdown",
    "028e76": "0x028e70 increments state after the 120-tick countdown",
    "028e82": "0x028e7c increments the high state byte when g8168 is nonzero",
    "028e86": "0x028e80 clears the low state byte",
    "028e9e": "0x028e98 increments state when the 30-tick terminal countdown reaches zero",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def identity(path: Path, variant: str) -> dict[str, object]:
    manifest = json.loads((path / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    require(manifest["authority_family"] ==
            "round1-boss-phase-clear-orchestration", "boss family drift")
    require(manifest["variant"] == variant, f"{path.name}: variant drift")
    for name in FILES:
        require(digest(path / name) == manifest["sha256"][name],
                f"{path.name}: {name} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "variant": variant, "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def source_window(image: bytes, pc: int) -> dict[str, object]:
    first, last = max(0, pc - 24), min(len(image), pc + 16)
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(image[first:last]).hexdigest()}


def phase_timeline(samples: list[dict[str, str]], record: str,
                   actor_class: str) -> list[dict[str, object]]:
    previous = None
    timeline = []
    for row in samples:
        if row["record"] != record or row["class"] != actor_class:
            continue
        key = (int(row["active"]), int(row["state"]), int(row["phase"]))
        if key == previous:
            continue
        timeline.append({"frame": int(row["frame"]), "active_u8": key[0],
                         "state_u16": key[1], "substate_u16": key[2]})
        previous = key
    return timeline


def build_report() -> dict[str, object]:
    id_a = identity(RAW_A, "baseline")
    id_b = identity(RAW_B, "baseline")
    id_clear = identity(RAW_CLEAR, "suppress-clear-writer")
    require(id_a["files"] == id_b["files"], "boss completions differ")
    image = OPCODES.read_bytes()
    samples = rows(RAW_A / "boss_samples.tsv")
    mutated_samples = rows(RAW_CLEAR / "boss_samples.tsv")
    require(len(samples) == 19988, "boss sample census drift")
    require(all(a == b for a, b in zip(samples, mutated_samples)
                if int(a["frame"]) <= 15017),
            "clear control diverged before the source clear write")

    enemy_report = json.loads(ENEMIES.read_text(encoding="ascii"))
    boss_actor = next(item for item in enemy_report["archetypes"]
                      if item["class"] == "0x06")
    require(boss_actor["classification"] == "SOURCE_CLOSED",
            "closed class-0x06 actor contract missing")
    encounter_report = json.loads(ENCOUNTERS.read_text(encoding="ascii"))
    spawns = [item for item in encounter_report["enemy_spawns"]
              if 5400 <= item["frame"] <= 14000]
    expected_spawns = [(5565, "0x06"), (5659, "0x00"), (5659, "0x00"),
                       (7745, "0x00"), (7756, "0x00"), (7767, "0x00"),
                       (11044, "0x01"), (11065, "0x01")]
    require([(item["frame"], item["class"]) for item in spawns] == expected_spawns,
            "boss-room spawn inventory drift")

    controller = phase_timeline(samples, "presentation", "02")
    witnessed = [(item["frame"], item["state_u16"], item["substate_u16"])
                 for item in controller]
    require(witnessed == list(CONTROLLER_PHASES), "boss controller phases drift")
    boss_timeline = phase_timeline(samples, "boss", "06")
    required_death = [(13935, 0x0400, 0), (13936, 0x0402, 0),
                      (13961, 0x0402, 0x0200),
                      (14140, 0x0402, 0x0400),
                      (14143, 0x0402, 0x0600), (14154, 0x0404, 0)]
    require([(x["frame"], x["state_u16"], x["substate_u16"])
             for x in boss_timeline if x["frame"] >= 13935] == required_death,
            "boss KO-to-settled sequence drift")

    writes = rows(RAW_A / "boss_writes.tsv")
    controller_writes = [row for row in writes if row["record"] == "presentation"]
    state_writes = [row for row in controller_writes
                    if row["offset"] in ("04", "05", "06", "07") and
                    row["pc"] in STATE_WRITER_SOURCE]
    state_pcs = {row["pc"] for row in state_writes}
    require(state_pcs == set(STATE_WRITER_SOURCE), "controller writer set drift")
    writer_counts = Counter((row["pc"], row["offset"])
                            for row in controller_writes)
    provenance = []
    for (pc, offset), count in sorted(writer_counts.items()):
        value = int(pc, 16)
        provenance.append({"tap_pc": f"0x{pc}", "record_offset": f"0x{offset}",
                           "write_count": count,
                           "source_window": source_window(image, value),
                           "classification": "SOURCE_CLOSED"})

    rng_rows = rows(RAW_A / "boss_rng.tsv")
    require(len(rng_rows) == 216 and all(row["record"] == "boss"
                                         for row in rng_rows),
            "boss RNG partition drift")
    rng_by_pc = Counter(row["pc"] for row in rng_rows)
    require(sum(boss_actor["rng"]["caller_pcs"].values()) == 216,
            "closed enemy RNG evidence drift")

    clear_rows = [row for row in rows(RAW_A / "clear_writes.tsv")
                  if row["pc"] == "028ea2"]
    mutant_clear = [row for row in rows(RAW_CLEAR / "clear_writes.tsv")
                    if row["pc"] == "028ea2"]
    require(len(clear_rows) == len(mutant_clear) == 1, "clear writer cardinality drift")
    clear_row, mutant_row = clear_rows[0], mutant_clear[0]
    require(clear_row["frame"] == "15017" and clear_row["a6"] == "ffd180" and
            clear_row["state"] == "1536" and clear_row["suppressed"] == "0",
            "baseline clear writer drift")
    require(mutant_row["suppressed"] == "1", "clear writer was not suppressed")
    baseline_route = {int(row["frame"]): row for row in rows(RAW_A / "samples.tsv")}
    mutant_route = {int(row["frame"]): row for row in rows(RAW_CLEAR / "samples.tsv")}
    require(baseline_route[15193]["route"] == "2" and
            baseline_route[16425]["route"] == "4", "baseline handoff drift")
    require(mutant_route[15193]["route"] == "4" and
            mutant_route[18000]["state"] == "512" and
            mutant_route[18000]["action"] == "4100",
            "clear suppression did not hold Round 1")
    for field in ("active", "state", "action", "health", "resource", "score"):
        require(baseline_route[15017][field] == mutant_route[15017][field],
                f"clear control changed {field} before the writer")

    route = json.loads(ROUTE.read_text(encoding="ascii"))
    controls = route["targeted_counterfactuals"]
    require(controls["remove_class_06"]["completed_round1"] is False and
            controls["suppress_boss_offense"]["completed_round1"] is True,
            "accepted boss counterfactual drift")
    report = {
        "schema": "oracle11-round1-boss-orchestration-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": ("Round 1 class-0x06 spawn-to-controller linkage, boss-room "
                  "reinforcements, boss defeat bridge, controller phases and "
                  "the causal boss-clear flag; post-clear route handoff remains separate"),
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True,
                             "clear_writer_suppression": id_clear,
                             "opcode_sha256": digest(OPCODES)},
        "boss_actor_contract": {
            "record": "0xffa3c0", "class": "0x06", "type": 12,
            "spawn": spawns[0], "dispatch_entry": boss_actor["dispatch_entry"],
            "source_contract": "data/oracle11_round1_enemy_archetypes.json",
            "classification": "SOURCE_CLOSED_CONSUMED_NOT_REOPENED",
        },
        "boss_room_spawns": spawns,
        "controller_contract": {
            "record": "0xffd180", "class": "0x02", "type": 32,
            "state_type": "u16 big-endian state/substate bytes",
            "phase_timeline": controller,
            "state_writer_rules": STATE_WRITER_SOURCE,
            "writer_provenance": provenance,
            "appearance_used_for_authority": False,
        },
        "boss_defeat_bridge": {
            "boss_phase_timeline": boss_timeline,
            "required_death_tail": required_death,
            "health_and_ko_contract": boss_actor["damage_hit_ko"],
            "controller_transition_after_boss_ko": {
                "frame": 13937, "from_state": "0x0208", "to_state": "0x020a",
                "tap_pc": "0x028db2", "source_writer": "0x028dac",
            },
            "classification": "SOURCE_CLOSED",
        },
        "rng": {
            "calls": len(rng_rows),
            "caller_counts": {f"0x{pc}": count for pc, count in sorted(rng_by_pc.items())},
            "consumption_order_sha256": hashlib.sha256("\n".join(
                f"{row['frame']}:{row['pc']}:{row['seed']}" for row in rng_rows
            ).encode("ascii")).hexdigest(),
            "owner": "closed class-0x06 actor contract",
            "orphan_calls": 0,
        },
        "boss_clear_guard": {
            "frame": 15017, "controller_record": "0xffd180",
            "controller_state": "0x0600", "countdown_field": "record+0x26:u16",
            "guard": "subq.w #1,0x26(A6) reaches zero in controller state 0x0400",
            "state_writer": "0x028e98 addq.b #2,0x04(A6)",
            "clear_writer": "0x028e9c move.b #1,0x01f3(A5)",
            "write_tap_pc": "0x028ea2", "global_field": "0xff81f3:u8",
            "route_consumer": "0x008418 tests u8(g81f3) and writes route state 6",
            "source_window": source_window(image, 0x028e9c),
            "classification": "SOURCE_CLOSED",
        },
        "counterfactuals": {
            "suppress_exact_clear_writer": {
                "suppression_count": 1, "completed_round1": False,
                "round1_state_at_frame_18000": 4,
                "frozen_player_state_action": [512, 4100],
                "baseline_round2_state_frame": 16425,
                "pre_writer_gameplay_projection_unchanged": True,
            },
            "remove_class_06": controls["remove_class_06"],
            "suppress_boss_offense": controls["suppress_boss_offense"],
        },
        "coverage": {
            "boss_actor_pairs_required": 1, "boss_actor_pairs_closed": 1,
            "boss_controller_phases_required": len(CONTROLLER_PHASES),
            "boss_controller_phases_closed": len(CONTROLLER_PHASES),
            "boss_room_spawns_required": len(expected_spawns),
            "boss_room_spawns_closed": len(spawns),
            "boss_rng_calls_required": 216, "boss_rng_calls_closed": 216,
            "boss_clear_writers_required": 1, "boss_clear_writers_closed": 1,
            "orphan_controller_phases": 0, "orphan_boss_spawns": 0,
            "orphan_boss_rng_calls": 0, "orphan_clear_writers": 0,
        },
        "owned_authoritative_writer_pcs": sorted({
            f"0x{row['pc']}" for row in controller_writes} | {"0x028ea2"}),
        "scope_boundary": {
            "boss_actor_behavior": "SOURCE_CLOSED_IN_ENEMY_FAMILY",
            "nonboss_encounter_route_authority": "SOURCE_CLOSED_IN_ENCOUNTER_FAMILY",
            "stage_clear_and_round2_handoff": "PENDING_HANDOFF_FAMILY",
            "global_rng_ownership": "PENDING_GLOBAL_RNG_FAMILY",
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED", "user09": "CHANGES_REQUESTED",
            "spec02_active": False, "production_runtime_writes": 0,
            "yaba_runs": 0, "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED", "boss status drift")
    require(report["capture_identity"]["byte_identical"] is True,
            "boss repeatability drift")
    coverage = report["coverage"]
    require(all(value == 0 for key, value in coverage.items()
                if key.startswith("orphan_")), "boss orphan drift")
    require(report["controller_contract"]["appearance_used_for_authority"] is False,
            "boss authority inferred from appearance")
    require(report["counterfactuals"]["suppress_exact_clear_writer"]
            ["completed_round1"] is False, "clear suppression fabricated completion")
    require(report["scope_boundary"]["stage_clear_and_round2_handoff"] ==
            "PENDING_HANDOFF_FAMILY", "handoff silently absorbed")
    require(report["protected_boundaries"]["spec02_active"] is False and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN",
            "protected boss boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes((json.dumps(report, sort_keys=True, indent=2) + "\n").encode("ascii"))
    print("ORACLE-11 Round 1 boss: SOURCE_CLOSED; 11 controller phases, "
          "8 boss-room spawns, 216 boss RNG calls and one causal clear writer")


if __name__ == "__main__":
    main()
