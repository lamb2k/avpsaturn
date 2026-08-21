"""Validate Tranche 1's private MAME oracle and emit a public manifest.

The input ledger is never tracked.  This program only commits provenance,
schema, counts and SHA-256 summaries.  It intentionally treats the final MAME
screen bitmap as RGB output, never as recoverable CPS2 palette indices.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "avsp_vertical_slice_contract.json"
RAW_ROOT = ROOT / ".deps" / "mame" / "vertical_slice"
OUT_PATH = ROOT / "data" / "avsp_vertical_slice_oracle_manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii") + b"\n"


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def expected_header(contract: dict) -> list[str]:
    return contract["required_frame_fields"]


def validate_provenance(contract: dict, inputs: dict) -> None:
    if contract.get("schema") != 1:
        fail("wrong contract schema version")
    target = contract["target"]
    mame = inputs.get("mame", {})
    if mame.get("version") != target["mame_version"]:
        fail("wrong MAME version")
    if mame.get("sha256", "").lower() != target["mame_sha256"]:
        fail("wrong MAME hash")
    observed = {entry["name"]: entry["sha256"].lower()
                for entry in inputs.get("roms", [])}
    expected = contract["canonical_rom_sha256"]
    observed_canonical = {name: value for name, value in observed.items()
                          if name in expected}
    allowed_extras = contract.get("noncanonical_local_dependencies", {})
    observed_extras = {name: value for name, value in observed.items()
                       if name not in expected}
    if observed_canonical != expected or observed_extras != allowed_extras:
        fail("wrong set or ROM hash inventory")
    if not inputs.get("config_sha256") or not inputs.get("nvram_baseline_sha256"):
        fail("missing config or NVRAM identity")


def parse_samples(path: Path, contract: dict) -> list[dict[str, str]]:
    rows = path.read_text(encoding="utf-8").splitlines()
    if not rows:
        fail("missing semantic samples")
    header = rows[0].split("\t")
    if header != expected_header(contract):
        fail("wrong schema version or missing frame field")
    expected_count = contract["window"]["frame_count"]
    if len(rows) - 1 != expected_count:
        fail("wrong semantic frame count")
    result = []
    first = contract["window"]["first_source_frame"]
    for index, line in enumerate(rows[1:]):
        fields = line.split("\t")
        if len(fields) != len(header):
            fail("missing field in semantic row %d" % (index + 1))
        row = dict(zip(header, fields))
        if int(row["frame"]) != first + index:
            fail("non-contiguous source frames")
        result.append(row)
    return result


def u16_words(path: Path) -> list[int]:
    data = path.read_bytes()
    if len(data) % 2:
        fail("odd CPS register byte count")
    return [int.from_bytes(data[offset:offset + 2], "big")
            for offset in range(0, len(data), 2)]


def int_field(row: dict[str, str], name: str, base: int = 10) -> int:
    return int(row[name], base)


def actor(row: dict[str, str], prefix: str) -> dict[str, int]:
    fields = ("state", "class", "sub", "action", "type", "facing", "x", "y", "z",
              "timer", "health", "hit", "source", "hurt", "attack")
    result = {field: int_field(row, "%s_%s" % (prefix, field)) for field in fields}
    result["anim"] = int_field(row, "%s_anim" % prefix, 16)
    return result


def qsound_by_frame(path: Path) -> tuple[dict[int, list[dict[str, int]]], int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "frame\tpc\tport\tbyte\tregister\tvalue":
        fail("missing QSound schema")
    result: dict[int, list[dict[str, int]]] = defaultdict(list)
    for line in lines[1:]:
        frame, pc, port, byte, register, value = line.split("\t")
        result[int(frame)].append({
            "pc": int(pc, 16), "port": int(port, 16), "byte": int(byte, 16),
            "register": int(register, 16) if register else -1,
            "value": int(value, 16) if value else -1,
        })
    return result, len(lines) - 1


def raw_frame_digest(run: Path, bucket: str, frame: int, suffix: str) -> str:
    path = run / bucket / ("%05d.%s" % (frame, suffix))
    if not path.is_file():
        fail("missing raw %s frame %d" % (bucket, frame))
    return digest(path)


def build_ledger(contract: dict, run: Path) -> tuple[bytes, dict]:
    rows = parse_samples(run / "samples.tsv", contract)
    qsound, qsound_events = qsound_by_frame(run / "qsound.tsv")
    entries = []
    field_values: dict[str, set[int]] = defaultdict(set)
    health_changes = 0
    prior_health = None
    for row in rows:
        frame = int_field(row, "frame")
        cps_a = u16_words(run / "cps_a" / ("%05d.bin" % frame))
        cps_b = u16_words(run / "cps_b" / ("%05d.bin" % frame))
        if len(cps_a) <= 17:
            fail("CPS-A register capture lacks scroll/row-scroll fields")
        player = actor(row, "p")
        enemy = actor(row, "e")
        for name, value in row.items():
            if name not in ("frame", "p_anim", "e_anim"):
                try:
                    field_values[name].add(int(value))
                except ValueError:
                    pass
        if prior_health is not None and enemy["health"] != prior_health:
            health_changes += 1
        prior_health = enemy["health"]
        entries.append({
            "frame": frame,
            "input": int_field(row, "input_word"),
            "object_bank": int_field(row, "active_bank"),
            "player": player,
            "enemy": enemy,
            "objects": {
                "ordered_list_sha256": raw_frame_digest(run, "objram", frame, "bin"),
                "palette_sha256": raw_frame_digest(run, "palette", frame, "bin"),
            },
            "stage": {
                "cps_a_sha256": raw_frame_digest(run, "cps_a", frame, "bin"),
                "cps_b_sha256": raw_frame_digest(run, "cps_b", frame, "bin"),
                "scroll": {"scroll1": cps_a[6], "scroll2": cps_a[8], "scroll3": cps_a[10]},
                "layer_control_word": cps_a[17],
                "row_scroll_offset_word": cps_a[16],
                "row_scroll_enabled": bool(cps_a[17] & 1),
            },
            "audio": qsound.get(frame, []),
            "final_scanout_sha256": raw_frame_digest(run, "frames", frame, "png"),
        })
    active_enemy = [entry["enemy"] for entry in entries if entry["enemy"]["state"] != 0]
    nonvacuous = {
        "input_changes": len(field_values["input_word"]) > 1,
        "player_action_changes": len(field_values["p_action"]) > 1,
        "enemy_identity": bool(active_enemy) and all(
            value["class"] == 31 and value["type"] == 12 for value in active_enemy),
        "enemy_health_changes": health_changes > 0,
        "hit_selector_present": any(entry["enemy"]["hurt"] or entry["enemy"]["attack"] for entry in entries),
        "ko_present": any(entry["enemy"]["state"] == 2 for entry in entries),
        "camera_registers_observed": all("scroll2" in entry["stage"]["scroll"] for entry in entries),
        "palette_changes": len({entry["objects"]["palette_sha256"] for entry in entries}) > 1,
        "object_changes": len({entry["objects"]["ordered_list_sha256"] for entry in entries}) > 1,
        "row_scroll_observed": any(entry["stage"]["row_scroll_enabled"] for entry in entries),
        "qsound_events": qsound_events > 0,
        "scanout_changes": len({entry["final_scanout_sha256"] for entry in entries}) > 1,
    }
    missing = [name for name, present in nonvacuous.items() if not present]
    if missing:
        fail("required semantic field is vacuous: %s" % ", ".join(missing))
    ledger = b"".join(canonical(entry) for entry in entries)
    summary = {
        "frame_count": len(entries),
        "semantic_ledger_sha256": hashlib.sha256(ledger).hexdigest(),
        "first_final_scanout_sha256": entries[0]["final_scanout_sha256"],
        "last_final_scanout_sha256": entries[-1]["final_scanout_sha256"],
        "qsound_bus_events": qsound_events,
        "enemy_health_changes": health_changes,
        "nonvacuous": nonvacuous,
        "unique": {
            "object_lists": len({entry["objects"]["ordered_list_sha256"] for entry in entries}),
            "palettes": len({entry["objects"]["palette_sha256"] for entry in entries}),
            "scanouts": len({entry["final_scanout_sha256"] for entry in entries}),
        },
    }
    return ledger, summary


def generate() -> dict:
    contract = load_json(CONTRACT_PATH)
    inputs = load_json(RAW_ROOT / "input_manifest.json")
    validate_provenance(contract, inputs)
    ledgers = {}
    summaries = {}
    for name in ("cold_run_1", "cold_run_2", "one_frame_perturbation"):
        ledger, summary = build_ledger(contract, RAW_ROOT / name)
        (RAW_ROOT / name / "semantic_ledger.jsonl").write_bytes(ledger)
        ledgers[name] = ledger
        summaries[name] = summary
    if ledgers["cold_run_1"] != ledgers["cold_run_2"]:
        fail("two cold-run semantic ledgers differ")
    if ledgers["cold_run_1"] == ledgers["one_frame_perturbation"]:
        fail("one-frame perturbation did not alter semantic identity")
    first_difference = next(
        index for index, (left, right) in enumerate(zip(ledgers["cold_run_1"].splitlines(),
                                                         ledgers["one_frame_perturbation"].splitlines()))
        if left != right)
    manifest = {
        "schema": 1,
        "artifact": "avsp_vertical_slice_oracle_manifest",
        "evidence_tier": "MAME_TRACE",
        "contract_sha256": digest(CONTRACT_PATH),
        "target": contract["target"],
        "window": contract["window"],
        "route": {"name": contract["route"]["name"], "anchors": contract["route"]["anchors"]},
        "input_provenance": {
            "mame": inputs["mame"],
            "config_sha256": inputs["config_sha256"],
            "nvram_baseline_sha256": inputs["nvram_baseline_sha256"],
            "rom_count": len(contract["canonical_rom_sha256"]),
            "rom_sha256": {entry["name"]: entry["sha256"] for entry in inputs["roms"]
                           if entry["name"] in contract["canonical_rom_sha256"]},
            "noncanonical_local_dependencies": contract.get("noncanonical_local_dependencies", {}),
        },
        "schema_fields": contract["required_frame_fields"],
        "cold_runs": {"byte_identical": True, "summary": summaries["cold_run_1"]},
        "negative_control": {
            "kind": "one_frame_input_perturbation",
            "frame": contract["route"]["one_frame_perturbation"]["frame"],
            "identity_changed": True,
            "first_different_source_frame": contract["window"]["first_source_frame"] + first_difference,
            "perturbed_ledger_sha256": summaries["one_frame_perturbation"]["semantic_ledger_sha256"],
        },
        "exclusions": contract["exclusions"],
    }
    OUT_PATH.write_bytes(canonical(manifest))
    return manifest


def self_test() -> None:
    contract = load_json(CONTRACT_PATH)
    good = {"mame": {"version": contract["target"]["mame_version"], "sha256": contract["target"]["mame_sha256"]},
            "roms": ([{"name": name, "sha256": value}
                      for name, value in contract["canonical_rom_sha256"].items()] +
                     [{"name": name, "sha256": value}
                      for name, value in contract.get("noncanonical_local_dependencies", {}).items()]),
            "config_sha256": "a", "nvram_baseline_sha256": "b"}
    validate_provenance(contract, good)
    controls = {
        "wrong_set": (lambda value: value["roms"].pop()),
        "wrong_rom_hash": (lambda value: value["roms"].__setitem__(0, {"name": value["roms"][0]["name"], "sha256": "0" * 64})),
        "wrong_schema": (lambda value: value.__setitem__("schema", 999)),
    }
    for name, mutate in controls.items():
        candidate_contract = copy.deepcopy(contract)
        candidate_input = copy.deepcopy(good)
        if name == "wrong_schema": mutate(candidate_contract)
        else: mutate(candidate_input)
        try:
            validate_provenance(candidate_contract, candidate_input)
        except ValueError:
            continue
        raise AssertionError("negative control did not reject %s" % name)
    header = expected_header(contract)
    assert len(header) > 10
    assert "e_attack" in header
    print("vertical-slice oracle self-test: schema and rejection controls pass")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.generate:
        manifest = generate()
        print("vertical-slice oracle: PASS frames=%d ledger=%s" %
              (manifest["cold_runs"]["summary"]["frame_count"],
               manifest["cold_runs"]["summary"]["semantic_ledger_sha256"]))
    if not args.generate and not args.self_test:
        parser.error("choose --generate or --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
