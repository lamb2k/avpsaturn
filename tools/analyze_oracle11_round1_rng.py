#!/usr/bin/env python3
"""Close the route-wide Round 1 source RNG algorithm and consumption ledger."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps/mame/oracle11_round1_route_a"
RAW_B = ROOT / ".deps/mame/oracle11_round1_route_b"
ENEMY_A = ROOT / ".deps/mame/oracle11_round1_enemies_a/enemy_rng.tsv"
AUX_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a/aux_rng.tsv"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ROUTE = ROOT / "data/oracle10_round1_route.json"
ENEMIES = ROOT / "data/oracle11_round1_enemy_archetypes.json"
AUXILIARY = ROOT / "data/oracle11_round1_auxiliary_authority.json"
COFFEE_STAGE_A = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs13a"
COFFEE_STAGE_B = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs13b"
COFFEE_STAGE_SUPPRESS = ROOT / ".deps/mame/oracle11_progression_lifecycle_cs10s"
OUT = ROOT / "data/oracle11_round1_rng.json"
FILES = ("route_samples.tsv", "route_writes.tsv", "route_writer_summary.tsv",
         "lifecycle_writes.tsv", "route_rng.tsv", "samples.tsv", "dispatches.tsv",
         "projectiles.tsv", "score_writes.tsv", "result.tsv")


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
            "encounters-waves-scripted-triggers", "route family drift")
    require(manifest["variant"] == "baseline", "route variant drift")
    for name in FILES:
        require(digest(path / name) == manifest["sha256"][name],
                f"{path.name}: {name} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "variant": manifest["variant"], "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def source_window(image: bytes, first: int, last: int) -> dict[str, object]:
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(image[first:last]).hexdigest()}


def next_seed(seed: int) -> int:
    high = ((3 * seed) & 0xffff) >> 8
    low = ((seed & 0xff) + high) & 0xff
    return (high << 8) | low


def in_pool(address: str, base: int, stride: int, count: int) -> bool:
    value = int(address, 16)
    return base <= value < base + stride * count and (value - base) % stride == 0


def enemy_key(row: dict[str, str]) -> tuple[str, ...]:
    return (row["frame"], row.get("slot", row.get("a6", "")),
            row.get("class", row.get("owner_class", "")),
            row.get("state", row.get("owner_state", "")),
            row.get("phase", row.get("owner_phase", "")), row["pc"], row["seed"],
            row["return0"], row["return1"], row["return2"])


def aux_key(row: dict[str, str]) -> tuple[str, ...]:
    return (row["frame"], row.get("slot", row.get("a6", "")), row["pc"],
            row["seed"], row["return0"], row["return1"], row["return2"])


def build_report() -> dict[str, object]:
    id_a, id_b = identity(RAW_A), identity(RAW_B)
    require(id_a["files"] == id_b["files"], "route RNG completions differ")
    rng = rows(RAW_A / "route_rng.tsv")
    require(len(rng) == 2280, "route RNG call census drift")
    frames = Counter(int(row["frame"]) for row in rng)
    require(len(frames) == 1023, "RNG seed-change frame census drift")
    for index, row in enumerate(rng[:-1]):
        require(next_seed(int(row["seed"], 16)) == int(rng[index + 1]["seed"], 16),
                f"RNG recurrence/order gap at call {index}")

    enemy = [row for row in rng if in_pool(row["a6"], 0xff9580, 0xc0, 20)]
    auxiliary = [row for row in rng if any(in_pool(row["a6"], base, 0x80, count)
                for base, count in ((0xffa480, 20), (0xffae80, 16),
                                    (0xffb680, 32)))]
    global_rows = [row for row in rng if row not in enemy and row not in auxiliary]
    require(len(enemy) == 893 and len(auxiliary) == 1348 and len(global_rows) == 39,
            "RNG owner partition drift")
    require([enemy_key(row) for row in enemy] ==
            [enemy_key(row) for row in rows(ENEMY_A)],
            "enemy RNG partition/order drift")
    require([aux_key(row) for row in auxiliary] ==
            [aux_key(row) for row in rows(AUX_A)],
            "auxiliary RNG partition/order drift")
    enemy_report = json.loads(ENEMIES.read_text(encoding="ascii"))
    auxiliary_report = json.loads(AUXILIARY.read_text(encoding="ascii"))
    require(enemy_report["status"] == auxiliary_report["status"] == "SOURCE_CLOSED",
            "accepted actor RNG contracts drift")
    require(sum(item["rng"]["calls"] for item in enemy_report["archetypes"]) == 893,
            "enemy RNG report total drift")
    dispatched_aux_calls = sum(item["rng"]["calls"]
                               for item in auxiliary_report["archetypes"])
    require(dispatched_aux_calls == 1288 and
            auxiliary_report["capture_identity"]["rng_rows"] == 1348,
            "auxiliary RNG report/capture total drift")
    aux_pairs = Counter((row["type"], row["class"]) for row in rows(AUX_A))
    transient_aux = {
        "type24-class47": aux_pairs[("24", "47")],
        "type24-class25": aux_pairs[("24", "25")],
        "type24-class4d": aux_pairs[("24", "4d")],
        "type20-class05": aux_pairs[("20", "05")],
    }
    require(transient_aux == {"type24-class47": 28, "type24-class25": 20,
                              "type24-class4d": 11, "type20-class05": 1},
            "transient auxiliary RNG partition drift")

    coffee_stage_files = ("coffee_shop_stage_setup.tsv",
                          "coffee_shop_stage_setup_writes.tsv")
    coffee_stage_hashes_a = {
        name: digest(COFFEE_STAGE_A / name) for name in coffee_stage_files}
    coffee_stage_hashes_b = {
        name: digest(COFFEE_STAGE_B / name) for name in coffee_stage_files}
    require(coffee_stage_hashes_a == coffee_stage_hashes_b,
            "Coffee Shop stage-setup captures differ")
    coffee_stage_writes = rows(
        COFFEE_STAGE_A / "coffee_shop_stage_setup_writes.tsv")
    require([(row["frame"], row["pc"], row["stage_parameter_before"],
              row["data"], row["rng"]) for row in coffee_stage_writes] == [
        ("2072", "017ab4", "0000", "0000000e", "8def"),
        ("2072", "017ade", "000e", "00000006", "8def"),
        ("2072", "017af2", "0006", "00000006", "8def"),
        ("2072", "017b08", "0006", "00000006", "a998"),
        ("2072", "017b1c", "0006", "00000006", "a998"),
        ("2072", "017b74", "0006", "00000008", "a998"),
    ], "Coffee Shop stage-parameter transaction drift")
    coffee_stage_rng = rows(COFFEE_STAGE_A / "coffee_shop_rng_calls.tsv")
    coffee_stage_rng_suppress = rows(
        COFFEE_STAGE_SUPPRESS / "coffee_shop_rng_calls.tsv")
    baseline_initial = [row["rng_before"] for row in coffee_stage_rng[:11]]
    suppressed_initial = [row["rng_before"]
                          for row in coffee_stage_rng_suppress[:11]]
    require(baseline_initial == ["8def", "a998", "fc94", "f589", "e069",
                                 "a10a", "e3ed", "ab98", "029a", "07a1",
                                 "16b7"] and
            suppressed_initial == ["8def", "8def", "a998", "fc94", "f589",
                                   "e069", "a10a", "e3ed", "ab98", "029a",
                                   "07a1"],
            "Coffee Shop stage RNG suppression control drift")

    global_counts = Counter(row["pc"] for row in global_rows)
    require(global_counts == {"017af6": 3, "028a60": 32,
                              "00a5de": 2, "00a5f0": 2},
            "global RNG caller partition drift")
    global_groups = [
        {"owner": "route-stage-table setup", "calls": 3,
         "frames": [2072, 5565, 15192], "call_pc": "0x017af0",
         "return_pc": "0x017af6", "caller_chain": ["0x01bf5c", "0x01be4e", "0x00848c"],
         "guard": ("source stage-table record type 0x1c passes its route and "
                   "player-variant guards, then 0x017a1e selects the stage row"),
         "reads": ["0xff8218:u16", "stage table 0x00117560", "0xff81a8:u16"],
         "writes": ["0xff81ea:s16 stage parameter", "0xff81a8:u16 RNG state"],
         "effect": "D0&0x3e indexes 0x017b98 and adjusts the source stage parameter",
         "coffee_shop_entry_transaction": {
             "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
             "capture_identity": {
                 "byte_identical": True,
                 "files": coffee_stage_hashes_a,
                 "suppression_rng_sha256": digest(
                     COFFEE_STAGE_SUPPRESS / "coffee_shop_rng_calls.tsv"),
                 "suppression_result_sha256": digest(
                     COFFEE_STAGE_SUPPRESS / "progression_result.tsv"),
             },
             "source_frame": 2072,
             "scheduler_position": "before the ten record-12/class-0x1f initializer calls at source frame 2073",
             "guard": {
                 "route_state_s16": 2,
                 "player_variant_u16": 1,
                 "stage_record_type_u8": "0x1c",
                 "stage_record_pointer": "0x0011759a",
             },
             "reads": {
                 "player_variant": "0xff8218:u16",
                 "population_selector": "D1:u16=25",
                 "variant_selector": "0xff81cf:u8=0",
                 "post_selector": "0xff820e:u8=3",
                 "lower_bound": "0xff821c:s16=8",
                 "upper_bound": "0xff821a:s16=16",
                 "rng_seed": "0xff81a8:u16=0x8def",
             },
             "arithmetic": [
                 "write stage parameter 14 from the selected type-0x1c stage row",
                 "population selector 25 is >=22, so signed add -8 produces 6",
                 "signed variant table adjustment at 0x017b88 index 0 adds 0",
                 "one source RNG call maps 0x8def to 0xa998 and returns 0x98",
                 "(return&0x3e)=0x18 selects signed word 0 from 0x017b98",
                 "signed post-selector table adjustment at 0x017c58 index 3 adds 0",
                 "clamp signed result 6 to the inclusive 8..16 stage bounds, producing 8",
             ],
             "writes": {
                 "stage_parameter_s16": 8,
                 "rng_seed_u16": "0xa998",
                 "writer_sequence": ["0x017ab4", "0x017ade", "0x017af2",
                                     "0x017b08", "0x017b1c", "0x017b74"],
             },
             "suppression_control": {
                 "suppressed_writer_pcs": ["0x017c70", "0x017c72"],
                 "baseline_first_class1f_seed": "0xa998",
                 "suppressed_first_class1f_seed": "0x8def",
                 "baseline_seed_before_tenth_class1f": "0x16b7",
                 "suppressed_seed_before_tenth_class1f": "0x07a1",
                 "downstream_route_projection_differs": True,
                 "fixed_frame_substitution_rejected": True,
             },
         }},
        {"owner": "encounter controller class-0x1f spawn initialization", "calls": 32,
         "first_frame": 2510, "last_frame": 5062, "call_pc": "0x028a5a",
         "return_pc": "0x028a60", "caller_chain": ["0x0288fa", "0x028860", "0x01bde6"],
         "guard": ("u8(0xff8019)&7 == 0 and actor allocation 0x01769e succeeds "
                   "inside the class-0x02 route controller"),
         "reads": ["0xff8019:u8", "controller+0x10:u16", "0xff81a8:u16"],
         "writes": ["allocated class-0x1f actor fields", "0xff81a8:u16 RNG state"],
         "effect": "source tables 0x028aca/0x028afa choose child variant and z offset"},
        {"owner": "stage-clear transition presentation parameter setup", "calls": 4,
         "frames": [15058, 15058, 15060, 15060],
         "call_pcs": ["0x00a5d8", "0x00a5ea"],
         "return_pcs": ["0x00a5de", "0x00a5f0"],
         "caller_chain": ["0x0094a6", "0x0080a2"],
         "guard": "route transition substate +0x14 dispatches source handler 0x00a5d4",
         "reads": ["route+0x14:u16", "0xff81a8:u16"],
         "writes": ["route+0x16:u16 timer", "0xff9086:u16 table selector",
                    "0xff9088:u16 table offset", "0xff81a8:u16 RNG state"],
         "effect": "first draw selects 32..95 ticks; second selects table bank 0/16/32/48"},
    ]
    image = OPCODES.read_bytes()
    for group in global_groups:
        pc = int(group.get("return_pc", group.get("return_pcs", ["0"])[0]), 16)
        group["source_window"] = source_window(image, max(0, pc - 48), pc + 48)
        group["classification"] = "SOURCE_CLOSED"

    route = json.loads(ROUTE.read_text(encoding="ascii"))
    controls = route["targeted_counterfactuals"]
    require(controls["freeze_rng"]["completed_round1"] is False and
            controls["freeze_rng"]["last_state"]["rng"] == "8def",
            "freeze-RNG control drift")
    require(controls["route_perturbed"]["completed_round1"] is True and
            controls["route_perturbed"]["last_state"]["rng"] == "786c" and
            controls["suppress_boss_offense"]["completed_round1"] is True,
            "RNG perturbation controls drift")
    order_material = "\n".join(":".join(row[key] for key in
        ("frame", "pc", "a6", "seed", "return0", "return1", "return2")) for row in rng)
    report = {
        "schema": "oracle11-round1-global-rng-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "Round 1 shared RNG algorithm, seed state, exact call order and every route-reachable owner",
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True,
                             "enemy_rng_sha256": digest(ENEMY_A),
                             "auxiliary_rng_sha256": digest(AUX_A),
                             "opcode_sha256": digest(OPCODES)},
        "algorithm": {
            "entry": "0x017c5e", "state": "0xff81a8..0xff81a9:u16",
            "input": "old_seed:u16", "types": "all arithmetic wraps at u16/u8",
            "recurrence": ("high=((3*old_seed)&0xffff)>>8; "
                           "low=((old_seed&0xff)+high)&0xff; new_seed=(high<<8)|low"),
            "return": "new low byte in D0", "state_writer_tap_pcs": ["0x017c70", "0x017c72"],
            "source_window": source_window(image, 0x017c5e, 0x017c78),
            "classification": "SOURCE_CLOSED",
        },
        "consumption": {
            "calls": len(rng), "distinct_seed_change_frames": len(frames),
            "first_frame": int(rng[0]["frame"]), "last_frame": int(rng[-1]["frame"]),
            "initial_seed": f"0x{int(rng[0]['seed'], 16):04x}",
            "seed_after_last_call": f"0x{next_seed(int(rng[-1]['seed'], 16)):04x}",
            "max_calls_in_one_frame": max(frames.values()),
            "order_sha256": hashlib.sha256(order_material.encode("ascii")).hexdigest(),
            "missing_calls": 0, "recurrence_gaps": 0,
        },
        "owner_partition": {
            "enemy_type12": {"calls": 893,
                "contract": "data/oracle11_round1_enemy_archetypes.json",
                "classification": "SOURCE_CLOSED_CONSUMED_NOT_REOPENED"},
            "auxiliary_type16_20_24": {"calls": 1348,
                "source_dispatched_actor_calls": 1288,
                "transient_child_calls": 60,
                "transient_child_groups": [
                    {"class": "0x47", "type": 24, "calls": 28,
                     "caller_pcs": ["0x08ebd6", "0x08ebe8", "0x08ebfa",
                                    "0x08ec0c", "0x08ec1e", "0x08ed38"],
                     "owner": "Coffee Shop class-0x02 damageable-prop child presentation actor",
                     "source_contract": "data/oracle11_round1_auxiliary_authority.json#/first_segment_dependencies/class_0x47_type24_class02_child_presentation",
                     "semantic_name": "UNKNOWN", "classification": "SOURCE_CLOSED"},
                    {"class": "0x25", "type": 24, "calls": 20,
                     "caller_pcs": ["0x081ab2", "0x081ae2"],
                     "owner": "type-24 child actor initialization at boss-room controller edges",
                     "semantic_name": "UNKNOWN", "classification": "SOURCE_CLOSED"},
                    {"class": "0x4d", "type": 24, "calls": 11,
                     "caller_pcs": ["0x092770", "0x0927a2"],
                     "owner": "type-24 route presentation child state dispatch",
                     "semantic_name": "UNKNOWN", "classification": "SOURCE_CLOSED"},
                    {"class": "0x05", "type": 20, "calls": 1,
                     "caller_pcs": ["0x0bc6ba"],
                     "owner": "type-20 source child initialization",
                     "semantic_name": "UNKNOWN", "classification": "SOURCE_CLOSED"},
                ],
                "contract": "data/oracle11_round1_auxiliary_authority.json",
                "classification": "SOURCE_CLOSED"},
            "global_route_and_controller": {"calls": 39, "groups": global_groups,
                "classification": "SOURCE_CLOSED"},
            "total": 2280, "orphan_calls": 0,
        },
        "counterfactuals": {
            "freeze_rng": {"completed_round1": False, "frozen_seed": "0x8def",
                           "classification": "DISCRIMINATING"},
            "route_perturbed": {"completed_round1": True, "final_seed": "0x786c",
                                "classification": "DISCRIMINATING"},
            "suppress_boss_offense": {"completed_round1": True,
                                      "final_seed": "0xf48c",
                                      "classification": "DISCRIMINATING"},
            "semantic_names_inferred": False,
        },
        "coverage": {"required_calls": 2280, "closed_calls": 2280,
                     "required_seed_change_frames": 1023,
                     "closed_seed_change_frames": 1023,
                     "orphan_calls": 0, "orphan_owner_groups": 0,
                     "recurrence_gaps": 0, "unowned_seed_writers": 0},
        "owned_authoritative_writer_pcs": ["0x017c70", "0x017c72"],
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED", "user09": "CHANGES_REQUESTED",
            "spec02_active": False, "production_runtime_writes": 0,
            "yaba_runs": 0, "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED", "RNG status drift")
    require(report["capture_identity"]["byte_identical"] is True,
            "RNG repeatability drift")
    require(report["algorithm"]["entry"] == "0x017c5e" and
            report["algorithm"]["classification"] == "SOURCE_CLOSED",
            "RNG algorithm drift")
    require(report["consumption"]["calls"] == 2280 and
            report["consumption"]["distinct_seed_change_frames"] == 1023 and
            report["consumption"]["recurrence_gaps"] == 0,
            "RNG consumption drift")
    owners = report["owner_partition"]
    require(owners["enemy_type12"]["calls"] +
            owners["auxiliary_type16_20_24"]["calls"] +
            owners["global_route_and_controller"]["calls"] == owners["total"] == 2280,
            "RNG owner total drift")
    require(owners["orphan_calls"] == 0 and
            len(owners["global_route_and_controller"]["groups"]) == 3,
            "RNG orphan/global group drift")
    coffee = owners["global_route_and_controller"]["groups"][0][
        "coffee_shop_entry_transaction"]
    require(coffee["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            coffee["capture_identity"]["byte_identical"] is True and
            coffee["writes"]["stage_parameter_s16"] == 8 and
            coffee["writes"]["rng_seed_u16"] == "0xa998" and
            coffee["suppression_control"][
                "downstream_route_projection_differs"] is True,
            "Coffee Shop stage RNG implementation boundary incomplete")
    require(report["counterfactuals"]["freeze_rng"]["completed_round1"] is False,
            "frozen RNG fabricated completion")
    require(all(value == 0 for key, value in report["coverage"].items()
                if key.startswith("orphan_") or key.endswith("_gaps") or
                key.startswith("unowned_")), "RNG closure gap accepted")
    require(report["protected_boundaries"]["spec02_active"] is False and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN",
            "protected RNG boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes((json.dumps(report, sort_keys=True, indent=2) + "\n").encode("ascii"))
    print("ORACLE-11 Round 1 RNG: SOURCE_CLOSED; 2,280 calls across 1,023 frames, "
          "zero recurrence gaps and zero orphan owners")


if __name__ == "__main__":
    main()
