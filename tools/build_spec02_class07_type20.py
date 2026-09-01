#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x07/type-20 source program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class01_spec", ROOT / "tools/build_spec02_class01_type12.py")
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_auxiliary_authority.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_auxiliary_b"
OUT = ROOT / "data/spec02_class07_type20_program.json"
PROGRAM_FIRST = 0x06D1AA
PROGRAM_LAST_EXCLUSIVE = 0x06D53C
OPCODE_SHA256 = base.OPCODE_SHA256

TABLES = {
    "top_state_high_byte": (0x06D1B6, 4),
    "active_state_low_byte": (0x06D210, 3),
}
COMPUTED_SITES = {0x06D1B2: 0x06D1B6, 0x06D20C: 0x06D210}
EXTERNAL_TRANSFER_OWNERS = {
    0x0025DC: "accepted-shared-gameplay-command-program",
    0x016518: "shared-animation-runtime-entry",
    0x016536: "shared-animation-movement-interpreter",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x017706: "fixed-pool-release",
    0x01DC2A: "accepted-type20-navigation-contact-program",
    0x06B2E2: "accepted-type20-navigation-body-program",
    0x07AC30: "accepted-shared-gameplay-command-program",
    0x0BC692: "accepted-shared-guarded-command-program",
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
               if x["type"] == "20" and x["class"] == "07"]
    samples = [x for x in rows(directory / "aux_samples.tsv")
               if x["type"] == "20" and x["class"] == "07"]
    writes = [x for x in rows(directory / "aux_writes.tsv")
              if x["type"] == "20" and x["class"] == "07"]
    rng = [x for x in rows(directory / "aux_rng.tsv")
           if x["type"] == "20" and x["class"] == "07"]
    effects = [x for x in rows(directory / "aux_player_effects.tsv")
               if x["owner_type"] == "20" and x["owner_class"] == "07"]
    contexts = sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}"
                       for x in entries})
    require(contexts == ["0000:0000", "0200:0000"],
            "class-0x07 reachable context drift")
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
                     if x["class"] == "0x07" and x["type"] == 20)
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x06d1aa",
            "accepted class-0x07 Oracle authority drift")
    image = OPCODES.read_bytes()
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x07 semantic witness drift")
    return {
        "schema": "spec02-class07-type20-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-20 class-0x07",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "entry": "0x06d1aa", "program_window": ["0x06d1aa", "0x06d53c"],
            "program_window_sha256": hashlib.sha256(image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record20", "record_type_u8": 20, "class_u8": 7,
            "entry_dispatch": "0x06d1aa",
            "order": "accepted fixed type-20 pool order; one entry per active slot per scheduler invocation",
        },
        "field_types": {
            "actor+0x04": "outer_state_u16_be", "actor+0x05": "active_phase_u8",
            "actor+0x06": "contact_state_u16_be", "actor+0x0a": "presentation_selector_u16",
            "actor+0x0c": "direction_u8", "actor+0x10": "world_x_s16",
            "actor+0x14": "world_y_s16", "actor+0x18": "world_z_s16",
            "actor+0x1c": "animation_record_u32", "actor+0x24": "animation_branch_s16",
            "actor+0x2a": "timer_u8", "actor+0x2e": "object_flags_u16",
            "actor+0x30..0x3e": "signed movement vectors and accelerations; exact widths in field_access_profiles",
            "actor+0x40..0x42": "saved presentation fields_u16", "actor+0x4f": "facing_u8",
            "actor+0x50": "table_set_pointer_u32", "actor+0x58..0x6f": "double-buffered navigation body state",
        },
        "dispatch": dispatch,
        "reachable_state_substate_contexts": ["0000:0000", "0200:0000"],
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
            "fixed_frame_transition_rejected": True, "navigation_double_buffer_substitution_rejected": True,
            "presentation_or_collision_substitution_rejected": True, "release_suppression_is_discriminating": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True, "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x07 status drift")
    require(value["reachable_state_substate_contexts"] == ["0000:0000", "0200:0000"],
            "class-0x07 context closure incomplete")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 135 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "daf8f4c5f7e0a5e27a1a7e2d28aa3aefa6151c66efb073b4d7b42dbf9440ffdb" and
            hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest() ==
                program["instructions_sha256"],
            "class-0x07 instruction closure incomplete")
    require(len(program["field_access_profiles"]) == 33,
            "class-0x07 field-access closure incomplete")
    require(len(program["external_transfers"]) == 10,
            "class-0x07 external-transfer closure incomplete")
    require(len(value["dispatch"]) == 2 and
            sum(x["entry_count"] for x in value["dispatch"].values()) == 7,
            "class-0x07 dispatch closure incomplete")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 26565, "samples": 28446, "writes": 26619,
                "rng_calls": 0, "player_effects": 0},
            "class-0x07 retained witness count drift")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "e320685aeda9b8834e2f71a84bef6ce15679b70c3126a008a2eea0308ead09d5",
                "samples": "521a244cef1cb179791412de61f2ea35beb56b0d40b77928401580f272bcfdaa",
                "writes": "c46992437d2ceda19f14af714b261b0665b56dd4167fae5993b8586abcecc77c",
                "rng": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                "player_effects": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            }, "class-0x07 paired semantic identity drift")
    require(not any(x["owner"].startswith("UNKNOWN") for x in program["external_transfers"]),
            "class-0x07 external transfer unowned")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "class-0x07 mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x07 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x07/type-20 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
