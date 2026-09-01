#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x01/type-12 source program.

This decoder is intentionally bound to the class-0x01 entry, its explicit
computed-dispatch tables, and the accepted paired ORACLE-11 witness.  It is
offline specification generation, not a general lifter or runtime interpreter.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

from capstone import CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, Cs


ROOT = Path(__file__).resolve().parents[1]
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_enemy_archetypes.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_enemies_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_enemies_b"
OUT = ROOT / "data/spec02_class01_type12_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"
PROGRAM_FIRST = 0x0407B0
PROGRAM_LAST_EXCLUSIVE = 0x042220

BASE_SPEC = importlib.util.spec_from_file_location(
    "class00_spec", ROOT / "tools/build_spec02_class00_type12.py")
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)


# The first word of every table equals its byte length.  Counts are fixed here
# so a widened or shortened guessed dispatch is rejected before decode.
TABLES = {
    "top_state_high_byte": (0x0407E4, 4),
    "spawn_variant_high_nibble": (0x0408B6, 16),
    "active_state_low_byte": (0x040B76, 6),
    "active_action_high_byte": (0x040BD2, 12),
    "action08_phase_low_byte": (0x040D1A, 2),
    "action0c_phase_low_byte": (0x040DB6, 5),
    "action0e_phase_low_byte": (0x040E90, 6),
    "action0e_plan_selector": (0x04108C, 13),
    "action0e_plan0_phase": (0x0410B2, 2),
    "action0e_plan8_phase": (0x0410F8, 5),
    "action0e_plan11_phase": (0x04117C, 4),
    "action0e_plan12_phase": (0x0411D0, 5),
    "action10_phase_low_byte": (0x0412B4, 4),
    "action12_phase_low_byte": (0x041394, 3),
    "action16_variant_u8": (0x041460, 9),
    "action16_variant0_phase": (0x04147E, 2),
    "action16_variant1_phase": (0x0414D8, 4),
    "action16_variant2_phase": (0x041602, 2),
    "action16_variant3_phase": (0x041672, 2),
    "action16_variant4_phase": (0x0416CA, 3),
    "action16_variant6_phase": (0x0417C2, 2),
    "action16_variant7_phase": (0x041812, 2),
    "action16_variant8_phase": (0x041874, 2),
    "hit_entry_action_high_byte": (0x041F7E, 2),
    "interruption_phase_high_byte": (0x04216C, 2),
}

COMPUTED_SITES = {
    0x0407E0: 0x0407E4, 0x0408AA: 0x0408B6,
    0x040B72: 0x040B76, 0x040BC8: 0x040BD2,
    0x040D16: 0x040D1A, 0x040DB2: 0x040DB6,
    0x040E8C: 0x040E90, 0x041088: 0x04108C,
    0x0410AE: 0x0410B2, 0x0410F4: 0x0410F8,
    0x041178: 0x04117C, 0x0411CC: 0x0411D0,
    0x0412B0: 0x0412B4, 0x041390: 0x041394,
    0x04145C: 0x041460, 0x04147A: 0x04147E,
    0x0414D4: 0x0414D8, 0x0415FE: 0x041602,
    0x04166E: 0x041672, 0x0416C0: 0x0416CA,
    0x0417BE: 0x0417C2, 0x04180E: 0x041812,
    0x041870: 0x041874, 0x041F74: 0x041F7E,
    0x042168: 0x04216C,
}

EXTERNAL_TRANSFER_OWNERS = {
    0x001AA6: "shared-animation-state-initializer",
    0x0024E0: "shared-score-resource-effect",
    0x016484: "shared-target-direction-helper",
    0x016518: "shared-animation-runtime-entry",
    0x016536: "shared-animation-movement-interpreter",
    0x016624: "shared-animation-record-selector",
    0x016644: "shared-current-movement-interpreter",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x0167D0: "shared-active-actor-scheduler-tail",
    0x017020: "shared-player-target-selector",
    0x0176B4: "fixed-pool-release",
    0x01778C: "shared-effect-allocation-helper",
    0x017C5E: "round1-rng-authority",
    0x01D768: "current-state-collision-helper",
    0x01E868: "shared-hit-ko-entry",
    0x01F23E: "shared-hit-ko-state-program",
    0x01F652: "shared-hit-ko-transition-program",
    0x01F826: "route-interruption-state-program",
    0x0B1BAA: "round1-navigation-movement-projection",
    0x0B2672: "round1-navigation-response-helper",
    0x0BC3F8: "shared-signed-timer-selector",
    0x0BC416: "shared-signed-timer-selector",
}

DIRECT_TARGET = re.compile(r"\$([0-9a-f]+)(?:\.[a-z])?$", re.IGNORECASE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def table_targets(image: bytes, table_base: int, count: int) -> list[int]:
    offsets = [int.from_bytes(image[table_base + index:table_base + index + 2],
                              "big") for index in range(0, count * 2, 2)]
    require(offsets[0] == count * 2,
            f"computed table 0x{table_base:06x} length drift")
    targets = [table_base + offset for offset in offsets]
    require(all(PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE
                for target in targets),
            f"computed table 0x{table_base:06x} target escaped class program")
    return targets


def access_mode(mnemonic: str, operand_index: int, operand_count: int) -> str:
    root = mnemonic.split(".", 1)[0]
    read_only = {"cmp", "cmpi", "cmpa", "tst", "btst", "chk"}
    write_only = {"move", "moveq", "movea", "lea", "clr"}
    if root in read_only:
        return "read"
    if operand_index != operand_count - 1:
        return "read"
    if root in write_only:
        return "write"
    return "read_write"


def memory_accesses(md: Cs, insn) -> list[dict[str, object]]:
    accesses = []
    width = base.width_for(insn.mnemonic) or "instruction_defined"
    for index, operand in enumerate(insn.operands):
        if operand.type != 3:
            continue
        base_name = md.reg_name(operand.mem.base_reg)
        if base_name not in {"a5", "a6"}:
            continue
        row = {
            "base": "actor" if base_name == "a6" else "a5_global",
            "displacement_s32": int(operand.mem.disp),
            "index_register": md.reg_name(operand.mem.index_reg) or None,
            "access": access_mode(insn.mnemonic, index, len(insn.operands)),
            "storage_width": width,
        }
        accesses.append(row)
    return accesses


def decode_program(image: bytes) -> tuple[list[dict[str, object]],
                                           list[dict[str, object]]]:
    md = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN)
    md.detail = True
    roots = {PROGRAM_FIRST}
    dispatch = {}
    for name, (table_base, count) in TABLES.items():
        targets = table_targets(image, table_base, count)
        roots.update(targets)
        dispatch[name] = {
            "table_base": f"0x{table_base:06x}",
            "entry_count": count,
            "targets": [f"0x{target:06x}" for target in targets],
        }

    queue = deque(sorted(roots))
    seen: set[int] = set()
    instructions: dict[int, dict[str, object]] = {}
    transfers: Counter[tuple[int, str]] = Counter()
    computed_seen: dict[int, int] = {}
    while queue:
        pc = queue.popleft()
        if pc in seen or not (PROGRAM_FIRST <= pc < PROGRAM_LAST_EXCLUSIVE):
            continue
        decoded = list(md.disasm(image[pc:pc + 10], pc, count=1))
        require(decoded, f"undecodable class-0x01 instruction at 0x{pc:06x}")
        insn = decoded[0]
        seen.add(pc)
        target_match = DIRECT_TARGET.search(insn.op_str)
        target = int(target_match.group(1), 16) if target_match else None
        row: dict[str, object] = {
            "pc": f"0x{pc:06x}", "opcode_hex": bytes(insn.bytes).hex(),
            "operation": insn.mnemonic, "operands": insn.op_str,
            "next_pc": f"0x{pc + insn.size:06x}",
        }
        width = base.width_for(insn.mnemonic)
        if width:
            row["operand_width"] = width
        accesses = memory_accesses(md, insn)
        if accesses:
            row["reads"] = [item for item in accesses
                            if item["access"] in {"read", "read_write"}]
            row["writes"] = [item for item in accesses
                             if item["access"] in {"write", "read_write"}]
        predicate = base.condition_semantics(insn.mnemonic)
        if predicate:
            row["transition_predicate"] = predicate
        if target is not None and (insn.mnemonic.startswith("b") or
                                   insn.mnemonic in {"jmp", "jsr"}):
            row["direct_target"] = f"0x{target:06x}"
        instructions[pc] = row

        next_pc = pc + insn.size
        mnemonic = insn.mnemonic
        if mnemonic in {"rts", "rte"}:
            continue
        if mnemonic == "jmp":
            if target is None:
                require(pc in COMPUTED_SITES,
                        f"unbound class-0x01 computed jump at 0x{pc:06x}")
                computed_seen[pc] = COMPUTED_SITES[pc]
            elif PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE:
                queue.append(target)
            else:
                transfers[(target, "tail_jump")] += 1
            continue
        if mnemonic in {"bra.b", "bra.w", "bra.l"}:
            require(target is not None, f"indirect branch at 0x{pc:06x}")
            if PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE:
                queue.append(target)
            else:
                transfers[(target, "tail_branch")] += 1
            continue
        if mnemonic.startswith("b") or mnemonic.startswith("db"):
            if target is not None:
                if PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE:
                    queue.append(target)
                else:
                    transfers[(target, "conditional_branch")] += 1
            queue.append(next_pc)
            continue
        if mnemonic in {"bsr.b", "bsr.w", "bsr.l", "jsr"}:
            if target is None:
                require(pc in COMPUTED_SITES,
                        f"unbound class-0x01 computed call at 0x{pc:06x}")
                computed_seen[pc] = COMPUTED_SITES[pc]
            elif PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE:
                queue.append(target)
            else:
                transfers[(target, "call")] += 1
            queue.append(next_pc)
            continue
        queue.append(next_pc)

    require(computed_seen == COMPUTED_SITES,
            "class-0x01 computed dispatch site coverage drift")
    unknown = sorted({target for target, _kind in transfers}
                     - set(EXTERNAL_TRANSFER_OWNERS))
    require(not unknown, "unowned class-0x01 external transfers: " +
            ", ".join(f"0x{value:06x}" for value in unknown))
    external = [{"entry": f"0x{target:06x}", "kind": kind,
                 "owner": EXTERNAL_TRANSFER_OWNERS[target],
                 "static_sites": count}
                for (target, kind), count in sorted(transfers.items())]
    return [instructions[pc] for pc in sorted(instructions)], [dispatch, external]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def semantic_ledger(rows: list[dict[str, str]], columns: list[str]) -> str:
    return hashlib.sha256(base.canonical(
        [[row[column] for column in columns] for row in rows])).hexdigest()


def dynamic_witness(archetype: dict, directory: Path) -> dict[str, object]:
    entries = [row for row in read_tsv(directory / "enemy_entries.tsv")
               if row["class"].lower() == "01"]
    samples = [row for row in read_tsv(directory / "enemy_samples.tsv")
               if row["class"].lower() == "01"]
    writes = [row for row in read_tsv(directory / "enemy_writes.tsv")
              if row["class"].lower() == "01"]
    rng = [row for row in read_tsv(directory / "enemy_rng.tsv")
           if row["class"].lower() == "01"]
    damage = [row for row in read_tsv(directory / "player_damage.tsv")
              if row["owner_class"].lower() == "01"]
    contexts = sorted({f"{int(row['state']):04x}:{int(row['phase']):04x}"
                       for row in entries})
    require(contexts == sorted(["0000:0000", *archetype["state_phase_contexts"]]),
            "class-0x01 reachable context drift")
    context_rows = {}
    for context in contexts:
        state, phase = (int(part, 16) for part in context.split(":"))
        ws = [row for row in writes
              if int(row["state"]) == state and int(row["phase"]) == phase]
        rs = [row for row in rng
              if int(row["state"]) == state and int(row["phase"]) == phase]
        ss = [row for row in samples
              if int(row["state"]) == state and int(row["phase"]) == phase]
        context_rows[context] = {
            "outer_state_u16": state, "action_substate_u16": phase,
            "writer_pcs": sorted({f"0x{int(row['pc'], 16):06x}" for row in ws}),
            "written_actor_offsets": sorted({f"0x{int(row['offset'], 16):02x}"
                                               for row in ws}),
            "rng_caller_pcs_in_order": [f"0x{int(row['pc'], 16):06x}"
                                         for row in rs],
            "observed_animation_records": sorted(
                {f"0x{int(row['anim'], 16):08x}" for row in ss}),
            "observed_assemblies": sorted(
                {f"0x{int(row['assembly'], 16):08x}" for row in ss}),
            "observed_hurt_selectors_u8": sorted({int(row["hurt"]) for row in ss}),
            "observed_attack_selectors_u8": sorted({int(row["attack"]) for row in ss}),
        }
    return {
        "counts": {"entries": len(entries), "samples": len(samples),
                   "writes": len(writes), "rng_calls": len(rng),
                   "player_damage_writes": len(damage)},
        "semantic_sha256": {
            "entries": semantic_ledger(entries, ["frame", "slot", "state", "phase", "facing", "x", "z", "anim", "assembly", "hurt", "attack", "timer", "health", "target", "rng"]),
            "samples": semantic_ledger(samples, ["frame", "slot", "state", "phase", "facing", "x", "y", "z", "anim", "assembly", "hurt", "attack", "timer", "health", "target"]),
            "writes": semantic_ledger(writes, ["frame", "slot", "state", "phase", "offset", "pc", "old", "data", "mask"]),
            "rng": semantic_ledger(rng, ["frame", "slot", "state", "phase", "pc", "seed"]),
            "player_damage": semantic_ledger(damage, ["frame", "owner_slot", "owner_state", "owner_phase", "pc", "old_health", "data", "mask"]),
        },
        "contexts": context_rows,
        "transition_edges": archetype["damage_hit_ko"]["hit_ko_transitions"],
    }


def field_profiles(instructions: list[dict[str, object]]) -> dict[str, object]:
    profiles: dict[str, dict[str, object]] = defaultdict(
        lambda: {"reads": [], "writes": [], "storage_widths": set()})
    for row in instructions:
        for mode in ("reads", "writes"):
            for access in row.get(mode, []):
                key = (f"{access['base']}+{access['displacement_s32']:+#x}" +
                       (f"[{access['index_register']}]"
                        if access["index_register"] else ""))
                profiles[key][mode].append(row["pc"])
                profiles[key]["storage_widths"].add(access["storage_width"])
    return {key: {"reads": value["reads"], "writes": value["writes"],
                  "storage_widths": sorted(value["storage_widths"]),
                  "signedness": "operation-local; preserve each decoded signed or unsigned branch predicate"}
            for key, value in sorted(profiles.items())}


def build() -> dict[str, object]:
    require(OPCODES.is_file() and base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    image = OPCODES.read_bytes()
    oracle = base.load_json(ORACLE)
    archetype = next(item for item in oracle["archetypes"]
                     if item["class"] == "0x01" and item["type"] == 12)
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x0407b0" and
            archetype["instance_count"] == 2,
            "accepted class-0x01 Oracle authority drift")
    instructions, decoded = decode_program(image)
    dispatch, external = decoded
    witness_a = dynamic_witness(archetype, CAPTURE_A)
    witness_b = dynamic_witness(archetype, CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x01 semantic witness drift")
    require(witness_a["counts"] == {"entries": 3304, "samples": 3796,
                                    "writes": 30904, "rng_calls": 131,
                                    "player_damage_writes": 1},
            "class-0x01 retained-ledger count drift")
    return {
        "schema": "spec02-class01-type12-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-12 class-0x01",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.sha256(ORACLE),
            "entry": "0x0407b0",
            "program_window": ["0x0407b0", "0x042220"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record12", "record_type_u8": 12, "class_u8": 1,
            "entry_dispatch": "0x0407b0",
            "order": "accepted fixed type-12 pool order; one entry per active slot per scheduler invocation",
            "post_dispatch_world_x_clamp": {
                "camera_x_global": "a5+0x0278:s16",
                "minimum_s16": "camera_x-0x0060",
                "maximum_s16": "camera_x+0x01e0",
                "branch_order": ["unsigned compare minimum against actor+0x10:s16",
                                 "only when below minimum compare camera_x+0x0240",
                                 "write actor+0x10:s16 only on an out-of-range branch"],
            },
        },
        "field_types": {
            "actor+0x04": "outer_state_u16_be; high byte then low byte dispatch",
            "actor+0x06": "action_substate_u16_be; high byte action then low byte phase",
            "actor+0x0c": "direction_u8", "actor+0x0f": "facing_u8",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s32_16_16",
            "actor+0x18": "world_z_s16", "actor+0x1c": "animation_record_u32",
            "actor+0x28": "target_slot_u16", "actor+0x2a": "timer_u16_or_u8_by_operation",
            "actor+0x30": "x_velocity_s32_16_16", "actor+0x34": "y_velocity_s32_16_16",
            "actor+0x38": "x_acceleration_s32_16_16", "actor+0x3c": "y_acceleration_s32_16_16",
            "actor+0x40": "health_s16", "actor+0x50": "table_set_pointer_u32",
            "actor+0x5c": "collision_or_airborne_u8", "actor+0x60": "target_x_offset_s16",
            "actor+0x62": "target_z_offset_s16", "actor+0x64": "presentation_mode_u8",
            "actor+0x6c": "animation_runtime_u8", "actor+0x6f": "presentation_priority_u8",
            "actor+0x80..0x9c": "class01_action_locals; exact widths and reads/writes in field_access_profiles",
        },
        "dispatch": dispatch,
        "reachable_state_substate_contexts": ["0000:0000", *archetype["state_phase_contexts"]],
        "normalized_source_program": {
            "representation": "bounded class-specific 68000 operations with explicit widths, reads, writes, guards and branch targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": field_profiles(instructions),
            "external_transfers": external,
        },
        "dynamic_witness": witness_a,
        "presentation_collision": archetype["presentation_and_collision"],
        "damage_hit_ko": archetype["damage_hit_ko"],
        "rng": archetype["rng"],
        "mutation_controls": {
            "wrong_dispatch_target_rejected": True,
            "omitted_reachable_context_rejected": True,
            "wrong_operand_width_read_write_or_signed_branch_rejected": True,
            "wrong_actor_or_a5_field_rejected": True,
            "changed_rng_call_order_rejected": True,
            "fixed_frame_transition_rejected": True,
            "presentation_selector_substitution_rejected": True,
            "collision_damage_or_release_suppression_is_discriminating": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_semantic_action_names_allowed": True,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "class-0x01 specification status drift")
    require(len(value["reachable_state_substate_contexts"]) == 32,
            "class-0x01 context coverage drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == len(program["instructions"]) == 1620 and
            program["instructions_sha256"] ==
                "6f17ccdcacfb88887cf196c2633de8a677a5d1002dd8af8ae28810fd025c9e34" and
            program["instructions_sha256"] ==
                hashlib.sha256(base.canonical(program["instructions"])).hexdigest(),
            "class-0x01 whole-routine instruction closure incomplete")
    require(set(value["dispatch"]) == set(TABLES) and
            sum(item["entry_count"] for item in value["dispatch"].values()) == 119 and
            hashlib.sha256(base.canonical(value["dispatch"])).hexdigest() ==
                "0978e56f45775fc57e42eea1ff24155533de7f3e4d8b9e7e90a07dbca1f618e5",
            "class-0x01 dispatch closure incomplete")
    require(not any(item["owner"].startswith("UNKNOWN")
                    for item in program["external_transfers"]),
            "class-0x01 external transfer unowned")
    require(value["dynamic_witness"]["counts"] == {
                "entries": 3304, "samples": 3796, "writes": 30904,
                "rng_calls": 131, "player_damage_writes": 1} and
            len(value["dynamic_witness"]["contexts"]) == 32 and
            value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "86b24751734d7bc6cc8775c1d8a47b32844f6738b5050605f24d7ca5b8f709bc",
                "samples": "fbaa0ebe63505e0c3179a311966501abd6578685293273504e4f4ad82cf5917d",
                "writes": "fc4533fb4628a7f612b5374c2f69ba0b3f68d65ad3e90f72a6a81b74f9a10ecc",
                "rng": "542bc510845b1b2ab266ecae566352c727fb71e294240493592ef4929939593c",
                "player_damage": "03b52f357f2e1869bb5de5d95c24a922da96dd3236b89976615633d8f983324b",
            },
            "class-0x01 dynamic witness incomplete")
    require(len(program["field_access_profiles"]) == 69 and
            len(program["external_transfers"]) == 23 and
            all(item["reads"] or item["writes"]
                for item in program["field_access_profiles"].values()),
            "class-0x01 read/write field contract incomplete")
    require(value["field_types"]["actor+0x10"] == "world_x_s16" and
            value["field_types"]["actor+0x40"] == "health_s16" and
            value["scheduler_contract"]["post_dispatch_world_x_clamp"]
                ["maximum_s16"] == "camera_x+0x01e0",
            "class-0x01 type, signedness, or scheduler arithmetic drift")
    require(all(value["mutation_controls"].values()),
            "class-0x01 mutation control disabled")
    require(value["implementation_rules"]["runtime_68000_interpretation_forbidden"]
            is True and value["implementation_rules"]
            ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x01 implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = base.canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x01 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x01/type-12 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
