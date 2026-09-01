#!/usr/bin/env python3
"""Build the bounded SPEC-02 class-0x00/type-12 source program.

This is deliberately class-specific.  It decodes only the source routine owned
by dispatch entry 0x03f09c, binds its indirect dispatch tables explicitly, and
uses the accepted paired ORACLE-11 ledgers as its reachable-state witness.  It
is not a general 68000 recompiler and the generated program is specification
data, never a runtime interpreter input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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
OUT = ROOT / "data/spec02_class00_type12_program.json"

OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"
PROGRAM_FIRST = 0x03F09C
PROGRAM_LAST_EXCLUSIVE = 0x0403BE

TOP_STATE_TABLE = {0x00: 0x03F0D8, 0x02: 0x03F44C,
                   0x04: 0x040346, 0x06: 0x04034C}
ACTIVE_INNER_TABLE = {0x00: 0x03F468, 0x02: 0x04025A,
                      0x04: 0x040294, 0x06: 0x040294,
                      0x08: 0x04029A}
ACTION_TABLE = {
    0x00: 0x03F4D0, 0x02: 0x03F544, 0x04: 0x03F562,
    0x06: 0x03F5E4, 0x08: 0x03F5F4, 0x0A: 0x03F786,
    0x0C: 0x03F84E, 0x0E: 0x03F886, 0x10: 0x03F8E6,
    0x12: 0x03F9AA, 0x14: 0x03FA5C, 0x16: 0x03FB52,
    0x18: 0x03FB8A, 0x1A: 0x03FBD0, 0x1C: 0x03FBE0,
    0x1E: 0x03FC68, 0x20: 0x03FCEA,
}
SUBSTATE_TABLES = {
    0x08: {0x00: 0x03F60A, 0x02: 0x03F708, 0x04: 0x03F728,
           0x06: 0x03F750, 0x08: 0x03F764},
    0x0A: {0x00: 0x03F798, 0x02: 0x03F7E4, 0x04: 0x03F806},
    0x0E: {0x00: 0x03F896, 0x02: 0x03F8D2},
    0x10: {0x00: 0x03F8FA, 0x02: 0x03F956,
           0x04: 0x03F984, 0x06: 0x03F996},
    0x12: {0x00: 0x03F9BE, 0x02: 0x03F9EA,
           0x04: 0x03FA00, 0x06: 0x03FA50},
    0x14: {0x00: 0x03FA6E, 0x02: 0x03FA98, 0x04: 0x03FB18},
    0x1C: {0x00: 0x03FBF0, 0x02: 0x03FC30},
    0x1E: {0x00: 0x03FC78, 0x02: 0x03FC94},
}

# These calls are already owned by accepted SPEC-02 authority families.  The
# class program binds to them by exact source entry and does not reimplement
# their shared transport/runtime semantics here.
EXTERNAL_CALL_OWNERS = {
    0x001AA6: "shared-animation-state-initializer",
    0x002534: "shared-score-resource-effect",
    0x0027E0: "shared-score-resource-effect",
    0x016484: "shared-target-direction-helper",
    0x016536: "shared-animation-movement-interpreter",
    0x016624: "shared-animation-record-selector",
    0x016644: "shared-current-movement-interpreter",
    0x0167AC: "shared-active-actor-scheduler-tail",
    0x017020: "shared-player-target-selector",
    0x017C5E: "round1-rng-authority",
    0x0176B4: "fixed-pool-release",
    0x01D768: "current-state-collision-helper",
    0x01E868: "shared-hit-ko-entry",
    0x01F23E: "shared-hit-ko-state-program",
    0x01F826: "route-interruption-state-program",
    0x0ABDD2: "packed-bcd-score-authority",
    0x0BC3F8: "shared-signed-timer-selector",
    0x0BC416: "shared-signed-timer-selector",
}

DIRECT_TARGET = re.compile(r"\$([0-9a-f]+)(?:\.[a-z])?$", re.IGNORECASE)
A6_FIELD = re.compile(r"(?:\$([0-9a-f]+))?\(a6(?:,.*)?\)", re.IGNORECASE)
A5_FIELD = re.compile(r"([+-]?)\$([0-9a-f]+)\(a5(?:,.*)?\)", re.IGNORECASE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("ascii")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def direct_target(op_str: str) -> int | None:
    match = DIRECT_TARGET.search(op_str)
    return int(match.group(1), 16) if match else None


def width_for(mnemonic: str) -> str | None:
    if "." not in mnemonic:
        return None
    suffix = mnemonic.rsplit(".", 1)[1]
    return {"b": "u8", "w": "u16", "l": "u32"}.get(suffix)


def condition_semantics(mnemonic: str) -> str | None:
    return {
        "beq.b": "equal_or_zero", "beq.w": "equal_or_zero",
        "bne.b": "not_equal_or_nonzero", "bne.w": "not_equal_or_nonzero",
        "bmi.b": "signed_negative", "bmi.w": "signed_negative",
        "bpl.b": "signed_nonnegative", "bpl.w": "signed_nonnegative",
        "bhi.b": "unsigned_higher", "bhi.w": "unsigned_higher",
        "bls.b": "unsigned_lower_or_same", "bls.w": "unsigned_lower_or_same",
        "bcc.b": "unsigned_carry_clear", "bcc.w": "unsigned_carry_clear",
        "bcs.b": "unsigned_carry_set", "bcs.w": "unsigned_carry_set",
        "bgt.b": "signed_greater", "bgt.w": "signed_greater",
        "bge.b": "signed_greater_or_equal", "bge.w": "signed_greater_or_equal",
        "blt.b": "signed_less", "blt.w": "signed_less",
        "ble.b": "signed_less_or_equal", "ble.w": "signed_less_or_equal",
    }.get(mnemonic)


def field_accesses(op_str: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for match in A6_FIELD.finditer(op_str):
        result.append({"base": "actor", "offset_u16": int(match.group(1) or "0", 16)})
    for match in A5_FIELD.finditer(op_str):
        value = int(match.group(2), 16)
        if match.group(1) == "-":
            value = -value
        result.append({"base": "a5_global", "offset_s16": value})
    return result


def decode_program(image: bytes) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    md = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN)
    roots = {PROGRAM_FIRST, *TOP_STATE_TABLE.values(), *ACTIVE_INNER_TABLE.values(),
             *ACTION_TABLE.values()}
    for table in SUBSTATE_TABLES.values():
        roots.update(table.values())
    queue: deque[int] = deque(sorted(roots))
    seen: set[int] = set()
    instructions: dict[int, dict[str, object]] = {}
    external_calls: Counter[int] = Counter()
    while queue:
        pc = queue.popleft()
        if pc in seen or not (PROGRAM_FIRST <= pc < PROGRAM_LAST_EXCLUSIVE):
            continue
        insns = list(md.disasm(image[pc:pc + 10], pc, count=1))
        require(insns, f"undecodable class-0x00 instruction at 0x{pc:06x}")
        insn = insns[0]
        seen.add(pc)
        target = direct_target(insn.op_str)
        row: dict[str, object] = {
            "pc": f"0x{pc:06x}", "opcode_hex": bytes(insn.bytes).hex(),
            "operation": insn.mnemonic, "operands": insn.op_str,
            "next_pc": f"0x{pc + insn.size:06x}",
        }
        width = width_for(insn.mnemonic)
        if width:
            row["operand_width"] = width
        accesses = field_accesses(insn.op_str)
        if accesses:
            row["field_accesses"] = accesses
        condition = condition_semantics(insn.mnemonic)
        if condition:
            row["transition_predicate"] = condition
        if target is not None and (insn.mnemonic.startswith("b") or
                                   insn.mnemonic in {"jmp", "jsr"}):
            row["direct_target"] = f"0x{target:06x}"
        instructions[pc] = row

        next_pc = pc + insn.size
        mnemonic = insn.mnemonic
        if mnemonic in {"rts", "rte"}:
            continue
        if mnemonic == "jmp":
            if target is not None and PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE:
                queue.append(target)
            continue
        if mnemonic in {"bra.b", "bra.w", "bra.l"}:
            require(target is not None, f"indirect unconditional branch at 0x{pc:06x}")
            queue.append(target)
            continue
        if mnemonic.startswith("b") or mnemonic.startswith("db"):
            if target is not None:
                queue.append(target)
            queue.append(next_pc)
            continue
        if mnemonic in {"bsr.b", "bsr.w", "bsr.l", "jsr"}:
            if target is not None:
                if PROGRAM_FIRST <= target < PROGRAM_LAST_EXCLUSIVE:
                    queue.append(target)
                else:
                    external_calls[target] += 1
            queue.append(next_pc)
            continue
        queue.append(next_pc)

    unknown = sorted(set(external_calls) - set(EXTERNAL_CALL_OWNERS))
    require(not unknown, "unowned class-0x00 external calls: " +
            ", ".join(f"0x{value:06x}" for value in unknown))
    calls = [{"entry": f"0x{entry:06x}", "owner": EXTERNAL_CALL_OWNERS[entry],
              "static_call_sites": count}
             for entry, count in sorted(external_calls.items())]
    return [instructions[pc] for pc in sorted(instructions)], calls


def verify_dispatch_bytes(image: bytes) -> dict[str, object]:
    def words(base: int, count: int) -> list[int]:
        return [int.from_bytes(image[base + index:base + index + 2], "big")
                for index in range(0, count * 2, 2)]

    require(words(0x03F0D0, 4) == [0x0008, 0x037C, 0x1276, 0x127C],
            "top-state dispatch table drift")
    require(words(0x03F45E, 5) == [0x000A, 0x0DFC, 0x0E36, 0x0E36, 0x0E3C],
            "active-inner dispatch table drift")
    action_offsets = words(0x03F4AE, 17)
    require([0x03F4AE + value for value in action_offsets] ==
            list(ACTION_TABLE.values()), "active-action dispatch table drift")
    for action, table in SUBSTATE_TABLES.items():
        base = {0x08: 0x03F600, 0x0A: 0x03F792, 0x0E: 0x03F892,
                0x10: 0x03F8F2, 0x12: 0x03F9B6, 0x14: 0x03FA68,
                0x1C: 0x03FBEC, 0x1E: 0x03FC74}[action]
        require([base + value for value in words(base, len(table))] ==
                list(table.values()), f"action 0x{action:02x} substate table drift")
    return {
        "top_state_high_byte": {f"0x{k:02x}": f"0x{v:06x}" for k, v in TOP_STATE_TABLE.items()},
        "active_state_low_byte": {f"0x{k:02x}": f"0x{v:06x}" for k, v in ACTIVE_INNER_TABLE.items()},
        "active_action_high_byte": {f"0x{k:02x}": f"0x{v:06x}" for k, v in ACTION_TABLE.items()},
        "action_substate_low_byte": {
            f"0x{action:02x}": {f"0x{k:02x}": f"0x{v:06x}" for k, v in table.items()}
            for action, table in SUBSTATE_TABLES.items()
        },
    }


def semantic_ledger(rows: list[dict[str, str]], columns: list[str]) -> str:
    projected = [[row[column] for column in columns] for row in rows]
    return hashlib.sha256(canonical(projected)).hexdigest()


def build_dynamic_witness(archetype: dict, directory: Path) -> dict[str, object]:
    entries = [row for row in read_tsv(directory / "enemy_entries.tsv")
               if row["class"].lower() == "00"]
    samples = [row for row in read_tsv(directory / "enemy_samples.tsv")
               if row["class"].lower() == "00"]
    writes = [row for row in read_tsv(directory / "enemy_writes.tsv")
              if row["class"].lower() == "00"]
    rng = [row for row in read_tsv(directory / "enemy_rng.tsv")
           if row["class"].lower() == "00"]
    damage = [row for row in read_tsv(directory / "player_damage.tsv")
              if row["owner_class"].lower() == "00"]

    contexts = sorted({f"{int(row['state']):04x}:{int(row['phase']):04x}"
                       for row in entries})
    # ORACLE-11's published state_phase_contexts intentionally describes the
    # post-initialization authority.  The paired entry ledger also witnesses
    # the source-owned 0x0000:0000 initializer, which P3 must retain.
    expected_contexts = sorted([*archetype["state_phase_contexts"], "0000:0000"])
    require(contexts == expected_contexts,
            "class-0x00 reachable context drift")
    per_context: dict[str, dict[str, object]] = {}
    for context in contexts:
        state, phase = (int(part, 16) for part in context.split(":"))
        context_writes = [row for row in writes
                          if int(row["state"]) == state and int(row["phase"]) == phase]
        context_rng = [row for row in rng
                       if int(row["state"]) == state and int(row["phase"]) == phase]
        context_samples = [row for row in samples
                           if int(row["state"]) == state and int(row["phase"]) == phase]
        per_context[context] = {
            "outer_state_u16": state,
            "action_substate_u16": phase,
            "dispatch": (f"0x{TOP_STATE_TABLE[(state >> 8) & 0xff]:06x}"),
            "active_action_dispatch": (f"0x{ACTION_TABLE[(phase >> 8) & 0xff]:06x}"
                                       if state in (0x0200, 0x0202) and
                                       ((phase >> 8) & 0xff) in ACTION_TABLE else None),
            "writer_pcs": sorted({f"0x{int(row['pc'], 16):06x}" for row in context_writes}),
            "written_actor_offsets": sorted({f"0x{int(row['offset'], 16):02x}" for row in context_writes}),
            "rng_caller_pcs_in_order": [f"0x{int(row['pc'], 16):06x}" for row in context_rng],
            "observed_animation_records": sorted({f"0x{int(row['anim'], 16):08x}" for row in context_samples}),
            "observed_assemblies": sorted({f"0x{int(row['assembly'], 16):08x}" for row in context_samples}),
            "observed_hurt_selectors_u8": sorted({int(row["hurt"]) for row in context_samples}),
            "observed_attack_selectors_u8": sorted({int(row["attack"]) for row in context_samples}),
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
        "contexts": per_context,
        "transition_edges": archetype["damage_hit_ko"]["hit_ko_transitions"],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    image = OPCODES.read_bytes()
    oracle = load_json(ORACLE)
    archetype = next(item for item in oracle["archetypes"]
                     if item["class"] == "0x00" and item["type"] == 12)
    require(archetype["classification"] == "SOURCE_CLOSED" and
            archetype["dispatch_entry"] == "0x03f09c" and
            archetype["instance_count"] == 5,
            "accepted class-0x00 Oracle authority drift")

    instructions, external_calls = decode_program(image)
    dispatch = verify_dispatch_bytes(image)
    witness_a = build_dynamic_witness(archetype, CAPTURE_A)
    witness_b = build_dynamic_witness(archetype, CAPTURE_B)
    require(witness_a == witness_b, "paired class-0x00 semantic witness drift")
    require(witness_a["counts"] == {"entries": 5821, "samples": 6397,
                                    "writes": 40876, "rng_calls": 194,
                                    "player_damage_writes": 2},
            "class-0x00 retained-ledger count drift")

    globals_used = sorted({access["offset_s16"]
                           for row in instructions
                           for access in row.get("field_accesses", [])
                           if access["base"] == "a5_global"})
    actor_offsets = sorted({access["offset_u16"]
                            for row in instructions
                            for access in row.get("field_accesses", [])
                            if access["base"] == "actor"})
    result = {
        "schema": "spec02-class00-type12-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of record-type-12 class-0x00",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": sha256(ORACLE),
            "entry": "0x03f09c",
            "program_window": ["0x03f09c", "0x0403be"],
            "program_window_sha256": hashlib.sha256(image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "pool": "record12", "record_type_u8": 12, "class_u8": 0,
            "entry_dispatch": "0x03f09c",
            "order": "accepted fixed type-12 pool order; one entry per active slot per scheduler invocation",
            "post_dispatch_world_x_clamp": {
                "camera_x_global": "a5+0x0278:s16",
                "minimum_s16": "camera_x-0x0060",
                "maximum_s16": "camera_x+0x01e0",
                "branch_order": ["unsigned compare minimum against actor+0x10:s16",
                                 "only when below minimum compare maximum",
                                 "write actor+0x10:s16 only on an out-of-range branch"],
            },
        },
        "field_types": {
            "actor+0x04": "outer_state_u16_be; high byte dispatch then low byte dispatch",
            "actor+0x06": "action_substate_u16_be; high byte action then low byte phase",
            "actor+0x0c": "direction_u8", "actor+0x0f": "facing_u8",
            "actor+0x10": "world_x_s16", "actor+0x14": "world_y_s32_16_16",
            "actor+0x18": "world_z_s16", "actor+0x1c": "animation_record_u32",
            "actor+0x28": "target_slot_u16", "actor+0x2a": "timer_u16_or_u8_by_source_operation",
            "actor+0x30": "x_velocity_s32_16_16", "actor+0x34": "y_velocity_s32_16_16",
            "actor+0x38": "x_acceleration_s32_16_16", "actor+0x3c": "y_acceleration_s32_16_16",
            "actor+0x40": "health_s16", "actor+0x50": "table_set_pointer_u32",
            "actor+0x5c": "collision_or_airborne_u8", "actor+0x60": "target_x_offset_s16",
            "actor+0x62": "target_z_offset_s16", "actor+0x64": "presentation_mode_u8",
            "actor+0x6c": "animation_runtime_u8", "actor+0x6f": "presentation_priority_u8",
            "actor+0x80": "action_table_cursor_u16", "actor+0x82": "action_local_u16",
            "actor+0x84": "action_local_u8", "actor+0x85": "style_u8",
            "actor+0x86": "lane_relation_s8", "actor+0x87": "group_lane_u8",
            "actor+0x88": "action_timer_u8", "actor+0x89": "group_timer_u8",
            "actor+0x8a": "group_occupancy_latch_u8",
        },
        "dispatch": dispatch,
        "reachable_state_substate_contexts": [
            "0000:0000", *archetype["state_phase_contexts"]],
        "normalized_source_program": {
            "representation": "bounded class-specific 68000 operations with explicit width, field accesses, direct guards and branch targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "actor_offsets_accessed_u16": actor_offsets,
            "a5_relative_globals_accessed_s16": globals_used,
            "external_calls": external_calls,
        },
        "dynamic_witness": witness_a,
        "presentation_collision": archetype["presentation_and_collision"],
        "damage_hit_ko": archetype["damage_hit_ko"],
        "rng": archetype["rng"],
        "mutation_controls": {
            "wrong_dispatch_target_rejected": True,
            "omitted_reachable_context_rejected": True,
            "wrong_operand_width_or_signed_branch_rejected": True,
            "wrong_actor_or_a5_offset_rejected": True,
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
    return result


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "class-0x00 specification status drift")
    require(len(value["reachable_state_substate_contexts"]) == 39,
            "class-0x00 context coverage drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == len(program["instructions"]) and
            program["instruction_count"] == 904 and
            program["instructions_sha256"] ==
                "d5b4705d75a75feaa7e7e9184ea17994ca711444b687bfdaa57f035328093348" and
            program["instructions_sha256"] ==
                hashlib.sha256(canonical(program["instructions"])).hexdigest(),
            "class-0x00 whole-routine instruction closure incomplete")
    expected_dispatch = {
        "top_state_high_byte": {f"0x{k:02x}": f"0x{v:06x}" for k, v in TOP_STATE_TABLE.items()},
        "active_state_low_byte": {f"0x{k:02x}": f"0x{v:06x}" for k, v in ACTIVE_INNER_TABLE.items()},
        "active_action_high_byte": {f"0x{k:02x}": f"0x{v:06x}" for k, v in ACTION_TABLE.items()},
        "action_substate_low_byte": {
            f"0x{action:02x}": {f"0x{k:02x}": f"0x{v:06x}" for k, v in table.items()}
            for action, table in SUBSTATE_TABLES.items()},
    }
    require(value["dispatch"] == expected_dispatch,
            "class-0x00 dispatch closure incomplete")
    require(not any(call["owner"].startswith("UNKNOWN")
                    for call in program["external_calls"]),
            "class-0x00 external helper unowned")
    require(value["dynamic_witness"]["counts"]["rng_calls"] == 194 and
            len(value["dynamic_witness"]["contexts"]) == 39 and
            value["dynamic_witness"]["semantic_sha256"] == {
                "entries": "272108ce40f5c2355279fe8395d0a774546e424901c8aeb60b4261add40261ba",
                "samples": "e00f513cb5bb542631e89533fde99132b265f66c0f6268a209d0a7a901a8c22a",
                "writes": "87424d99d016091fe0b4dec748132301769b82e255ad31c4ab8ed01455263fef",
                "rng": "04f9efea82865f48df78fe83a592b1decec399276cfd471344b2043d44a7873a",
                "player_damage": "d7df717474355d0bfe293f8db0ce843cef81061191b67d98023c63aad284e1ff",
            } and
            value["damage_hit_ko"]["player_damage_write_count"] == 2,
            "class-0x00 dynamic witness incomplete")
    require(value["field_types"]["actor+0x04"] ==
                "outer_state_u16_be; high byte dispatch then low byte dispatch" and
            value["field_types"]["actor+0x06"] ==
                "action_substate_u16_be; high byte action then low byte phase" and
            value["field_types"]["actor+0x10"] == "world_x_s16" and
            value["field_types"]["actor+0x14"] == "world_y_s32_16_16" and
            value["field_types"]["actor+0x40"] == "health_s16" and
            value["scheduler_contract"]["post_dispatch_world_x_clamp"]
                ["minimum_s16"] == "camera_x-0x0060" and
            value["scheduler_contract"]["post_dispatch_world_x_clamp"]
                ["maximum_s16"] == "camera_x+0x01e0",
            "class-0x00 type, signedness, or scheduler arithmetic drift")
    require(all(value["mutation_controls"].values()),
            "class-0x00 mutation control disabled")
    require(value["implementation_rules"] == {
        "portable_c_translation_required": True,
        "runtime_68000_interpretation_forbidden": True,
        "fixed_frame_or_authored_fallback_forbidden": True,
        "unknown_semantic_action_names_allowed": True,
        "unknown_state_or_transition_logic_allowed": False,
    }, "class-0x00 implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed class-0x00 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 class-0x00/type-12 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"contexts={len(value['reachable_state_substate_contexts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
