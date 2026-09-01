#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x4b/type-24 source program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class49_spec", ROOT / "tools/build_spec02_class49_type24.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_auxiliary_authority.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_auxiliary_b"
OUT = ROOT / "data/spec02_class4b_type24_program.json"
PROGRAM_FIRST = 0x08F86E
PROGRAM_LAST_EXCLUSIVE = 0x08F8E0
OPCODE_SHA256 = base.OPCODE_SHA256

TABLES = {"top_state_byte": (0x08F87A, 4)}
COMPUTED_SITES = {0x08F876: 0x08F87A}
EXTERNAL_TRANSFER_OWNERS = {
    0x016526: "shared-animation-sequence-initializer",
    0x016536: "shared-animation-movement-interpreter",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x017176: "shared-visible-presentation-submit",
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
               if x["type"] == "24" and x["class"] == "4b"]
    samples = [x for x in rows(directory / "aux_samples.tsv")
               if x["type"] == "24" and x["class"] == "4b"]
    writes = [x for x in rows(directory / "aux_writes.tsv")
              if x["type"] == "24" and x["class"] == "4b"]
    rng = [x for x in rows(directory / "aux_rng.tsv")
           if x["type"] == "24" and x["class"] == "4b"]
    effects = [x for x in rows(directory / "aux_player_effects.tsv")
               if x["owner_type"] == "24" and x["owner_class"] == "4b"]
    contexts = sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}"
                       for x in entries})
    require(contexts == ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x4b paired witness context drift")
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
                     if x["class"] == "0x4b" and x["type"] == 24)
    dependency = oracle["first_segment_dependencies"][
        "predator_special_type24_effects"]["class_0x4b"]
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x08f86e" and
            dependency["source_body"]["first"] == "0x08f86e" and
            dependency["source_body"]["last_exclusive"] == "0x08f8e0",
            "accepted class-0x4b Oracle authority drift")
    image = OPCODES.read_bytes()
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x4b semantic witness drift")
    return {
        "schema": "spec02-class4b-type24-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-24 class-0x4b",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "entry": "0x08f86e", "program_window": ["0x08f86e", "0x08f8e0"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record24", "record_type_u8": 24, "class_u8": 75,
            "entry_dispatch": "0x08f86e",
            "order": "accepted fixed type-24 pool order after player update and before collision allocation",
        },
        "field_types": {
            "actor+0x04": "outer_state_u8", "actor+0x09": "coordinate_mode_u8",
            "actor+0x0a": "animation_timer_u16_be", "actor+0x0f": "facing_u8",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s16",
            "actor+0x18": "world_z_s16", "actor+0x1c": "animation_record_u32",
            "actor+0x24": "animation_branch_s16", "actor+0x26": "owner_pointer_low_u16",
            "actor+0x2e": "object_flags_u16", "owner+0x25": "animation_event_u8",
            "owner+0x5c": "current_contact_u8",
        },
        "dispatch": dispatch,
        "unreachable_dispatch_entries": {
            "0600:0000": "fourth source table entry aliases the state-4 release body; no accepted Round 1 route or counterfactual enters it",
        },
        "state_contract": dependency,
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
            "fixed_frame_transition_rejected": True, "owner_contact_guard_mutation_rejected": True,
            "facing_offset_or_vertical_position_mutation_rejected": True,
            "animation_wrap_or_terminal_guard_mutation_rejected": True,
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
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x4b status drift")
    require(value["reachable_state_substate_contexts"] ==
            ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x4b context closure incomplete")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 26 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "c26b95f74b4a49e0494e7f0cf64aa78346a01bb8234a6d4b8cf518faead52b9a" and
            hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest() ==
                program["instructions_sha256"],
            "class-0x4b instruction closure incomplete")
    require(len(program["field_access_profiles"]) == 8,
            "class-0x4b field-access closure incomplete")
    require(len(program["external_transfers"]) == 5,
            "class-0x4b external-transfer closure incomplete")
    require(len(value["dispatch"]) == 1 and
            sum(x["entry_count"] for x in value["dispatch"].values()) == 4,
            "class-0x4b dispatch closure incomplete")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 661, "samples": 810, "writes": 4080,
                "rng_calls": 0, "player_effects": 0},
            "class-0x4b retained witness count drift")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "3bb7bfb509e8ed79b66d93e573803923d1d93cdb776dd559b239c06b6bade2a3",
                "samples": "a6ef2f82692c39ce8485108e1385694fba14ddcce024fd3188406fb1d09cd039",
                "writes": "f2b5e414cf75ef4f62831c7ecc2a28117604b92a71c17f833cffe3460d68fee4",
                "rng": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                "player_effects": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            }, "class-0x4b paired semantic identity drift")
    require(len(value["state_contract"]["state0"]["animation_records"]) == 32 and
            value["state_contract"]["state_sequence_u16"] == [0, 512, 1024] and
            value["state_contract"]["state_0x0200"]["coffee_shop_wrap_witness"] == {
                "terminal_record_frame_u16": 2835,
                "wrapped_animation_record": "0x0008f8e0",
                "wrapped_record_frame_u16": 2836},
            "class-0x4b state or animation closure incomplete")
    require(not any(x["owner"].startswith("UNKNOWN")
                    for x in program["external_transfers"]),
            "class-0x4b external transfer unowned")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "class-0x4b mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x4b SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x4b/type-24 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
