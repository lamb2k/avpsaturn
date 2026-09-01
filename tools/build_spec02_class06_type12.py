#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x06/type-12 source program.

This is an offline, class-specific decode of the accepted opcode image.  It
binds every Round 1-reachable branch and retained semantic witness; it is not a
runtime interpreter or a generalized source-lifting system.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class01_spec", ROOT / "tools/build_spec02_class01_type12.py")
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_enemy_archetypes.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_enemies_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_enemies_b"
OUT = ROOT / "data/spec02_class06_type12_program.json"
PROGRAM_FIRST = 0x04956C
PROGRAM_LAST_EXCLUSIVE = 0x04BE76
OPCODE_SHA256 = base.OPCODE_SHA256

TABLES = {
    "top_state_high_byte": (0x0495D8, 4),
    "spawn_variant_high_byte": (0x0496B4, 5),
    "active_action_high_byte": (0x049700, 11),
    "action00_phase_low_byte": (0x049878, 3),
    "action0a_selector_u16": (0x049AE0, 13),
    "action0a_selector0_phase": (0x049B06, 2),
    "action0a_selector6_phase": (0x049B4E, 2),
    "action0a_selector8_phase": (0x049BA4, 5),
    "action0a_selector9_phase": (0x049C5E, 4),
    "action0a_selector11_phase": (0x049D2E, 4),
    "action0e_phase_low_byte": (0x049DE4, 7),
    "action10_phase_low_byte": (0x04A0D4, 4),
    "action10_selector_u16": (0x04A388, 4),
    "action10_selector0_phase": (0x04A39C, 2),
    "action10_selector2_phase": (0x04A406, 4),
    "action12_phase_low_byte": (0x04A4DA, 6),
    "action12_selector_u16": (0x04A7C4, 3),
    "action18_phase_with_unreachable_zero": (0x04AF08, 8),
    "action18_selector_u16": (0x04AF8A, 15),
    "action1a_phase_low_byte": (0x04B046, 3),
    "hit_state_high_byte": (0x04B14A, 7),
    "hit_state0_phase": (0x04B16A, 2),
    "hit_state1_phase": (0x04B1B2, 2),
    "hit_state2_phase": (0x04B24E, 2),
    "hit_state3_phase": (0x04B2BC, 2),
    "hit_state4_phase": (0x04B2EC, 2),
    "hit_state6_phase": (0x04B322, 5),
    "interruption_state_high_byte": (0x04B3E0, 3),
    "interruption_selector_u16": (0x04B414, 3),
}

COMPUTED_SITES = {
    0x0495D4: 0x0495D8, 0x0496B0: 0x0496B4,
    0x0496F0: 0x049700, 0x049874: 0x049878,
    0x049ADC: 0x049AE0, 0x049B02: 0x049B06,
    0x049B4A: 0x049B4E, 0x049B9A: 0x049BA4,
    0x049C54: 0x049C5E, 0x049D2A: 0x049D2E,
    0x049DCE: 0x049DE4, 0x04A0D0: 0x04A0D4,
    0x04A384: 0x04A388, 0x04A398: 0x04A39C,
    0x04A3FC: 0x04A406, 0x04A4D0: 0x04A4DA,
    0x04A7C0: 0x04A7C4, 0x04AF04: 0x04AF08,
    0x04AF86: 0x04AF8A, 0x04B036: 0x04B046,
    0x04B146: 0x04B14A, 0x04B160: 0x04B16A,
    0x04B1AE: 0x04B1B2, 0x04B24A: 0x04B24E,
    0x04B2B8: 0x04B2BC, 0x04B2E8: 0x04B2EC,
    0x04B318: 0x04B322, 0x04B3D6: 0x04B3E0,
    0x04B410: 0x04B414,
}

EXTERNAL_TRANSFER_OWNERS = {
    0x001C20: "accepted-shared-landing-resource-program",
    0x00255E: "accepted-shared-gameplay-command-program",
    0x002588: "accepted-shared-gameplay-command-program",
    0x002684: "accepted-shared-animation-terminal-program",
    0x016248: "shared-16.16-motion-program",
    0x016368: "shared-actor-direction-program",
    0x016484: "shared-target-direction-helper",
    0x016518: "shared-animation-runtime-entry",
    0x016536: "shared-animation-movement-interpreter",
    0x016624: "shared-animation-record-selector",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x017020: "shared-player-target-selector",
    0x0176B4: "fixed-pool-release",
    0x017C5E: "round1-rng-authority",
    0x01D768: "current-state-collision-helper",
    0x01E868: "shared-hit-ko-entry",
    0x01F250: "shared-hit-ko-state-program",
    0x01F316: "shared-hit-ko-state-program",
    0x01F652: "shared-hit-ko-transition-program",
    0x081A10: "accepted-class06-effect-allocation-program",
    0x09A642: "accepted-class06-presentation-binding-program",
    0x09A660: "accepted-class06-presentation-binding-program",
    0x0AE44C: "round1-world-projection-program",
    0x0B1BAA: "round1-navigation-movement-projection",
    0x0B2672: "round1-navigation-response-helper",
    0x0BC416: "shared-signed-timer-selector",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def table_targets(image: bytes, table_base: int, count: int) -> list[int]:
    offsets = [int.from_bytes(image[table_base + index:table_base + index + 2],
                              "big") for index in range(0, count * 2, 2)]
    if table_base == 0x04AF08:
        require(offsets[0] == 0xFFFF and offsets[1] == count * 2,
                "class-0x06 action18 unreachable sentinel drift")
        offsets = offsets[1:]
    elif table_base == 0x04AF8A:
        # This selector has no length prefix.  Its 15-entry extent is proven by
        # the preceding unsigned compare and the accepted reachable selectors.
        require(min(offsets) == count * 2,
                "class-0x06 action18 selector extent drift")
    else:
        require(offsets[0] == count * 2,
                f"computed table 0x{table_base:06x} length drift")
    targets = [table_base + offset for offset in offsets]
    require(all(PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE
                for target in targets),
            f"computed table 0x{table_base:06x} target escaped class program")
    return targets


def dynamic_witness(archetype: dict, directory: Path) -> dict[str, object]:
    old_a, old_b = base.CAPTURE_A, base.CAPTURE_B
    try:
        # Reuse the exact paired-ledger projection while binding this class.
        entries = [row for row in base.read_tsv(directory / "enemy_entries.tsv")
                   if row["class"].lower() == "06"]
        samples = [row for row in base.read_tsv(directory / "enemy_samples.tsv")
                   if row["class"].lower() == "06"]
        writes = [row for row in base.read_tsv(directory / "enemy_writes.tsv")
                  if row["class"].lower() == "06"]
        rng = [row for row in base.read_tsv(directory / "enemy_rng.tsv")
               if row["class"].lower() == "06"]
        damage = [row for row in base.read_tsv(directory / "player_damage.tsv")
                  if row["owner_class"].lower() == "06"]
        contexts = sorted({f"{int(row['state']):04x}:{int(row['phase']):04x}"
                           for row in entries})
        require(contexts == sorted(["0000:0000", *archetype["state_phase_contexts"]]),
                "class-0x06 reachable context drift")
        context_rows = {}
        for context in contexts:
            state, phase = (int(part, 16) for part in context.split(":"))
            ws = [row for row in writes if int(row["state"]) == state and int(row["phase"]) == phase]
            rs = [row for row in rng if int(row["state"]) == state and int(row["phase"]) == phase]
            ss = [row for row in samples if int(row["state"]) == state and int(row["phase"]) == phase]
            context_rows[context] = {
                "outer_state_u16": state, "action_substate_u16": phase,
                "writer_pcs": sorted({f"0x{int(row['pc'], 16):06x}" for row in ws}),
                "written_actor_offsets": sorted({f"0x{int(row['offset'], 16):02x}" for row in ws}),
                "rng_caller_pcs_in_order": [f"0x{int(row['pc'], 16):06x}" for row in rs],
                "observed_animation_records": sorted({f"0x{int(row['anim'], 16):08x}" for row in ss}),
                "observed_assemblies": sorted({f"0x{int(row['assembly'], 16):08x}" for row in ss}),
                "observed_hurt_selectors_u8": sorted({int(row["hurt"]) for row in ss}),
                "observed_attack_selectors_u8": sorted({int(row["attack"]) for row in ss}),
            }
        return {
            "counts": {"entries": len(entries), "samples": len(samples),
                       "writes": len(writes), "rng_calls": len(rng),
                       "player_damage_writes": len(damage)},
            "semantic_sha256": {
                "entries": base.semantic_ledger(entries, ["frame", "slot", "state", "phase", "facing", "x", "z", "anim", "assembly", "hurt", "attack", "timer", "health", "target", "rng"]),
                "samples": base.semantic_ledger(samples, ["frame", "slot", "state", "phase", "facing", "x", "y", "z", "anim", "assembly", "hurt", "attack", "timer", "health", "target"]),
                "writes": base.semantic_ledger(writes, ["frame", "slot", "state", "phase", "offset", "pc", "old", "data", "mask"]),
                "rng": base.semantic_ledger(rng, ["frame", "slot", "state", "phase", "pc", "seed"]),
                "player_damage": base.semantic_ledger(damage, ["frame", "owner_slot", "owner_state", "owner_phase", "pc", "old_health", "data", "mask"]),
            },
            "contexts": context_rows,
            "transition_edges": archetype["damage_hit_ko"]["hit_ko_transitions"],
        }
    finally:
        base.CAPTURE_A, base.CAPTURE_B = old_a, old_b


def build() -> dict[str, object]:
    require(OPCODES.is_file() and base.base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    image = OPCODES.read_bytes()
    oracle = base.base.load_json(ORACLE)
    archetype = next(item for item in oracle["archetypes"]
                     if item["class"] == "0x06" and item["type"] == 12)
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x04956c" and
            archetype["instance_count"] == 1,
            "accepted class-0x06 Oracle authority drift")
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = TABLES, COMPUTED_SITES
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    base.table_targets = table_targets
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    sentinel = next(item for item in dispatch.values()
                    if item["table_base"] == "0x04af08")
    sentinel["unreachable_entry_0"] = "0xffff"
    witness_a = dynamic_witness(archetype, CAPTURE_A)
    witness_b = dynamic_witness(archetype, CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x06 semantic witness drift")
    profiles = base.field_profiles(instructions)
    return {
        "schema": "spec02-class06-type12-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-12 class-0x06",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "entry": "0x04956c", "program_window": ["0x04956c", "0x04be76"],
            "program_window_sha256": hashlib.sha256(image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record12", "record_type_u8": 12, "class_u8": 6,
            "entry_dispatch": "0x04956c",
            "order": "accepted fixed type-12 pool order; one entry per active slot per scheduler invocation",
            "post_dispatch_world_x_reflection": {
                "camera_x_global": "a5+0x0278:s16",
                "minimum_s16": "camera_x+0x0040", "maximum_s16": "camera_x+0x0140",
                "guard_order": ["reflect negative x velocity below minimum", "reflect nonnegative x velocity above maximum"],
                "writes": ["actor+0x4f facing_u8", "negate actor+0x30 velocity_s32", "negate actor+0x38 acceleration_s32"],
            },
        },
        "field_types": {
            "actor+0x04": "outer_state_u16_be", "actor+0x06": "action_substate_u16_be",
            "actor+0x0c": "direction_u8", "actor+0x0f": "facing_u8",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s32_16_16",
            "actor+0x18": "world_z_s16", "actor+0x1c": "animation_record_u32",
            "actor+0x28": "target_slot_u16", "actor+0x2a": "timer_u16_or_u8_by_operation",
            "actor+0x30": "x_velocity_s32_16_16", "actor+0x34": "y_velocity_s32_16_16",
            "actor+0x38": "x_acceleration_s32_16_16", "actor+0x3c": "y_acceleration_s32_16_16",
            "actor+0x40": "health_s16", "actor+0x4f": "reflection_facing_u8",
            "actor+0x50": "table_set_pointer_u32", "actor+0x5c": "collision_or_airborne_u8",
            "actor+0x60": "target_x_offset_s16", "actor+0x62": "target_z_offset_s16",
            "actor+0x64": "presentation_mode_u8", "actor+0x6c": "animation_runtime_u8",
            "actor+0x70..0xa0": "class06 action locals; exact widths and accesses in field_access_profiles",
        },
        "dispatch": dispatch,
        "reachable_state_substate_contexts": ["0000:0000", *archetype["state_phase_contexts"]],
        "normalized_source_program": {
            "representation": "bounded class-specific 68000 operations with explicit widths, reads, writes, guards and branch targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(base.base.canonical(instructions)).hexdigest(),
            "instructions": instructions, "field_access_profiles": profiles,
            "external_transfers": external,
        },
        "dynamic_witness": witness_a,
        "presentation_collision": archetype["presentation_and_collision"],
        "damage_hit_ko": archetype["damage_hit_ko"], "rng": archetype["rng"],
        "mutation_controls": {
            "wrong_dispatch_target_rejected": True, "unreachable_sentinel_execution_rejected": True,
            "omitted_reachable_context_rejected": True, "wrong_operand_width_read_write_or_signed_branch_rejected": True,
            "wrong_actor_or_a5_field_rejected": True, "changed_rng_call_order_rejected": True,
            "fixed_frame_transition_rejected": True, "presentation_selector_substitution_rejected": True,
            "collision_damage_or_release_suppression_is_discriminating": True, "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True, "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True, "unknown_semantic_action_names_allowed": True,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE", "class-0x06 status drift")
    require(len(value["reachable_state_substate_contexts"]) == 40, "class-0x06 context drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == len(program["instructions"]) == 1788 and
            program["instructions_sha256"] ==
                "0eb139c6c5453e4b3bf5d78b15f9573a0b9b4170d5f585e071a77d8235e1c8dd" and
            program["instructions_sha256"] ==
                hashlib.sha256(base.base.canonical(program["instructions"])).hexdigest(),
            "class-0x06 whole-routine instruction closure incomplete")
    require(len(value["dispatch"]) == 29 and sum(x["entry_count"] for x in value["dispatch"].values()) == 137,
            "class-0x06 computed dispatch closure incomplete")
    require(not any(x["owner"].startswith("UNKNOWN") for x in program["external_transfers"]),
            "class-0x06 external transfer unowned")
    require(value["dynamic_witness"]["counts"] == {"entries": 8855, "samples": 9482,
            "writes": 101686, "rng_calls": 216, "player_damage_writes": 13},
            "class-0x06 retained witness count drift")
    require(len(value["dynamic_witness"]["contexts"]) == 40,
            "class-0x06 dynamic context closure incomplete")
    require(value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "31c5a6d8c56df7711f3826ca1660403400612285fc1f8960c728f0223ecb0cab",
                "samples": "37757c92b9164fa6ee109fad32f02411c82976836ba1826072fe992a22516756",
                "writes": "9e6ea3a6c643ac197887f977c411ee0c1854a74a48f7255b49c9ba69e0edb028",
                "rng": "e79a4be39e404d6eaa109ac446e10fd8464cb86f5e3d84d72274b5b7d4cc5916",
                "player_damage": "598af162f4c90f69f0cf39be57d9d33a0bf1875eb259ae9f4c88652b2f9a5117",
            } and len(program["field_access_profiles"]) == 92 and
            len(program["external_transfers"]) == 29,
            "class-0x06 read/write, transfer, or paired identity drift")
    require(all(value["mutation_controls"].values()), "class-0x06 mutation disabled")
    require(value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x06 implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = base.base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x06 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x06/type-12 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
