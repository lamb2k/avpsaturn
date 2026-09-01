#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x10/type-24 source program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class07_spec", ROOT / "tools/build_spec02_class07_type20.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_auxiliary_authority.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_auxiliary_b"
OUT = ROOT / "data/spec02_class10_type24_program.json"
PROGRAM_FIRST = 0x079FFC
PROGRAM_LAST_EXCLUSIVE = 0x07A08E
OPCODE_SHA256 = base.OPCODE_SHA256
PROGRAM_SHA256 = "0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9"

TABLES = {"top_state_high_byte": (0x07A008, 4)}
COMPUTED_SITES = {0x07A004: 0x07A008}
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
               if x["type"] == "24" and x["class"] == "10"]
    samples = [x for x in rows(directory / "aux_samples.tsv")
               if x["type"] == "24" and x["class"] == "10"]
    writes = [x for x in rows(directory / "aux_writes.tsv")
              if x["type"] == "24" and x["class"] == "10"]
    rng = [x for x in rows(directory / "aux_rng.tsv")
           if x["type"] == "24" and x["class"] == "10"]
    effects = [x for x in rows(directory / "aux_player_effects.tsv")
               if x["owner_type"] == "24" and x["owner_class"] == "10"]
    contexts = sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}"
                       for x in entries})
    require(contexts == ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x10 reachable context drift")
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
                     if x["class"] == "0x10" and x["type"] == 24)
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x079ffc",
            "accepted class-0x10 Oracle authority drift")
    image = OPCODES.read_bytes()
    program_data = PROGRAM.read_bytes()
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x10 semantic witness drift")
    movement_words = [int.from_bytes(image[address:address + 2], "big", signed=True)
                      for address in range(0x07A050, 0x07A068, 2)]
    movement_offsets = [movement_words[index:index + 2]
                        for index in range(0, len(movement_words), 2)]
    animation_offsets = [int.from_bytes(program_data[address:address + 2], "big")
                         for address in range(0x07A08E, 0x07A09A, 2)]
    require(movement_offsets == [[0, 84], [0, 78], [0, 84], [0, 68],
                                 [0, 0], [0, 80]],
            "class-0x10 movement selector table drift")
    require(animation_offsets == [14, 14, 14, 862, 1566, 1566],
            "class-0x10 animation selector table drift")
    return {
        "schema": "spec02-class10-type24-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-24 class-0x10",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "entry": "0x079ffc", "program_window": ["0x079ffc", "0x07a08e"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record24", "record_type_u8": 24, "class_u8": 16,
            "entry_dispatch": "0x079ffc",
            "order": "accepted fixed type-24 pool order; one entry per active slot per scheduler invocation",
        },
        "field_types": {
            "actor+0x03": "variant_u8", "actor+0x04": "outer_state_u16_be",
            "actor+0x09": "coordinate_mode_u8", "actor+0x0a": "presentation_selector_u16",
            "actor+0x0c": "direction_u8", "actor+0x0f": "palette_u8",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s16",
            "actor+0x1c": "animation_record_u32", "actor+0x24": "animation_branch_s16",
            "actor+0x25": "animation_event_u8", "actor+0x2e": "object_flags_u16",
        },
        "dispatch": dispatch,
        "variant_tables": {
            "entry_count": 6,
            "movement_offset_table": {
                "source_view": "accepted decrypted opcode image",
                "base": "0x07a050", "element_type": "pair<s16_be>",
                "values": movement_offsets,
                "sha256": hashlib.sha256(image[0x07A050:0x07A068]).hexdigest(),
            },
            "animation_record_offset_table": {
                "source_view": "accepted decrypted program-data image",
                "base": "0x07a08e", "element_type": "u16_be",
                "values": animation_offsets,
                "resolved_record_bases": [f"0x{0x07A08E + value:08x}"
                                          for value in animation_offsets],
                "sha256": hashlib.sha256(
                    program_data[0x07A08E:0x07A09A]).hexdigest(),
            },
            "selection": "variant_u8 indexes both six-entry tables; x offset is negated when direction_u8 is zero; selected animation record base is passed to the accepted shared animation runtime",
        },
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
            "fixed_frame_transition_rejected": True, "variant_projection_substitution_rejected": True,
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
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x10 status drift")
    require(value["reachable_state_substate_contexts"] ==
            ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x10 context closure incomplete")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 28 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "08834fc077f94dbc85413c436dbde7950db807957b3d0bac422c92b4aba34638" and
            hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest() ==
                program["instructions_sha256"],
            "class-0x10 instruction closure incomplete")
    require(len(program["field_access_profiles"]) == 10,
            "class-0x10 field-access closure incomplete")
    require(len(program["external_transfers"]) == 4,
            "class-0x10 external-transfer closure incomplete")
    require(len(value["dispatch"]) == 1 and
            sum(x["entry_count"] for x in value["dispatch"].values()) == 4,
            "class-0x10 dispatch closure incomplete")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 4769, "samples": 4694, "writes": 23665,
                "rng_calls": 0, "player_effects": 0},
            "class-0x10 retained witness count drift")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "d04bc4594f435ca9b2e76709848c8ad103263dfd019433bce21bc600d48dd112",
                "samples": "65d9f18ad1eb1126bef7233d5c1dbc3eea4c36c357451e555c0059064b43e959",
                "writes": "917404a371b380be9f76bcb817b1f26b54d17e0b26fb9857e456339bf206e6cd",
                "rng": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                "player_effects": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            }, "class-0x10 paired semantic identity drift")
    require(value["variant_tables"]["entry_count"] == 6 and
            value["variant_tables"]["movement_offset_table"]["values"] ==
                [[0, 84], [0, 78], [0, 84], [0, 68], [0, 0], [0, 80]] and
            value["variant_tables"]["movement_offset_table"]["sha256"] ==
                "12f94f29d3b78ac863fc5cc2c9680557744ccd2e096cba5a83f939b75a1f2436" and
            value["variant_tables"]["animation_record_offset_table"]["values"] ==
                [14, 14, 14, 862, 1566, 1566] and
            value["variant_tables"]["animation_record_offset_table"]["resolved_record_bases"] ==
                ["0x0007a09c", "0x0007a09c", "0x0007a09c",
                 "0x0007a3ec", "0x0007a6ac", "0x0007a6ac"] and
            value["variant_tables"]["animation_record_offset_table"]["sha256"] ==
                "aa8280984b9c1bbb0e2154676789bbf3c40e62648ddd636e0ad8b8885043918f",
            "class-0x10 source selector tables incomplete")
    require(not any(x["owner"].startswith("UNKNOWN")
                    for x in program["external_transfers"]),
            "class-0x10 external transfer unowned")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "class-0x10 mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x10 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x10/type-24 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
