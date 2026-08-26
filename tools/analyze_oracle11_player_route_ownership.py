#!/usr/bin/env python3
"""Close route-wide Predator Warrior interaction/resource ownership."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle11_player_route_ownership_a"
RAW_UNINTERRUPTED = (ROOT / ".deps" / "mame" /
                     "oracle11_player_route_ownership_b")
RAW_RESOURCE = ROOT / ".deps" / "mame" / "oracle11_player_route_ownership_e"
EVENT_A = ROOT / ".deps" / "mame" / "oracle11_player_route_events_a"
EVENT_B = ROOT / ".deps" / "mame" / "oracle11_player_route_events_b"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
OUT = ROOT / "data" / "oracle11_predator_route_ownership.json"

ACTION_OWNERS = {
    0x0000: "locomotion-neutral", 0x0002: "locomotion-neutral",
    0x0200: "locomotion-neutral", 0x0202: "locomotion-neutral",
    0x0204: "locomotion-neutral", 0x0206: "route-reachable-melee",
    0x0208: "route-reachable-melee", 0x020A: "route-reachable-melee",
    0x020C: "route-reachable-melee", 0x020E: "route-reachable-melee",
    0x0400: "directional-airborne", 0x0402: "directional-airborne",
    0x0404: "directional-airborne", 0x0406: "directional-airborne",
    0x0600: "route-reachable-melee",
    0x0800: "weapon-projectile-resource", 0x0802: "weapon-projectile-resource",
    0x0804: "weapon-projectile-resource", 0x0806: "weapon-projectile-resource",
    0x0808: "weapon-projectile-resource", 0x080A: "weapon-projectile-resource",
    0x080C: "weapon-projectile-resource",
    0x0C00: "weapon-projectile-resource", 0x0C02: "weapon-projectile-resource",
    0x0C04: "weapon-projectile-resource",
    0x0E00: "route-interaction",
    0x1000: "external-stage-clear-route-edge",
    0x1002: "external-stage-clear-route-edge",
    0x1004: "external-stage-clear-route-edge",
    0x1202: "hit-ko-failure-continue-respawn",
    0x1204: "hit-ko-failure-continue-respawn",
    0x1400: "route-reachable-melee", 0x1402: "route-reachable-melee",
    0x1A00: "weapon-projectile-resource", 0x1A02: "weapon-projectile-resource",
}

LOAD_WINDOWS = ((5530, 5580), (6170, 6230), (12770, 12830))
BULK_LOAD_PCS = {
    "0ac1be", "0ac1c2", "0ac1c6", "0ac1ca", "0b1b9a", "0b1ba6",
    "018420", "018422", "018424", "018426", "018428", "01842a",
    "01842c", "01842e", "018430", "018432", "018434", "018436",
    "018438", "01843a", "01843c", "01843e",
}
PLAYER_PRESENTATION_PCS = {
    "0ae048", "016fc2", "0aded0", "008f7e", "0b27e8", "0b27ea",
    "008dc0", "0abd44", "0abd46", "0b2cf2", "0b2cf4", "0abd24",
    "0abd26", "0adf08", "0ade9a", "0ade8a", "0ade84", "0ade92",
    "0aecdc", "0aecde", "0aecd8", "0aece0", "0aecda", "0aec8c",
    "0aec70", "0aec66", "0aec68", "0aec72", "0aec86", "0aec7c",
    "0aec84", "0aec7a", "0aec54", "0ae2e6", "0aec48", "0aec4e",
    "0aec4c", "0aec4a", "0aec46", "0aec40", "0aec42", "0aec44",
    "00efc6", "00efa0", "00efa4", "00efc2", "00efaa", "00efbc",
    "00efb8", "00efae", "0ae0be", "0ae0c2", "0ae0cc", "0ae0c8",
    "0ae140", "0ae142", "0ae146", "0ae150", "0ae154", "0ae148",
    "0addf8", "0adde4", "0ae2f4",
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


def samples(path: Path) -> dict[int, dict[str, int | str]]:
    result = {}
    for row in rows(path):
        converted = {key: (value if key == "variant" else int(value))
                     for key, value in row.items()}
        result[int(row["frame"])] = converted
    return result


def manifest_identity(base: Path, variants: tuple[str, ...]) -> dict[str, object]:
    manifest_path = base / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    selected = []
    by_name = {item["name"]: item for item in manifest["variants"]}
    for name in variants:
        require(name in by_name, f"missing declared capture variant {name}")
        item = by_name[name]
        for filename, expected in item["sha256"].items():
            require(digest(base / name / filename) == expected,
                    f"{name}: {filename} identity drift")
        selected.append(item)
    return {"manifest_sha256": digest(manifest_path), "variants": selected}


def write_exists(source: list[dict[str, str]], frame: int, pc: str,
                 offset: str | None = None, data: str | None = None) -> bool:
    return any(int(row["frame"]) == frame and row["pc"] == pc and
               (offset is None or row["offset"] == offset) and
               (data is None or row["data"] == data) for row in source)


def ranges(values: list[tuple[int, int]], action: int) -> list[list[int]]:
    frames = [frame for frame, value in values if value == action]
    result: list[list[int]] = []
    for frame in frames:
        if not result or frame != result[-1][1] + 1:
            result.append([frame, frame])
        else:
            result[-1][1] = frame
    return result


def source_window(data: bytes, start: int, end: int) -> dict[str, object]:
    return {"start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
            "bytes": end - start,
            "sha256": hashlib.sha256(data[start:end]).hexdigest()}


def build_report() -> dict[str, object]:
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()
    require(len(opcodes) == len(program) == 0x200000,
            "decoded source image size drift")

    identity_a = manifest_identity(
        RAW, ("route_interaction_1", "route_interaction_2", "health_max",
              "effect_pool_unavailable"))
    identity_u = manifest_identity(RAW_UNINTERRUPTED,
                                   ("interaction_uninterrupted",))
    identity_r = manifest_identity(RAW_RESOURCE, ("resource_pickup_near",))
    for filename in ("samples.tsv", "writes.tsv", "actors.tsv", "qsound.tsv"):
        require(digest(RAW / "route_interaction_1" / filename) ==
                digest(RAW / "route_interaction_2" / filename),
                f"independent interaction controls differ: {filename}")

    event_manifest_a = json.loads((EVENT_A / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    event_manifest_b = json.loads((EVENT_B / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    for base, manifest in ((EVENT_A, event_manifest_a),
                           (EVENT_B, event_manifest_b)):
        for filename, expected in manifest["sha256"].items():
            require(digest(base / filename) == expected,
                    f"route event identity drift: {base.name}/{filename}")
    require(event_manifest_a["sha256"] == event_manifest_b["sha256"],
            "independent route-event controls differ")

    baseline = samples(RAW / "route_interaction_1" / "samples.tsv")
    health_max = samples(RAW / "health_max" / "samples.tsv")
    no_effect = samples(RAW / "effect_pool_unavailable" / "samples.tsv")
    uninterrupted = samples(RAW_UNINTERRUPTED / "interaction_uninterrupted" /
                            "samples.tsv")
    resource = samples(RAW_RESOURCE / "resource_pickup_near" / "samples.tsv")
    baseline_writes = rows(RAW / "route_interaction_1" / "writes.tsv")
    max_writes = rows(RAW / "health_max" / "writes.tsv")
    resource_writes = rows(RAW_RESOURCE / "resource_pickup_near" / "writes.tsv")
    resource_actors = rows(RAW_RESOURCE / "resource_pickup_near" / "actors.tsv")

    require(baseline[3101]["health"] == 85 and baseline[3102]["health"] == 95 and
            all(baseline[f]["action"] == 0x0E00 for f in range(3102, 3108)),
            "natural health interaction drift")
    require(write_exists(baseline_writes, 3101, "019ff2", "06", "0e0e") and
            write_exists(baseline_writes, 3101, "019ff8", "06", "0000") and
            write_exists(baseline_writes, 3101, "0bc638", "40", "005f") and
            write_exists(baseline_writes, 3101, "0bc64a", "42", "005f"),
            "natural health writer set drift")
    require(health_max[3101]["health"] == 101 and
            health_max[3102]["action"] == 0x0E00 and
            not any(int(row["frame"]) == 3101 and
                    row["pc"] in {"0bc638", "0bc64a"} for row in max_writes),
            "maximum-health alternate branch drift")
    require(no_effect[4032]["action"] == 0x0E00 and
            no_effect[4032]["r24_free"] >= 0 and no_effect[4033]["health"] == 30,
            "effect-pool isolation changed gameplay interaction")

    require(all(uninterrupted[f]["action"] == 0x0E00
                for f in range(4032, 4060)) and
            uninterrupted[4060]["action"] == 0 and
            baseline[4051]["action"] == 0x0E00 and
            baseline[4052]["action"] == 0x0C00,
            "interaction completion/interruption boundary drift")

    require(all(resource[f]["award"] == 0 for f in range(3997, 4002)) and
            all(resource[f]["award"] == 600 for f in range(4002, 4006)) and
            resource[4002]["action"] == 0x0E00,
            "temporary resource award drift")
    require(all(write_exists(resource_writes, frame, "01cec2", "8e", "cd00")
                for frame in range(3997, 4001)) and
            write_exists(resource_writes, 4001, "019ff2", "06", "0e0e") and
            write_exists(resource_writes, 4001, "019ff8", "06", "0000") and
            write_exists(resource_writes, 4001, "01a1bc", "82", "5454") and
            write_exists(resource_writes, 4001, "01a1c6", "ae", "0258"),
            "resource target/grant writer identity drift")
    require(any(int(row["frame"]) == 4002 and row["class"] == "54"
                for row in resource_actors), "class-0x54 display actor missing")

    event_rows = rows(EVENT_A / "samples.tsv")
    action_values = [(int(row["frame"]), int(row["action"]))
                     for row in event_rows]
    observed_actions = sorted({value for _, value in action_values})
    unmapped = [value for value in observed_actions if value not in ACTION_OWNERS]
    require(not unmapped, f"unmapped route-reachable player actions: {unmapped}")
    require(ranges(action_values, 0x0E00) ==
            [[3102, 3107], [4032, 4051], [17522, 17549]],
            "route interaction interval census drift")
    require(all(int(row["award"]) == 0 for row in event_rows),
            "baseline route unexpectedly reaches temporary resource pickup")

    gfx_rows = rows(EVENT_A / "gfx_writes.tsv")
    load_rows = [row for row in gfx_rows if any(
        first <= int(row["frame"]) <= last for first, last in LOAD_WINDOWS)]
    observed_bulk = {row["pc"] for row in load_rows if row["pc"] in BULK_LOAD_PCS}
    require(observed_bulk == BULK_LOAD_PCS, "bulk loader writer set drift")
    require(not any(row["pc"] in BULK_LOAD_PCS and row["a6"] == "ff8380"
                    for row in load_rows),
            "bulk load/release was attributed to the player actor")
    player_gfx = {row["pc"] for row in load_rows if row["a6"] == "ff8380"}
    require(player_gfx == PLAYER_PRESENTATION_PCS,
            "player-keyed HUD/transition presentation writer set drift")
    require(len(rows(EVENT_A / "audio_writes.tsv")) == 0,
            "main-program audio tap unexpectedly became a causal ledger")

    report = {
        "schema": "oracle11-predator-route-ownership-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "PARTIAL",
        "scope": ("Predator Warrior route-reachable action-phase, target, health "
                  "pickup, temporary-resource grant, interaction interruption, "
                  "resource-meter, player-owned audio-call and load/release-edge "
                  "ownership; other actors and route systems remain separate "
                  "ORACLE-11 authority families"),
        "coverage_universe": {
            "rule": ("union of both baseline completions, completing perturbations, "
                     "failure/continue, and targeted counterfactual routes"),
            "routes": ["baseline-completion-a", "baseline-completion-b",
                       "perturbed-completions", "failure-continue",
                       "targeted-counterfactuals"],
            "independent_route_event_controls_byte_identical": True,
            "independent_interaction_controls_byte_identical": True,
        },
        "action_phase_reconciliation": {
            "observed": [f"0x{value:04x}" for value in observed_actions],
            "owner_by_phase": {f"0x{value:04x}": ACTION_OWNERS[value]
                               for value in observed_actions},
            "interaction_intervals": ranges(action_values, 0x0E00),
            "unmapped_player_phases": [],
            "external_edge": ("0x1000/0x1002/0x1004 are written by the "
                              "stage-clear/route family; their player-facing "
                              "phase identity is mapped here but their route "
                              "guard remains outside player authority"),
        },
        "health_pickup": {
            "classification": "SOURCE_CLOSED",
            "target_pool": "record28 0xffc680 base, 16 slots, 0x80 stride",
            "natural_target": "0xffcd00 class0x0a subtype0x12",
            "target_scan": "0x01ce98..0x01cece; 0x01cec2 writes player +0x8e",
            "dispatch": "0x019fec..0x01a174 to 0x0bc5fc",
            "health_rule": ("zero establishes 5, subtype table amount is added, "
                            "then clamped to 101 and copied to +0x42"),
            "natural_witness": {"entry_frame": 3102, "health_before": 85,
                                "health_after": 95, "target": "0xffcd00"},
            "max_health_control": ("health 101 preserves the same 0x0e00 action "
                                   "but skips the health and latch writers and "
                                   "takes the source alternate-audio branch"),
            "effect_actor_is_gameplay_authority": False,
            "remaining_unknowns": [],
        },
        "temporary_resource_pickup": {
            "classification": "SOURCE_CLOSED",
            "source_body": "0x01a196..0x01a1d8",
            "target": "record28 class0x0e at 0xffcd00",
            "grant": {"field": "player +0xae u16", "value": 600,
                      "writer": "0x01a1c6"},
            "display_actor": {"pool": "record24", "class": "0x54",
                              "allocation_writer": "0x01a1bc",
                              "gameplay_authority": False},
            "targeted_control": ("changes only the live class0x0e actor position "
                                 "and supplies one real Button2 edge after native "
                                 "target acquisition"),
            "natural_route_reachable": False,
            "natural_route_classification": "NOT_REQUIRED_FOR_ROUND1",
            "source_body_closed_for_mutation_coverage": True,
            "remaining_unknowns": [],
        },
        "interaction_action_and_interruption": {
            "classification": "SOURCE_CLOSED",
            "action": "0x0e00",
            "natural_completion": {"entry": 4032, "last": 4059,
                                   "return_to_neutral": 4060},
            "button_interruption": {"baseline_last": 4051,
                                    "next_action": "0x0c00",
                                    "next_frame": 4052},
            "effect_actor": ("record24 class0x20 is presentation/coordination; "
                             "pool unavailability does not change gameplay result"),
            "remaining_unknowns": [],
        },
        "resource_meter": {
            "classification": "SOURCE_CLOSED",
            "fields": {"meter": "+0x8c u8", "recharge": "+0x8d u8",
                       "depleted": "+0x8b u8", "temporary_award": "+0xae u16"},
            "authority": ("debit/recharge remains bound by the accepted weapon "
                          "artifact; pickup grant is independently bound above"),
            "remaining_unknowns": [],
        },
        "audio_ownership": {
            "classification": "PARTIAL_CROSS_FAMILY",
            "health_max_score_award": ("0x0bc5fc..0x0bc664 jumps 0x0abdd2; "
                                       "this is BCD score authority, not audio"),
            "score_award": {
                "routine": "0x0abdd2..0x0abe18",
                "amount_index": "D0 u8 indexes 0x0abf1c",
                "player_index": "D1 low two bits select A5+0x380 plus index*0x100",
                "arithmetic": "four ABCD operations into score bytes +0xe0..+0xe3",
                "maximum_guard": "unsigned compare against packed BCD 0x09999999",
            },
            "route_audio_owner": "gameplay-audio-load-release",
            "causal_scope_guard": ("the empty main-program audio-write tap is not "
                                   "used to infer silence or route-wide ownership"),
            "remaining_player_unknowns": [
                "identify every player-origin gameplay-audio trigger through the real main-to-QSound command boundary"
            ],
        },
        "load_release_ownership": {
            "classification": "SOURCE_CLOSED_FOR_PLAYER_EDGE",
            "route_windows": [list(value) for value in LOAD_WINDOWS],
            "bulk_loader_pcs": sorted(BULK_LOAD_PCS),
            "bulk_loader_uses_player_actor_base": False,
            "player_keyed_gfx_pcs": sorted(PLAYER_PRESENTATION_PCS),
            "player_keyed_gfx_classification": "HUD_OR_ROUTE_TRANSITION_PRESENTATION",
            "route_load_release_owner": "gameplay-audio-load-release",
            "remaining_player_unknowns": [],
        },
        "external_authority_edges": {
            "stage_clear_action_phases": "stage-clear-failure-continue-round2-handoff",
            "pickup_actor_lifecycle": "pickups-equipment-weapons-projectiles-hazards-destructibles",
            "route_audio": "gameplay-audio-load-release",
            "route_load_release": "gameplay-audio-load-release",
            "hud_and_transition_gfx": "presentation infrastructure / route family",
            "note": ("these mapped edges are not player unknowns and do not close "
                     "their owning Round 1 families"),
        },
        "source_identity": {
            "decoded_opcodes_sha256": hashlib.sha256(opcodes).hexdigest(),
            "decrypted_program_sha256": hashlib.sha256(program).hexdigest(),
            "target_scan": source_window(opcodes, 0x01CE98, 0x01CECE),
            "interaction_dispatch": source_window(opcodes, 0x019FEC, 0x01A1D8),
            "health_item": source_window(opcodes, 0x0BC5FC, 0x0BC664),
            "bcd_score_award": source_window(opcodes, 0x0ABDD2, 0x0ABE18),
            "interaction_effect": source_window(opcodes, 0x01ABFC, 0x01AC48),
            "record28_scheduler": source_window(opcodes, 0x01BCDA, 0x01BD48),
            "class54_display": source_window(opcodes, 0x094B3A, 0x094BF0),
        },
        "capture_identity": {
            "interaction": identity_a, "uninterrupted": identity_u,
            "resource": identity_r,
            "route_events": {"a_manifest_sha256": digest(EVENT_A / "input_manifest.json"),
                             "b_manifest_sha256": digest(EVENT_B / "input_manifest.json"),
                             "files": event_manifest_a["sha256"]},
        },
        "mutation_controls": {
            "count": 10,
            "classes": ["independent-launch identity", "health clamp",
                        "health writer", "target acquisition", "resource grant",
                        "display actor separation", "interaction interruption",
                        "action-phase mapping", "audio edge", "load edge"],
        },
        "remaining_player_unknowns": [
            "player-to-global gameplay-audio trigger ownership pending real dispatcher closure"
        ],
        "protected_boundaries": {
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "PARTIAL", "route ownership status drift")
    require(report["action_phase_reconciliation"]["unmapped_player_phases"] == [],
            "unmapped player action phase")
    require(report["health_pickup"]["classification"] == "SOURCE_CLOSED" and
            report["health_pickup"]["natural_witness"]["health_after"] == 95,
            "health pickup authority drift")
    require(report["temporary_resource_pickup"]["grant"]["value"] == 600 and
            report["temporary_resource_pickup"]["natural_route_classification"] ==
            "NOT_REQUIRED_FOR_ROUND1", "resource pickup authority drift")
    require(report["interaction_action_and_interruption"]["natural_completion"] ==
            {"entry": 4032, "last": 4059, "return_to_neutral": 4060},
            "interaction completion drift")
    require(report["audio_ownership"]["route_audio_owner"] ==
            "gameplay-audio-load-release" and
            len(report["audio_ownership"]["remaining_player_unknowns"]) == 1 and
            "BCD score" in report["audio_ownership"]["health_max_score_award"],
            "audio edge drift")
    require(report["load_release_ownership"]["bulk_loader_uses_player_actor_base"]
            is False and
            report["load_release_ownership"]["remaining_player_unknowns"] == [],
            "load/release edge drift")
    require(len(report["remaining_player_unknowns"]) == 1 and
            report["mutation_controls"]["count"] == 10,
            "route ownership backlog drift")
    require(report["protected_boundaries"] == {
        "production_runtime_writes": 0, "yaba_runs": 0,
        "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
        "salvage08_active": False, "physical_saturn": "UNRUN",
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 Predator route pickup/resource/load ownership closed; real audio trigger boundary PARTIAL")


if __name__ == "__main__":
    main()
