#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x4e/type-24 source program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class4b_spec", ROOT / "tools/build_spec02_class4b_type24.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_auxiliary_authority.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_auxiliary_b"
OUT = ROOT / "data/spec02_class4e_type24_program.json"
PROGRAM_FIRST = 0x0927F6
PROGRAM_LAST_EXCLUSIVE = 0x0928AA
OPCODE_SHA256 = base.OPCODE_SHA256
PROGRAM_SHA256 = "0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9"

TABLES = {"top_state_byte": (0x092802, 4)}
COMPUTED_SITES = {0x0927FE: 0x092802}
EXTERNAL_TRANSFER_OWNERS = {
    0x016518: "shared-animation-runtime-entry",
    0x016536: "shared-animation-movement-interpreter",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x0177F0: "type24-fixed-pool-release",
    0x017C5E: "shared-source-rng",
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
               if x["type"] == "24" and x["class"] == "4e"]
    samples = [x for x in rows(directory / "aux_samples.tsv")
               if x["type"] == "24" and x["class"] == "4e"]
    writes = [x for x in rows(directory / "aux_writes.tsv")
              if x["type"] == "24" and x["class"] == "4e"]
    rng = [x for x in rows(directory / "aux_rng.tsv")
           if x["type"] == "24" and x["class"] == "4e"]
    effects = [x for x in rows(directory / "aux_player_effects.tsv")
               if x["owner_type"] == "24" and x["owner_class"] == "4e"]
    contexts = sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}"
                       for x in entries})
    require(contexts == ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x4e paired witness context drift")
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
    require(PROGRAM.is_file() and base.base.sha256(PROGRAM) == PROGRAM_SHA256,
            "accepted decrypted program-data image missing or drifted")
    oracle = base.base.load_json(ORACLE)
    archetype = next(x for x in oracle["archetypes"]
                     if x["class"] == "0x4e" and x["type"] == 24)
    dependency = oracle["first_segment_dependencies"][
        "class_0x4e_type24_variant4_effect"]
    variant10 = dependency["variant10_collision_effect"]
    source_body = variant10["source_bodies"]["class_dispatch"]
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x0927f6" and
            source_body["first"] == "0x0927f6" and
            source_body["last_exclusive"] == "0x0928aa" and
            dependency["dispatch"] == "0x0927f6",
            "accepted class-0x4e Oracle authority drift")
    image = OPCODES.read_bytes()
    program_data = PROGRAM.read_bytes()
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x4e semantic witness drift")
    jitter_words = [int.from_bytes(image[address:address + 2], "big", signed=True)
                    for address in range(0x092866, 0x092886, 2)]
    jitter_pairs = [jitter_words[index:index + 2]
                    for index in range(0, len(jitter_words), 2)]
    selector_offsets = [int.from_bytes(program_data[address:address + 2], "big")
                        for address in range(0x0928AA, 0x0928DE, 2)]
    require(jitter_pairs == dependency["jitter_table_s16"],
            "class-0x4e accepted jitter table drift")
    return {
        "schema": "spec02-class4e-type24-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch and impact variant of record-type-24 class-0x4e",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "program_data_sha256": PROGRAM_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "entry": "0x0927f6", "program_window": ["0x0927f6", "0x0928aa"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record24", "record_type_u8": 24, "class_u8": 78,
            "entry_dispatch": "0x0927f6",
            "order": "accepted fixed type-24 pool order; collision allocation occurs after this pool and state-0 initialization on the next scheduler visit",
        },
        "field_types": {
            "actor+0x03": "impact_variant_u8", "actor+0x04": "outer_state_u8",
            "actor+0x09": "coordinate_mode_u8", "actor+0x0a": "animation_timer_u16_be",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s16",
            "actor+0x1c": "animation_record_u32", "actor+0x24": "animation_branch_s16",
            "actor+0x2e": "object_flags_u16", "actor+0x4f": "reaction_facing_u8",
            "rng.seed": "source_global_u16",
        },
        "dispatch": dispatch,
        "reachable_state_substate_contexts": ["0000:0000", "0200:0000", "0400:0000"],
        "unreachable_dispatch_entries": {
            "0600:0000": "fourth source table entry aliases the state-4 release body; no accepted Round 1 route or counterfactual enters it",
        },
        "variant_tables": {
            "entry_count": 26,
            "reachable_variant_u8": [0, 1, 4, 5, 10, 20, 24, 25],
            "animation_record_offset_table": {
                "source_view": "accepted decrypted program-data image",
                "base": "0x0928aa", "element_type": "u16_be",
                "values": selector_offsets,
                "resolved_record_bases": [f"0x{0x0928AA + value:08x}"
                                          for value in selector_offsets],
                "sha256": hashlib.sha256(
                    program_data[0x0928AA:0x0928DE]).hexdigest(),
            },
            "rng_jitter_table": {
                "source_view": "accepted decrypted opcode image",
                "base": "0x092866", "element_type": "pair<s16_be>",
                "values": jitter_pairs,
                "sha256": hashlib.sha256(image[0x092866:0x092886]).hexdigest(),
            },
            "selection": "variant_u8 indexes the 26-entry animation-record table; variants 24 and 25 use facing-relative signed X displacement, all other reachable variants consume one source RNG call and index the eight-pair jitter table with rng_result & 0x001c",
        },
        "state_contract": dependency,
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
            "fixed_frame_transition_rejected": True, "impact_variant_substitution_rejected": True,
            "rng_call_or_consumption_order_mutation_rejected": True,
            "jitter_table_or_mask_mutation_rejected": True,
            "variant24_25_facing_branch_mutation_rejected": True,
            "animation_selector_or_terminal_order_mutation_rejected": True,
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
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x4e status drift")
    require(value["reachable_state_substate_contexts"] ==
            ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x4e context closure incomplete")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 31 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "6ed7f89057dbe457f049d87df2ad1d9855f5aea0ac5ea34c71d5fd61b05e3d8d" and
            hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest() ==
                program["instructions_sha256"],
            "class-0x4e instruction closure incomplete")
    require(len(program["field_access_profiles"]) == 8,
            "class-0x4e field-access closure incomplete")
    require(len(program["external_transfers"]) == 5 and
            not any(x["owner"].startswith("UNKNOWN") for x in program["external_transfers"]),
            "class-0x4e external-transfer closure incomplete")
    require(len(value["dispatch"]) == 1 and
            sum(x["entry_count"] for x in value["dispatch"].values()) == 4 and
            value["unreachable_dispatch_entries"] == {
                "0600:0000": "fourth source table entry aliases the state-4 release body; no accepted Round 1 route or counterfactual enters it"},
            "class-0x4e dispatch closure incomplete")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 848, "samples": 909, "writes": 3732,
                "rng_calls": 80, "player_effects": 0},
            "class-0x4e retained witness count drift")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "4ff47cc6171169c28884e1b63936049a4e248d0ec0e179c8244ee6dd1b4b6ce3",
                "samples": "497775ba60b74fb47bd9b921f2203450fc4d358658568809811729d01eed4bb4",
                "writes": "98858835303ded7dfbabf5afe132ad8499405e1d0d466bf1f8f24aa3f70274a4",
                "rng": "96cf8dfb352682df963f0494392f6bfa3145927cdfd7929288cbaaf3c2937a34",
                "player_effects": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            }, "class-0x4e paired semantic identity drift")
    variants = value["variant_tables"]
    require(variants["entry_count"] == 26 and
            variants["reachable_variant_u8"] == [0, 1, 4, 5, 10, 20, 24, 25] and
            variants["animation_record_offset_table"]["sha256"] ==
                "9f5981283b009426f7e7a79c4f60a24cc84dc9ed31fee12aca3ea5831be35b19" and
            variants["rng_jitter_table"]["values"] ==
                [[0, 0], [4, 0], [4, -4], [4, 4], [-4, 0], [-4, -4], [-4, 4], [-8, 8]] and
            variants["rng_jitter_table"]["sha256"] ==
                "23fce65ab50565273c5e3c5c678b4e29b94ac9d638e39e9111bb918e4dbfe835",
            "class-0x4e variant-table closure incomplete")
    state = value["state_contract"]
    require(state["variant_u8"] == 4 and len(state["animation_records"]) == 5 and
            state["state_sequence_u16"] == [0, 512, 1024] and
            state["variant0_collision_effect"]["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            state["variant1_collision_effect"]["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            state["variant10_collision_effect"]["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            sorted(int(x) for x in state["variant10_collision_effect"]
                   ["shared_dispatch_reachable_variant_programs"]) == [5, 20],
            "class-0x4e state or impact-variant closure incomplete")
    require(len(value["presentation_collision"]["records"]) == 53 and
            value["rng"] == {"calls": 80, "caller_pcs": {"0x092830": 80},
                             "orphan_calls": 0},
            "class-0x4e presentation or RNG ownership drift")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "class-0x4e mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x4e SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x4e/type-24 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
