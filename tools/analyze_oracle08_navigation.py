#!/usr/bin/env python3
"""Derive the bounded Coffee Shop navigation contract for ORACLE-08."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle08_navigation_source_closure_v2"
ENEMY_RAW = ROOT / ".deps" / "mame" / "oracle08_enemy_bounds_source_closure"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
ORACLE06 = ROOT / "data" / "oracle06_round1_encounter.json"
OUT = ROOT / "data" / "oracle08_round1_navigation_bounds.json"

VARIANTS = (
    "cold_run_1", "cold_run_2", "up_hold", "down_hold", "left_hold",
    "right_hold", "up_right", "down_right", "right_hold_no_obstacle",
    "up_hold_no_obstacle",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii") + b"\n"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    require(bool(rows), f"empty trace: {path}")
    return rows


def samples(variant: str) -> list[dict[str, int | str]]:
    rows = read_tsv(RAW / variant / "samples.tsv")
    required = {"frame", "variant", "input_word", "p_x", "p_y", "p_z",
                "bound_x", "bound_z", "scroll2_x", "ob_active", "ob_class",
                "ob_type", "ob_state", "ob_x", "ob_z", "ob_hex"}
    require(required <= set(rows[0]), f"sample schema drift: {variant}")
    converted: list[dict[str, int | str]] = []
    for row in rows:
        converted.append({key: value if key in ("variant", "ob_hex") else int(value)
                          for key, value in row.items()})
    require(len(converted) == 1301 and converted[0]["frame"] == 3400 and
            converted[-1]["frame"] == 4700,
            f"sample window drift: {variant}")
    return converted


def writes(variant: str) -> list[dict[str, str]]:
    rows = read_tsv(RAW / variant / "navigation_writes.tsv")
    required = {"frame", "offset", "pc", "a4", "a5", "a6", "a4_hex"}
    require(required <= set(rows[0]), f"write schema drift: {variant}")
    return rows


def enemy_samples(variant: str) -> dict[int, dict[str, int | str]]:
    rows = read_tsv(ENEMY_RAW / variant / "samples.tsv")
    required = {"frame", "variant", "e_active", "e_class", "e_state",
                "e_inner", "e_action", "e_x", "e_z", "bound_x", "bound_z"}
    require(required <= set(rows[0]), f"enemy sample schema drift: {variant}")
    converted = [{key: value if key == "variant" else int(value)
                  for key, value in row.items()} for row in rows]
    require(len(converted) == 151 and converted[0]["frame"] == 4150 and
            converted[-1]["frame"] == 4300,
            f"enemy sample window drift: {variant}")
    return {int(row["frame"]): row for row in converted}


def enemy_writes(variant: str) -> list[dict[str, str]]:
    return read_tsv(ENEMY_RAW / variant / "enemy_writes.tsv")


def post(rows: list[dict[str, int | str]]) -> list[dict[str, int | str]]:
    return [row for row in rows if int(row["frame"]) >= 4210]


def endpoint(rows: list[dict[str, int | str]]) -> dict[str, object]:
    bounded = post(rows)
    first, last = bounded[0], bounded[-1]
    return {
        "input_start_frame": 4210,
        "start": {"x": first["p_x"], "z": first["p_z"]},
        "end": {"x": last["p_x"], "z": last["p_z"]},
        "observed_range": {
            "x": [min(int(row["p_x"]) for row in bounded),
                  max(int(row["p_x"]) for row in bounded)],
            "z": [min(int(row["p_z"]) for row in bounded),
                  max(int(row["p_z"]) for row in bounded)],
        },
        "bound_x_range": [min(int(row["bound_x"]) for row in bounded),
                          max(int(row["bound_x"]) for row in bounded)],
        "bound_z_range": [min(int(row["bound_z"]) for row in bounded),
                          max(int(row["bound_z"]) for row in bounded)],
        "scroll2_x_end": last["scroll2_x"],
    }


def has_writer(rows: list[dict[str, str]], *, pc: str, offset: str,
               a4: str | None = None, a6: str | None = None) -> bool:
    return any(int(row["frame"]) >= 4210 and row["pc"].lower() == pc and
               row["offset"].lower() == offset and
               (a4 is None or row["a4"].lower() == a4) and
               (a6 is None or row["a6"].lower() == a6) for row in rows)


def obstacle_contract(cold: list[dict[str, int | str]], program: bytes) -> dict:
    row = next(item for item in cold if item["frame"] == 4210)
    blob = bytes.fromhex(str(row["ob_hex"]))
    require(len(blob) == 0xC0, "obstacle actor snapshot length drift")
    anim = int.from_bytes(blob[0x1C:0x20], "big")
    table_set = int.from_bytes(blob[0x50:0x54], "big")
    require((row["ob_active"], row["ob_class"], row["ob_type"],
             row["ob_state"], row["ob_x"], row["ob_z"]) ==
            (1, 0x0A, 0x14, 2, 1123, 323), "obstacle identity drift")
    require(anim == 0x06E136 and table_set == 0x06E210,
            "obstacle animation/table binding drift")
    require(program[anim + 8] == 1, "obstacle hurt selector drift")
    hurt_rel = int.from_bytes(program[table_set:table_set + 2], "big", signed=True)
    attack_rel = int.from_bytes(program[table_set + 2:table_set + 4],
                                "big", signed=True)
    hurt = table_set + hurt_rel + 8
    require((hurt_rel, attack_rel) == (4, 0x14), "obstacle table relatives drift")
    box = {
        "x_center": int.from_bytes(program[hurt:hurt + 1], "big", signed=True),
        "y_center": int.from_bytes(program[hurt + 1:hurt + 2], "big", signed=True),
        "x_half": program[hurt + 2], "y_half": program[hurt + 3],
        "z_center": int.from_bytes(program[hurt + 4:hurt + 5], "big", signed=True),
        "z_half": program[hurt + 5],
    }
    require(box == {"x_center": 0, "y_center": 64, "x_half": 16,
                    "y_half": 64, "z_center": 0, "z_half": 6},
            "obstacle hurt geometry drift")
    return {
        "classification": "MEASURED",
        "actor_slot": "0xffb380", "class": "0x0a", "type": "0x14",
        "state": 2, "world_position": {"x": 1123, "z": 323},
        "animation_record": "0x06e136", "table_set": "0x06e210",
        "hurt_selector": 1, "hurt_box": box,
        "extent_note": "table geometry is source data; accepted player position also depends on the player box and minimum-penetration response",
    }


def validate(report: dict) -> None:
    require(report.get("schema") == 1, "schema drift")
    require(report.get("task") == "ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS",
            "task drift")
    require(report.get("classification") ==
            "MEASURED_MAME_SOURCE_NAVIGATION_AND_BOUNDS_CONTRACT",
            "classification drift")
    require(report["determinism"]["cold_runs_byte_identical"] is True,
            "determinism not proven")
    require(report["coordinate_contract"]["up_input_world_z_delta_sign"] == 1 and
            report["coordinate_contract"]["down_input_world_z_delta_sign"] == -1,
            "lane input/world-z sign drift")
    require(report["segment_bounds"]["coffee_shop_lock"]["x_formula"] ==
            {"minimum": "bound_x + 0x20", "maximum": "bound_x + 0x160"},
            "world-x formula drift")
    attempts = report["boundary_counterfactuals"]
    require(attempts["left"]["result"]["end"]["x"] == 864,
            "left clamp drift")
    require(attempts["down"]["result"]["end"]["z"] == 224,
            "lower lane clamp drift")
    require(attempts["up"]["result"]["end"]["z"] == 327,
            "terrain boundary drift")
    require(attempts["right_obstacle"]["result"]["end"]["x"] == 1091,
            "obstacle rejection drift")
    require(attempts["right_obstacle_removed"]["result"]["end"]["x"] == 1184,
            "obstacle counterfactual drift")
    require(report["walkable_shape"]["rectangular_screen_clamp"] is False,
            "screen clamp incorrectly authorized")
    require(report["enemy_boundary_counterfactuals"]["beyond_left"]["accepted_next_tick"]["x"] == 840 and
            report["enemy_boundary_counterfactuals"]["beyond_right"]["accepted_next_tick"]["x"] == 1200,
            "enemy x boundary behavior drift")
    require(report["enemy_boundary_counterfactuals"]["beyond_lower"]["accepted_next_tick"]["z"] == 300 and
            report["enemy_boundary_counterfactuals"]["beyond_upper"]["accepted_next_tick"]["z"] == 300,
            "enemy z rejection behavior drift")
    require(report["camera_and_route"]["coffee_shop_lock"] ==
            {"scroll2_x": 768, "first_frame": 3821, "last_frame": 4994,
             "player_right_clamp_x": 1184, "right_edge_offset": 416},
            "camera lock drift")
    require(report["camera_and_route"]["first_unlock_frame"] == 4995 and
            report["camera_and_route"]["next_lock"]["scroll2_x"] == 944,
            "route transition drift")
    require(all(report["negative_controls"].values()),
            "negative control disabled")
    require(report["saturn_emulator"] == "UNRUN" and
            report["physical_saturn"] == "UNRUN",
            "unearned Saturn evidence")


def mutation_self_test(report: dict) -> None:
    mutants: list[tuple[str, dict]] = []
    widened = copy.deepcopy(report)
    widened["boundary_counterfactuals"]["left"]["result"]["end"]["x"] = 840
    mutants.append(("widened left bound", widened))
    bypass = copy.deepcopy(report)
    bypass["boundary_counterfactuals"]["right_obstacle"]["result"]["end"]["x"] = 1184
    mutants.append(("bypassed obstacle", bypass))
    screen = copy.deepcopy(report)
    screen["walkable_shape"]["rectangular_screen_clamp"] = True
    mutants.append(("screen clamp", screen))
    enemy = copy.deepcopy(report)
    enemy["enemy_boundary_counterfactuals"]["beyond_right"]["accepted_next_tick"]["x"] = 1184
    mutants.append(("shared player/enemy clamp", enemy))
    physical = copy.deepcopy(report)
    physical["physical_saturn"] = "PASS"
    mutants.append(("physical claim", physical))
    for name, mutant in mutants:
        try:
            validate(mutant)
        except ValueError:
            continue
        raise AssertionError(f"accepted ORACLE-08 mutation: {name}")


def build_report() -> dict:
    manifest = json.loads((RAW / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    require(tuple(item["name"] for item in manifest["variants"]) == VARIANTS,
            "variant manifest drift")
    require(digest(RAW / "cold_run_1" / "samples.tsv") ==
            digest(RAW / "cold_run_2" / "samples.tsv") and
            digest(RAW / "cold_run_1" / "navigation_writes.tsv") ==
            digest(RAW / "cold_run_2" / "navigation_writes.tsv"),
            "cold runs are not byte-identical")
    run = {name: samples(name) for name in VARIANTS}
    write = {name: writes(name) for name in VARIANTS}
    ends = {name: endpoint(rows) for name, rows in run.items()}
    enemy_manifest = json.loads((ENEMY_RAW / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    enemy_variants = ("cold_run_1", "cold_run_2", "beyond_left",
                      "beyond_right", "beyond_lower", "beyond_upper")
    require(tuple(item["name"] for item in enemy_manifest["variants"]) ==
            enemy_variants, "enemy variant manifest drift")
    require(digest(ENEMY_RAW / "cold_run_1" / "samples.tsv") ==
            digest(ENEMY_RAW / "cold_run_2" / "samples.tsv") and
            digest(ENEMY_RAW / "cold_run_1" / "enemy_writes.tsv") ==
            digest(ENEMY_RAW / "cold_run_2" / "enemy_writes.tsv"),
            "enemy cold runs are not byte-identical")
    enemy_run = {name: enemy_samples(name) for name in enemy_variants}
    enemy_write = {name: enemy_writes(name) for name in enemy_variants}
    require((enemy_run["beyond_left"][4210]["e_x"],
             enemy_run["beyond_left"][4211]["e_x"],
             enemy_run["beyond_right"][4210]["e_x"],
             enemy_run["beyond_right"][4211]["e_x"]) ==
            (840, 840, 1200, 1200), "enemy x perturbation result drift")
    require((enemy_run["beyond_lower"][4210]["e_z"],
             enemy_run["beyond_lower"][4211]["e_z"],
             enemy_run["beyond_upper"][4210]["e_z"],
             enemy_run["beyond_upper"][4211]["e_z"]) ==
            (200, 300, 420, 300), "enemy z perturbation result drift")
    require(any(row["pc"] == "060c84" and row["offset"] == "18" and
                int(row["frame"]) == 4210 for row in enemy_write["beyond_lower"]) and
            any(row["pc"] == "060c84" and row["offset"] == "18" and
                int(row["frame"]) == 4210 for row in enemy_write["beyond_upper"]),
            "enemy lane authority writer drift")

    require(ends["cold_run_1"]["start"] == {"x": 1067, "z": 320},
            "common start drift")
    require(has_writer(write["left_hold"], pc="01b018", offset="10") and
            has_writer(write["left_hold"], pc="01b020", offset="10") and
            has_writer(write["down_hold"], pc="01b042", offset="18") and
            has_writer(write["down_hold"], pc="01b04a", offset="18") and
            has_writer(write["right_hold_no_obstacle"], pc="01b030", offset="10"),
            "global clamp writer binding drift")
    require(has_writer(write["right_hold"], pc="01d986", offset="10",
                       a6="ffb380"), "obstacle response writer drift")
    require(has_writer(write["up_hold"], pc="0b1c68", offset="18",
                       a4="0b2136", a6="ff8380"),
            "terrain response writer drift")
    top_rows = [row for row in write["up_hold"] if int(row["frame"]) >= 4210
                and row["pc"] == "0b1c68"]
    require(top_rows and {row["a4_hex"] for row in top_rows} ==
            {"0202808010080080"}, "terrain record bytes drift")

    program, opcodes = PROGRAM.read_bytes(), OPCODES.read_bytes()
    require(opcodes[0x01B004:0x01B06A].hex().startswith("302e001004400020"),
            "global bound routine opcode drift")
    require(opcodes[0x01D97C:0x01D998].hex().startswith("01e9005d93690010"),
            "obstacle response opcode drift")
    obstacle = obstacle_contract(run["cold_run_1"], program)

    oracle06 = json.loads(ORACLE06.read_text(encoding="utf-8"))
    locks = oracle06["source_set_piece"]["camera"]["scroll2_x_locks"]
    require(locks[1] == {"value": 768, "first_frame": 3821,
                         "last_frame": 4994, "player_right_clamp_x": 1184},
            "ORACLE-06 Coffee Shop lock drift")
    require(locks[2]["value"] == 944 and locks[2]["first_frame"] == 5071 and
            locks[2]["player_right_clamp_x"] == 1360,
            "ORACLE-06 next lock drift")

    report = {
        "schema": 1,
        "task": "ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS",
        "classification": "MEASURED_MAME_SOURCE_NAVIGATION_AND_BOUNDS_CONTRACT",
        "scope": "Predator Warrior navigation in the bounded Coffee Shop segment and its next camera lock; not a generic Round 1 navigation engine",
        "target": {"set": "avspu", "revision": "USA 940520",
                   "player_slot": "0xff8380"},
        "coordinate_contract": {
            "classification": "MEASURED",
            "world_fields": {"x": "actor+0x10 signed word",
                             "y": "actor+0x14 signed word",
                             "z": "actor+0x18 signed word"},
            "up_input_world_z_delta_sign": 1,
            "down_input_world_z_delta_sign": -1,
            "screen_position_rule": "UNKNOWN here; world-z must be translated by SPEC-01 and must not be copied as screen-y",
        },
        "segment_bounds": {
            "classification": "TRANSLATED_FROM_BOUND_ROUTINE_AND_MEASURED",
            "routine": "0x01b000",
            "base_fields": {"bound_x": "A5+0x278 signed word",
                            "bound_z": "A5+0x27c signed word"},
            "coffee_shop_lock": {
                "bound_x": 832,
                "x_formula": {"minimum": "bound_x + 0x20",
                              "maximum": "bound_x + 0x160"},
                "observed_x": [864, 1184],
                "bound_z_is_dynamic": True,
                "observed_bound_z": [208, 256],
                "z_formula": {"minimum": "bound_z + 0x10",
                              "maximum": "bound_z + 0x90"},
                "observed_lower_z": 224,
            },
            "writers": {"left_clamp": ["0x01b018", "0x01b020"],
                        "right_clamp": "0x01b030",
                        "lower_z_clamp": ["0x01b042", "0x01b04a"],
                        "world_y_sync": "0x01b05a"},
        },
        "walkable_shape": {
            "classification": "MEASURED",
            "rectangular_screen_clamp": False,
            "finding": "non-rectangular world-space lane: the upper/middle Coffee Shop path is blocked at x=1091, while the lower route reaches x=1184",
            "upper_middle_samples": {"z": [320, 327], "rightmost_x": 1091},
            "lower_sample": {"z": 224, "rightmost_x": 1184},
        },
        "obstacle": obstacle,
        "terrain_constraint": {
            "classification": "MEASURED_AND_STATICALLY_BOUND",
            "record": "0x0b2136", "record_bytes": "0202808010080080",
            "resolver_block": "0x0b1baa-0x0b1c70",
            "upper_response_writer": "0x0b1c68",
            "accepted_max_world_z": 327,
            "finding": "up input is rejected at the terrain-cell boundary; removing obstacle slot 0xffb380 does not change the result",
        },
        "boundary_counterfactuals": {
            "left": {"requested": "hold Left from frame 4210",
                     "result": ends["left_hold"], "authority": "0x01b000 global bound"},
            "right_obstacle": {"requested": "hold Right at world-z 320",
                               "result": ends["right_hold"],
                               "authority": "0x01d930 minimum-penetration actor/obstacle response"},
            "right_obstacle_removed": {"requested": "same Right schedule; deactivate only 0xffb380",
                                       "result": ends["right_hold_no_obstacle"],
                                       "authority": "declared source mutation exposes 0x01b000 segment edge"},
            "up": {"requested": "hold Up from world-z 320",
                   "result": ends["up_hold"], "authority": "0x0b1c68 terrain response"},
            "up_obstacle_removed": {"requested": "same Up schedule; deactivate only 0xffb380",
                                    "result": ends["up_hold_no_obstacle"],
                                    "authority": "terrain boundary remains independent of obstacle actor"},
            "down": {"requested": "hold Down from world-z 320",
                     "result": ends["down_hold"], "authority": "0x01b000 dynamic lower bound"},
            "up_right": {"requested": "hold Up+Right",
                         "result": ends["up_right"], "authority": "terrain plus obstacle"},
            "down_right": {"requested": "hold Down+Right",
                           "result": ends["down_right"], "authority": "lower route passes obstacle then global bounds"},
        },
        "camera_and_route": {
            "classification": "MEASURED_PRIOR_ACCEPTED_ORACLE06",
            "coffee_shop_lock": {"scroll2_x": 768, "first_frame": 3821,
                                 "last_frame": 4994, "player_right_clamp_x": 1184,
                                 "right_edge_offset": 416},
            "first_unlock_frame": 4995,
            "first_unlock_counterfactual": "attack suppression changes actors but not unlock frame; entry-hold shifts last locked frame to 5020, proving route/input participation",
            "route_authority": {"controller_state": "g8009 remains 4",
                                "camera_target_field": "g8032 written by 0x0b0706",
                                "exact_generalized_guard": "UNKNOWN; do not replace with a guessed x or kill trigger"},
            "next_lock": {"scroll2_x": 944, "first_frame": 5071,
                          "player_right_clamp_x": 1360},
        },
        "enemy_boundary_counterfactuals": {
            "classification": "MEASURED_BOUNDARY_AUTHORITY_ONLY",
            "target_slot": "0xffa000", "class": "0x1f",
            "finding": "the class-0x1f actor is not clamped to the player's Coffee Shop x interval; one-frame z perturbations are overwritten by its state/lane writer, so a shared player/enemy rectangle is forbidden",
            "beyond_left": {"requested_at_4210": {"x": 840, "z": 300},
                            "accepted_next_tick": {"x": 840, "z": 300},
                            "result": "accepted; later approach motion continues"},
            "beyond_right": {"requested_at_4210": {"x": 1200, "z": 300},
                             "accepted_next_tick": {"x": 1200, "z": 300},
                             "result": "accepted beyond player x=1184; later source state can leave/remove the actor"},
            "beyond_lower": {"requested_at_4210": {"x": 976, "z": 200},
                             "accepted_next_tick": {"x": 976, "z": 300},
                             "result": "rejected/rewritten by 0x060c84"},
            "beyond_upper": {"requested_at_4210": {"x": 976, "z": 420},
                             "accepted_next_tick": {"x": 976, "z": 300},
                             "result": "rejected/rewritten by 0x060c84"},
            "scope_guard": "ORACLE-09 owns target-relative lane steering and state semantics; ORACLE-08 proves only that enemy navigation must not consume the player clamp",
        },
        "determinism": {
            "cold_runs_byte_identical": True, "sample_frames_each": 1301,
            "enemy_cold_runs_byte_identical": True,
            "enemy_sample_frames_each": 151,
            "samples_sha256": digest(RAW / "cold_run_1" / "samples.tsv"),
            "writes_sha256": digest(RAW / "cold_run_1" / "navigation_writes.tsv"),
        },
        "declared_capture_mutations": manifest["declared_mutations"],
        "negative_controls": {
            "reject_widened_global_bounds": True,
            "reject_bypassed_obstacle": True,
            "reject_removed_terrain_constraint": True,
            "reject_rectangular_screen_clamp": True,
            "reject_guessed_route_trigger": True,
            "reject_shared_player_enemy_clamp": True,
        },
        "bounded_unknowns": [
            "a generalized camera-unlock guard beyond the measured Coffee Shop transition",
            "enemy target-relative navigation and lane steering semantics, deferred to ORACLE-09",
            "later Round 1 terrain and segment tables",
            "screen projection semantics, deferred to SPEC-01",
            "physical Saturn behavior",
        ],
        "provenance": {
            "capture_manifest_sha256": digest(RAW / "input_manifest.json"),
            "enemy_capture_manifest_sha256": digest(ENEMY_RAW / "input_manifest.json"),
            "capture_artifacts": {item["name"]: {
                "samples_sha256": item["samples_sha256"],
                "writes_sha256": item["writes_sha256"]} for item in manifest["variants"]},
            "mame": manifest["mame"], "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "rom_sha256": manifest["roms"],
            "enemy_capture_artifacts": {item["name"]: {
                "samples_sha256": item["samples_sha256"],
                "writes_sha256": item["writes_sha256"]} for item in enemy_manifest["variants"]},
            "decrypted_program_sha256": digest(PROGRAM),
            "decrypted_opcodes_sha256": digest(OPCODES),
            "oracle06_sha256": digest(ORACLE06),
        },
        "saturn_emulator": "UNRUN",
        "physical_saturn": "UNRUN",
    }
    validate(report)
    mutation_self_test(report)
    return report


if __name__ == "__main__":
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"wrote {OUT.relative_to(ROOT)} sha256={digest(OUT)}")
