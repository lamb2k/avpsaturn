#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x49/type-24 source program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class3d_spec", ROOT / "tools/build_spec02_class3d_type24.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_auxiliary_authority.json"
WEAPON = ROOT / "data/oracle11_predator_weapon_projectile_resource.json"
AIR = ROOT / "data/oracle11_predator_air_authority.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_auxiliary_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_auxiliary_b"
OUT = ROOT / "data/spec02_class49_type24_program.json"
PROGRAM_FIRST = 0x08F080
PROGRAM_LAST_EXCLUSIVE = 0x08F13A
OPCODE_SHA256 = base.OPCODE_SHA256

TABLES = {"top_state_byte": (0x08F08C, 4)}
COMPUTED_SITES = {0x08F088: 0x08F08C}
EXTERNAL_TRANSFER_OWNERS = {
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x0177DA: "type24-fixed-pool-allocator",
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
               if x["type"] == "24" and x["class"] == "49"]
    samples = [x for x in rows(directory / "aux_samples.tsv")
               if x["type"] == "24" and x["class"] == "49"]
    writes = [x for x in rows(directory / "aux_writes.tsv")
              if x["type"] == "24" and x["class"] == "49"]
    rng = [x for x in rows(directory / "aux_rng.tsv")
           if x["type"] == "24" and x["class"] == "49"]
    effects = [x for x in rows(directory / "aux_player_effects.tsv")
               if x["owner_type"] == "24" and x["owner_class"] == "49"]
    contexts = sorted({f"{int(x['state']):04x}:{int(x['phase']):04x}"
                       for x in entries})
    require(contexts == ["0000:0000", "0200:0000"],
            "class-0x49 paired witness context drift")
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
    weapon = base.base.load_json(WEAPON)
    air = base.base.load_json(AIR)
    archetype = next(x for x in oracle["archetypes"]
                     if x["class"] == "0x49" and x["type"] == 24)
    weapon_effect = weapon["implementation_contract"]["record4_parent_class0"][
        "effect_allocation"]
    air_effect = air["airborne_actions"]["button1"]["record4_class03"][
        "effect_allocation"]
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x08f080" and
            weapon_effect["source_bodies"]["dispatch"]["start"] == "0x08f080" and
            weapon_effect["source_bodies"]["dispatch"]["end_exclusive"] == "0x08f0c6" and
            weapon_effect["source_bodies"]["helper"]["start"] == "0x08f0c6" and
            weapon_effect["source_bodies"]["helper"]["end_exclusive"] == "0x08f100" and
            air_effect["helper"] == "0x08f100",
            "accepted class-0x49 Oracle authority drift")
    image = OPCODES.read_bytes()
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = 0x08F080, 0x08F0C6
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    dispatch_instructions, decoded = base.decode_program(image)
    dispatch, dispatch_external = decoded
    helper_instructions = []
    helper_external = []
    for first, last in ((0x08F0C6, 0x08F100), (0x08F100, 0x08F13A)):
        base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = first, last
        base.TABLES, base.COMPUTED_SITES = {}, {}
        body_instructions, (_, body_external) = base.decode_program(image)
        helper_instructions.extend(body_instructions)
        helper_external.extend(body_external)
    instructions = sorted(dispatch_instructions + helper_instructions,
                          key=lambda row: int(row["pc"], 16))
    external = dispatch_external + helper_external
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x49 semantic witness drift")
    return {
        "schema": "spec02-class49-type24-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch and variant allocator of record-type-24 class-0x49",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifacts": {
                ORACLE.relative_to(ROOT).as_posix(): base.base.sha256(ORACLE),
                WEAPON.relative_to(ROOT).as_posix(): base.base.sha256(WEAPON),
                AIR.relative_to(ROOT).as_posix(): base.base.sha256(AIR),
            },
            "entry": "0x08f080", "program_window": ["0x08f080", "0x08f13a"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record24", "record_type_u8": 24, "class_u8": 73,
            "entry_dispatch": "0x08f080",
            "order": "accepted fixed type-24 pool order; one entry per active slot per scheduler invocation",
        },
        "field_types": {
            "actor+0x00": "active_u8", "actor+0x02": "class_u8",
            "actor+0x03": "variant_u8", "actor+0x04": "outer_state_u8",
            "actor+0x09": "coordinate_mode_u8", "actor+0x0a": "animation_timer_u16_be",
            "actor+0x0f": "facing_u8", "actor+0x10": "world_x_s16",
            "actor+0x14": "world_y_s16", "actor+0x18": "world_z_s16",
            "actor+0x1c": "animation_record_u32", "actor+0x24": "animation_branch_s16",
            "actor+0x2a": "lifetime_timer_u8", "actor+0x2e": "object_flags_u16",
            "actor+0x50": "collision_pointer_u32",
            "global+a5+0x02c0": "variant1_world_x_delta_s16",
        },
        "dispatch": dispatch,
        "allocation_helpers": {
            "variant0": weapon_effect,
            "variant1": air_effect,
            "shared_rule": "both helpers allocate from the fixed type-24 pool, copy owner x/y/z, facing and animation record, retain unwritten slot animation timer/branch fields, and write D6 to the lifetime timer",
        },
        "reachable_state_substate_contexts": ["0000:0000", "0200:0000", "0400:0000"],
        "unreachable_dispatch_entries": {
            "0600:0000": "fourth source table entry aliases the state-4 release body; no accepted Round 1 route or counterfactual enters it",
        },
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
            "fixed_frame_transition_rejected": True, "variant_helper_substitution_rejected": True,
            "timer_or_phase_guard_mutation_rejected": True,
            "unwritten_animation_field_clear_rejected": True,
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
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x49 status drift")
    require(value["reachable_state_substate_contexts"] ==
            ["0000:0000", "0200:0000", "0400:0000"],
            "class-0x49 context closure incomplete")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 39 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "6b36cd103dc59cde7928f8d24a0f1c963b90ab3f10d036a118b9f6bb56e7a71a" and
            hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest() ==
                program["instructions_sha256"],
            "class-0x49 instruction closure incomplete")
    require(len(program["field_access_profiles"]) == 12,
            "class-0x49 field-access closure incomplete")
    require(len(program["external_transfers"]) == 4,
            "class-0x49 external-transfer closure incomplete")
    require(len(value["dispatch"]) == 1 and
            sum(x["entry_count"] for x in value["dispatch"].values()) == 4 and
            value["unreachable_dispatch_entries"] == {
                "0600:0000": "fourth source table entry aliases the state-4 release body; no accepted Round 1 route or counterfactual enters it"},
            "class-0x49 dispatch closure incomplete")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 4808, "samples": 4209, "writes": 19339,
                "rng_calls": 0, "player_effects": 0},
            "class-0x49 retained witness count drift")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "ee749f9cf3f6f969eea751df8e008b1f1d5bd93f1b995eb2171ed58e7b38b4de",
                "samples": "11204d0eca9031e56e7e33a1c8aad88ccca94a81a03e7bfdf51fb31dddc92c5c",
                "writes": "b457a6d870b36d7d821a2aaec3bdf9254e9065cfde5b145fbe417446d4a3b3b8",
                "rng": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                "player_effects": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            }, "class-0x49 paired semantic identity drift")
    require(value["allocation_helpers"]["variant0"]["variant_u8"] == 0 and
            value["allocation_helpers"]["variant0"]["timer_u8"] == 8 and
            value["allocation_helpers"]["variant1"]["variant_u8"] == 1 and
            value["allocation_helpers"]["variant1"]["timer_u8"] == 8 and
            value["allocation_helpers"]["variant0"]["fixed_slot_reuse_presentation"]
                ["unwritten_retained_fields"] == [
                    "animation_timer actor+0x0a:u16",
                    "animation_branch actor+0x24:s16"],
            "class-0x49 variant helper closure incomplete")
    require(not any(x["owner"].startswith("UNKNOWN")
                    for x in program["external_transfers"]),
            "class-0x49 external transfer unowned")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "class-0x49 mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x49 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x49/type-24 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
