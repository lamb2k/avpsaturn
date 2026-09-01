#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x3d/type-24 source program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class10_spec", ROOT / "tools/build_spec02_class10_type24.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_auxiliary_authority.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_auxiliary_b"
OUT = ROOT / "data/spec02_class3d_type24_program.json"
PROGRAM_FIRST = 0x0887C8
PROGRAM_LAST_EXCLUSIVE = 0x0888A0
OPCODE_SHA256 = base.OPCODE_SHA256

TABLES = {"top_state_high_byte": (0x0887D4, 4)}
COMPUTED_SITES = {0x0887D0: 0x0887D4}
EXTERNAL_TRANSFER_OWNERS = {
    0x016518: "shared-animation-runtime-entry",
    0x016536: "shared-animation-movement-interpreter",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x0177F0: "type24-fixed-pool-release",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def semantic(rows_: list[dict[str, str]]) -> str:
    return hashlib.sha256(json.dumps(
        rows_, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()


def dynamic_witness(directory: Path) -> dict[str, object]:
    entries = [x for x in rows(directory / "aux_entries.tsv")
               if x["type"] == "24" and x["class"] == "3d"]
    samples = [x for x in rows(directory / "aux_samples.tsv")
               if x["type"] == "24" and x["class"] == "3d"]
    writes = [x for x in rows(directory / "aux_writes.tsv")
              if x["type"] == "24" and x["class"] == "3d"]
    rng = [x for x in rows(directory / "aux_rng.tsv")
           if x["type"] == "24" and x["class"] == "3d"]
    effects = [x for x in rows(directory / "aux_player_effects.tsv")
               if x["owner_type"] == "24" and x["owner_class"] == "3d"]
    contexts = sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}"
                       for x in entries})
    require(contexts == ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x3d reachable context drift")
    context_rows = {}
    for context in contexts:
        state, phase = (int(part, 16) for part in context.split(":"))
        ws = [x for x in writes if int(x["state"]) == state and int(x["phase"]) == phase]
        ss = [x for x in samples if int(x["state"]) == state and int(x["phase"]) == phase]
        context_rows[context] = {
            "outer_state_u16": state, "substate_u16": phase,
            "writer_pcs": sorted({f"0x{int(x['pc'], 16):06x}" for x in ws}),
            "written_actor_offsets": sorted({f"0x{int(x['offset'], 16):02x}" for x in ws}),
            "animation_records": sorted({f"0x{int(x['anim'], 16):08x}" for x in ss}),
            "assemblies": sorted({f"0x{int(x['assembly'], 16):08x}" for x in ss}),
            "hurt_selectors_u8": sorted({int(x["hurt"]) for x in ss}),
            "attack_selectors_u8": sorted({int(x["attack"]) for x in ss}),
        }
    return {
        "counts": {"entries": len(entries), "samples": len(samples),
                   "writes": len(writes), "rng_calls": len(rng),
                   "player_effects": len(effects)},
        "semantic_sha256": {"entries": semantic(entries), "samples": semantic(samples),
                            "writes": semantic(writes), "rng": semantic(rng),
                            "player_effects": semantic(effects)},
        "contexts": context_rows,
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and base.base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = base.base.load_json(ORACLE)
    archetype = next(x for x in oracle["archetypes"]
                     if x["class"] == "0x3d" and x["type"] == 24)
    dependency = oracle["first_segment_dependencies"][
        "predator_special_type24_effects"]["class_0x3d"]
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x0887c8" and
            dependency["source_body"]["first"] == "0x0887c8" and
            dependency["source_body"]["last_exclusive"] == "0x0888a0",
            "accepted class-0x3d Oracle authority drift")
    image = OPCODES.read_bytes()
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x3d semantic witness drift")
    movement_words = [int.from_bytes(image[address:address + 2], "big", signed=True)
                      for address in range(0x088864, 0x0888A4, 2)]
    movement_offsets = [movement_words[index:index + 2]
                        for index in range(0, len(movement_words), 2)]
    require(movement_offsets == dependency["state_0x0200"]["movement_offsets_s16"],
            "class-0x3d movement offset table drift")
    return {
        "schema": "spec02-class3d-type24-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-24 class-0x3d",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "entry": "0x0887c8", "program_window": ["0x0887c8", "0x0888a0"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record24", "record_type_u8": 24, "class_u8": 61,
            "entry_dispatch": "0x0887c8",
            "order": "accepted fixed type-24 pool order; one entry per active slot per scheduler invocation",
        },
        "field_types": {
            "actor+0x03": "variant_u8", "actor+0x04": "outer_state_u16_be",
            "actor+0x09": "coordinate_mode_u8", "actor+0x0a": "presentation_selector_u16",
            "actor+0x0c": "direction_u8", "actor+0x0f": "palette_u8",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s16",
            "actor+0x18": "world_z_s16", "actor+0x1c": "animation_record_u32",
            "actor+0x24": "animation_branch_s16", "actor+0x2e": "object_flags_u16",
            "actor+0x38": "anchor_x_s16", "actor+0x3c": "anchor_z_s16",
        },
        "dispatch": dispatch,
        "movement_table": {
            "entry_count": 16, "base": "0x088864",
            "element_type": "pair<s16_be>", "values": movement_offsets,
            "sha256": hashlib.sha256(image[0x088864:0x0888A4]).hexdigest(),
            "selection": "variant_u8 indexes the table; x is negated when direction_u8 is nonzero; z is copied to y; variant advances by eight modulo sixteen",
        },
        "animation_record_base": "0x0009a7ec",
        "unwritten_field_retention": dependency["unwritten_field_retention"],
        "reachable_state_substate_contexts": ["0000:0000", "0200:0000", "0400:0000"],
        "normalized_source_program": {
            "representation": "bounded class-specific 68000 operations with explicit widths, reads, writes, guards and branch targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(base.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": base.field_profiles(instructions),
            "external_transfers": external,
        },
        "dynamic_witness": witness_a,
        "presentation_collision": archetype["presentation_and_collision"],
        "counterfactual": archetype["counterfactual"],
        "rng": archetype["rng"],
        "mutation_controls": {
            "wrong_dispatch_target_rejected": True, "omitted_reachable_context_rejected": True,
            "wrong_operand_width_or_signed_branch_rejected": True, "wrong_actor_field_rejected": True,
            "fixed_frame_transition_rejected": True, "movement_offset_or_sign_mutation_rejected": True,
            "unwritten_y_field_clear_rejected": True,
            "presentation_or_collision_substitution_rejected": True,
            "release_suppression_is_discriminating": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True, "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x3d status drift")
    require(value["reachable_state_substate_contexts"] ==
            ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x3d context closure incomplete")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 34 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "cd19a563651cbe39672e4cbe28887c841fe8eafa3cad22bd4e91eb7313c4fdf4" and
            hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest() ==
                program["instructions_sha256"],
            "class-0x3d instruction closure incomplete")
    require(len(program["field_access_profiles"]) == 11,
            "class-0x3d field-access closure incomplete")
    require(len(program["external_transfers"]) == 4,
            "class-0x3d external-transfer closure incomplete")
    require(len(value["dispatch"]) == 1 and
            sum(x["entry_count"] for x in value["dispatch"].values()) == 4,
            "class-0x3d dispatch closure incomplete")
    require(value["movement_table"]["entry_count"] == 16 and
            value["movement_table"]["values"][0] == [-61, -13] and
            value["movement_table"]["values"][8] == [61, 13] and
            value["movement_table"]["values"][-1] == [-72, 0] and
            value["movement_table"]["sha256"] ==
                "15e0fc64a7ecbd8ee0c9008f43b9c757cee36991339401e8b383d30f06ed4ecf",
            "class-0x3d movement table incomplete")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 11476, "samples": 12811, "writes": 121404,
                "rng_calls": 0, "player_effects": 0},
            "class-0x3d retained witness count drift")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "e5b0ded528dcca2788ac027ac6fa832fb436126b23e2f00046c207b8eef5317f",
                "samples": "2f37d9a647fea0ddbe9fde37412aea1c27d4b42be3e73c1284cfdf606205713a",
                "writes": "e500c30a6189ba5dceaef9c92011b38dd1067c5a33a4793850bd4a3a68a08233",
                "rng": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                "player_effects": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            }, "class-0x3d paired semantic identity drift")
    require(not any(x["owner"].startswith("UNKNOWN")
                    for x in program["external_transfers"]),
            "class-0x3d external transfer unowned")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "class-0x3d mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x3d SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x3d/type-24 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
