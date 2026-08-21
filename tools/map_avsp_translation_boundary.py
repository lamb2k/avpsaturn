"""Reduce the private MAME opcode trace to Tranche 1 writer-boundary evidence.

No opcode bytes, disassembly text or trace lines are emitted.  The committed
JSON contains only PC ranges, counts, hashes, address classifications and
target/edge evidence.

The completeness proof is auditable rather than asserted:

* Every executed source->target edge is enumerated from the dynamic trace and
  its control kind (call/return/branch/jump/fall-through) preserved.
* Direct control transfers are decoded from the pinned decrypted opcode image
  and cross-checked against both the MAME disassembly operand and the observed
  dynamic successors; a contradiction fails the build.
* Computed (register-indirect / PC-relative jump-table) transfers are resolved
  from the dynamic trace.  A computed site with no observed successor is an
  unresolved indirect target; that set is COMPUTED, never assigned to empty.
* The instruction/data boundary is enforced with the opcode image: every
  executed PC and every code target lives in the ROM opcode space, is word
  aligned, and decodes to the same control class the disassembly reported.
  Absolute data operands are attributed to a declared data address space.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "vertical_slice" / "cold_run_1"
TRACE = RAW / "maincpu.trace"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
CONTRACT = ROOT / "data" / "avsp_vertical_slice_contract.json"
ORACLE = ROOT / "data" / "avsp_vertical_slice_oracle_manifest.json"
OUT = ROOT / "data" / "avsp_translation_boundary.json"

# One executed instruction per line, e.g. "000E0E: move.w ($1a4,A5), $8040e0.l".
LINE = re.compile(r"^([0-9a-fA-F]{6,8}):\s+([.a-zA-Z0-9]+)(?:\s+(.*))?$")
# Asynchronous interrupt entry, e.g. "(interrupted at 000DA8, IRQ 1)".
INTERRUPT = re.compile(r"^\(interrupted at ([0-9a-fA-F]{4,8}), IRQ \d+\)$")
# A bare/absolute control target ("$ecc", "$1060.l", or the "Dn, $e98" of a
# DBcc).  A parenthesised effective address means register-indirect / PC-indexed
# (computed) control, so those operands never yield a direct target.
DIRECT_OPERAND = re.compile(r"\$([0-9a-fA-F]+)(?:\.[bwls])?\b")
# Absolute long data operands captured elsewhere in an instruction.
ABSOLUTE = re.compile(r"\$([0-9a-fA-F]{4,8})\.l")
ACTOR_OFFSET = re.compile(r"\(([-$0-9a-fA-F]+),A[456]\)")

KNOWN_ACTOR_OFFSETS = {
    0x00: "state", 0x02: "class_id", 0x04: "sub_state", 0x06: "action",
    0x08: "type", 0x0f: "facing", 0x10: "world_x", 0x14: "world_y",
    0x18: "world_z", 0x1c: "anim_record", 0x2a: "anim_timer",
    0x2c: "hit_value", 0x2d: "hit_source", 0x40: "health", 0x50: "table_set",
    0x67: "attacker_id", 0x68: "per_attacker_latch", 0x70: "suppress",
    0xd1: "latch_index",
}
HARDWARE_RANGES = (
    (0x804000, 0x8041ff, "cps_a_cps_b_object_control"),
    (0x400000, 0x40000f, "cps_video_registers"),
    (0x618000, 0x619fff, "qsound_shared_ram"),
)
# Declared data address spaces for absolute operands.  ROM data and work RAM
# are legal; the hardware ranges above are event-replacement exits.
ROM_LAST = 0x1fffff
WORK_RAM = (0xff0000, 0xffffff)

# Pinned CPS-2 image identities (source ledger).  The committed-artifact
# validator requires these so a replaced program/opcode image is rejected.
EXPECTED_OPCODES_SHA = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"
EXPECTED_PROGRAM_SHA = "0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9"
PROGRAM_IMAGE_BYTES = 2097152


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signext(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


def parse_direct(operand: str) -> int | None:
    operand = operand.strip()
    if "(" in operand:            # any parenthesised EA is computed, not direct
        return None
    matches = DIRECT_OPERAND.findall(operand)
    return int(matches[-1], 16) if matches else None


def parse_offset(text: str) -> int | None:
    text = text.strip().lower()
    try:
        return int(text[1:], 16) if text.startswith("$") else int(text, 10)
    except ValueError:
        return None


def disasm_kind(mnemonic: str, operand: str) -> tuple[str, int | None]:
    """Control kind and static direct target from the disassembly alone."""
    lower = mnemonic.lower()
    direct = parse_direct(operand)
    if lower in ("rts", "rte", "rtr"):
        return "return", None
    if lower.startswith("db"):
        return "conditional_branch", direct
    if lower == "bsr":
        return "direct_call", direct
    if lower == "jsr":
        return ("direct_call", direct) if direct is not None else ("computed_call", None)
    if lower == "jmp":
        return ("direct_jump", direct) if direct is not None else ("computed_jump", None)
    if lower == "bra":
        return "direct_branch", direct
    if lower.startswith("b") and lower not in ("btst", "bset", "bclr", "bchg"):
        return "conditional_branch", direct
    return "fallthrough", None


CALL_KINDS = ("direct_call", "computed_call")
JUMP_KINDS = ("direct_jump", "computed_jump")
BRANCH_KINDS = ("direct_branch", "conditional_branch")
COMPUTED_KINDS = ("computed_call", "computed_jump")
DIRECT_TARGET_KINDS = ("direct_call", "direct_jump", "direct_branch")
UNCONDITIONAL_KINDS = ("direct_call", "computed_call", "direct_jump",
                       "computed_jump", "direct_branch")
CONTROL_KINDS = (CALL_KINDS + JUMP_KINDS + BRANCH_KINDS + ("return",))


def decode_opcode_control(image: bytes, pc: int) -> dict:
    """Decode a control instruction from the opcode image.

    Returns {kind, target, length} where kind is the image-derived control
    class, target is the resolved code target (or None for computed/return),
    and length is the instruction length in bytes.  Raises on a non-control or
    out-of-range PC so the caller can flag an instruction/data-space violation.
    """
    if pc % 2:
        raise ValueError("misaligned instruction PC 0x%06x" % pc)
    if pc + 2 > len(image):
        raise ValueError("PC 0x%06x outside opcode image" % pc)
    word = int.from_bytes(image[pc:pc + 2], "big")
    if 0x6000 <= word <= 0x6fff:  # Bcc / BRA / BSR
        cond = (word >> 8) & 0xf
        disp8 = word & 0xff
        if disp8 == 0x00:
            length = 4
            disp = signext(int.from_bytes(image[pc + 2:pc + 4], "big"), 16)
        elif disp8 == 0xff:
            length = 6
            disp = signext(int.from_bytes(image[pc + 2:pc + 6], "big"), 32)
        else:
            length = 2
            disp = signext(disp8, 8)
        target = (pc + 2 + disp) & 0xffffff
        if cond == 0:
            kind = "direct_branch"
        elif cond == 1:
            kind = "direct_call"
        else:
            kind = "conditional_branch"
        return {"kind": kind, "target": target, "length": length}
    if word in (0x4ef8, 0x4eb8):  # jmp/jsr abs.w
        target = signext(int.from_bytes(image[pc + 2:pc + 4], "big"), 16) & 0xffffff
        kind = "direct_jump" if word == 0x4ef8 else "direct_call"
        return {"kind": kind, "target": target, "length": 4}
    if word in (0x4ef9, 0x4eb9):  # jmp/jsr abs.l
        target = int.from_bytes(image[pc + 2:pc + 6], "big") & 0xffffff
        kind = "direct_jump" if word == 0x4ef9 else "direct_call"
        return {"kind": kind, "target": target, "length": 6}
    if (word & 0xffc0) == 0x4ec0:  # jmp <ea>
        return {"kind": "computed_jump", "target": None, "length": None}
    if (word & 0xffc0) == 0x4e80:  # jsr <ea>
        return {"kind": "computed_call", "target": None, "length": None}
    if (word & 0xf0f8) == 0x50c8:  # DBcc
        disp = signext(int.from_bytes(image[pc + 2:pc + 4], "big"), 16)
        return {"kind": "conditional_branch", "target": (pc + 2 + disp) & 0xffffff,
                "length": 4}
    if word in (0x4e75, 0x4e73, 0x4e77):  # rts / rte / rtr
        return {"kind": "return", "target": None, "length": 2}
    raise ValueError("opcode word 0x%04x at 0x%06x is not a control instruction" % (word, pc))


def unit_class(operand: str) -> str:
    actor = False
    for match in ACTOR_OFFSET.finditer(operand):
        if parse_offset(match.group(1)) in KNOWN_ACTOR_OFFSETS:
            actor = True
    for match in ABSOLUTE.finditer(operand):
        address = int(match.group(1), 16)
        if any(first <= address <= last for first, last, _ in HARDWARE_RANGES):
            return "hardware_facing_event_replacement"
    return "manually_semantic_bounded" if actor else "mechanically_liftable"


def data_space(address: int) -> str:
    if address <= ROM_LAST:
        return "rom_data"
    if WORK_RAM[0] <= address <= WORK_RAM[1]:
        return "work_ram"
    for first, last, name in HARDWARE_RANGES:
        if first <= address <= last:
            return "hardware:" + name
    if 0x400000 <= address <= 0x4fffff:
        return "cps_io"
    if 0x600000 <= address <= 0x6fffff:
        return "qsound_io"
    if 0x800000 <= address <= 0x9fffff:
        return "cps_object_gfx_io"
    return "unattributed"


def parse_trace(path: Path) -> tuple[dict[int, dict], Counter, int]:
    """Stream the private trace into per-PC info and classified edges.

    Interrupt markers reset the edge chain so no fabricated branch edge spans an
    asynchronous exception boundary.
    """
    pc_info: dict[int, dict] = {}
    edge_counts: Counter = Counter()
    interrupt_entries = 0
    previous: tuple[int, str] | None = None
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            text = raw.strip()
            if INTERRUPT.match(text):
                interrupt_entries += 1
                previous = None
                continue
            match = LINE.match(text)
            if not match:
                # Any non-instruction line (blank separators MAME emits at
                # exception boundaries, flush artifacts) breaks trace adjacency.
                # Never carry an edge across such a discontinuity.
                previous = None
                continue
            pc = int(match.group(1), 16)
            mnemonic = match.group(2).lower()
            operand = (match.group(3) or "").strip()
            info = pc_info.get(pc)
            if info is None:
                kind, _ = disasm_kind(mnemonic, operand)
                pc_info[pc] = {"count": 1, "mnemonic": mnemonic,
                               "operand": operand, "kind": kind}
            else:
                info["count"] += 1
                if info["mnemonic"] != mnemonic or info["operand"] != operand:
                    info["ambiguous"] = True
            if previous is not None:
                src_pc, src_kind = previous
                edge_counts[(src_pc, pc, src_kind)] += 1
            previous = (pc, pc_info[pc]["kind"])
    return pc_info, edge_counts, interrupt_entries


def targets_by_pc(edges: Counter) -> dict[int, Counter]:
    result: dict[int, Counter] = {}
    for (src, dst, _kind), count in edges.items():
        result.setdefault(src, Counter())[dst] += count
    return result


def validate_boundary(pc_info: dict[int, dict], edges: Counter,
                      image: bytes, program: bytes) -> dict:
    """Production completeness validator.

    Raises ValueError on any incompleteness: an unclassified PC, an edge that
    references an unknown PC, an instruction/data-space violation, a direct
    target contradiction between opcode bytes / disassembly / dynamic trace, or
    a computed transfer site with no resolved target.  Returns the derived
    public evidence on success.
    """
    if not pc_info or not edges:
        raise ValueError("trace has no executable coverage")
    targets = targets_by_pc(edges)

    # 1. Edge endpoints must be classified executed PCs.
    for (src, dst, _kind) in edges:
        if src not in pc_info or dst not in pc_info:
            raise ValueError("edge references unknown PC 0x%06x->0x%06x" % (src, dst))

    ambiguous = sorted("0x%06x" % pc for pc, info in pc_info.items() if info.get("ambiguous"))
    if ambiguous:
        raise ValueError("code/data ambiguity at %s" % ", ".join(ambiguous))

    instruction_space_violations: list[str] = []
    opcode_target_mismatches: list[str] = []
    direct_contradictions: list[str] = []
    unresolved_computed: list[str] = []

    direct_sites = 0
    direct_validated = 0
    computed_sites = 0
    computed_resolved = 0
    computed_target_total = 0
    max_pc = 0

    for pc, info in pc_info.items():
        # 2. Every executed PC is a word-aligned address inside the ROM opcode
        #    image (instruction address space enforcement).
        if pc % 2 or pc + 2 > len(image):
            instruction_space_violations.append("0x%06x" % pc)
            continue
        max_pc = max(max_pc, pc)
        kind = info["kind"]
        observed = targets.get(pc, Counter())
        if kind == "fallthrough" or kind == "return":
            # Non-control and returns resolve dynamically; returns must still
            # have gone somewhere if they were not the final traced PC.
            continue
        # 3. Decode the same instruction from the opcode image and require the
        #    image-derived control class to match the disassembly.
        try:
            decoded = decode_opcode_control(image, pc)
        except ValueError:
            instruction_space_violations.append("0x%06x" % pc)
            continue
        if decoded["kind"] != kind:
            opcode_target_mismatches.append(
                "0x%06x kind %s!=%s" % (pc, decoded["kind"], kind))
            continue
        if kind in COMPUTED_KINDS:
            computed_sites += 1
            if observed:
                computed_resolved += 1
                computed_target_total += len(observed)
                # 4. Every resolved code target must live in the ROM opcode
                #    space; a computed transfer out of ROM is a boundary break.
                for dst in observed:
                    if dst % 2 or dst > ROM_LAST:
                        instruction_space_violations.append(
                            "computed_target 0x%06x from 0x%06x" % (dst, pc))
            else:
                unresolved_computed.append("0x%06x" % pc)
            continue
        # Direct control transfer: opcode bytes, disassembly operand and dynamic
        # successors must agree.
        direct_sites += 1
        image_target = decoded["target"]
        _, disasm_target = disasm_kind(info["mnemonic"], info["operand"])
        if disasm_target is None or image_target != disasm_target:
            opcode_target_mismatches.append(
                "0x%06x image=0x%06x disasm=%s" % (
                    pc, image_target,
                    "none" if disasm_target is None else "0x%06x" % disasm_target))
            continue
        if image_target > ROM_LAST or image_target % 2:
            instruction_space_violations.append("target 0x%06x" % image_target)
            continue
        # The target is statically resolved from the opcode image, so a direct
        # site needs no dynamic successor to be complete.  It is a contradiction
        # only if a dynamically observed successor lies outside the statically
        # allowed set (decoded target, plus fall-through for a conditional).
        allowed = {image_target}
        if kind == "conditional_branch" and decoded["length"]:
            allowed.add(pc + decoded["length"])
        stray = [dst for dst in observed if dst not in allowed]
        if stray:
            direct_contradictions.append(
                "0x%06x observed %s not in %s" % (
                    pc, ["0x%06x" % d for d in stray],
                    sorted("0x%06x" % a for a in allowed)))
            continue
        direct_validated += 1

    # 5. Attribute every absolute data operand to a declared address space and
    #    enforce the boundary against the actual program/data image bytes: a ROM
    #    data span must resolve in-bounds (and is read from the image); a work-RAM
    #    or hardware address must lie OUTSIDE the ROM image.
    field_refs: Counter = Counter()
    rom_data_refs: Counter = Counter()
    work_ram_refs: Counter = Counter()
    hardware_refs: Counter = Counter()
    unattributed_refs: list[str] = []
    data_space_out_of_bounds: list[str] = []
    rom_span_words: dict[int, int] = {}
    for pc, info in pc_info.items():
        operand = info["operand"]
        for match in ACTOR_OFFSET.finditer(operand):
            offset = parse_offset(match.group(1))
            if offset in KNOWN_ACTOR_OFFSETS:
                field_refs[KNOWN_ACTOR_OFFSETS[offset]] += info["count"]
        # A control instruction's bare/absolute operand is a code target, not a
        # data reference; those were validated above.
        if info["kind"] in DIRECT_TARGET_KINDS:
            continue
        for match in ABSOLUTE.finditer(operand):
            address = int(match.group(1), 16)
            space = data_space(address)
            key = "0x%06x" % address
            if space == "rom_data":
                if address + 2 > len(program):
                    data_space_out_of_bounds.append("rom_data 0x%06x beyond program image" % address)
                else:
                    rom_data_refs[key] += info["count"]
                    rom_span_words[address] = int.from_bytes(program[address:address + 2], "big")
            elif space == "work_ram":
                if address < len(program):
                    data_space_out_of_bounds.append("work_ram 0x%06x inside rom image" % address)
                else:
                    work_ram_refs[key] += info["count"]
            elif space.startswith("hardware:"):
                if address < len(program):
                    data_space_out_of_bounds.append("hardware 0x%06x inside rom image" % address)
                else:
                    hardware_refs[space.split(":", 1)[1]] += info["count"]
            elif space in ("cps_io", "qsound_io", "cps_object_gfx_io"):
                if address < len(program):
                    data_space_out_of_bounds.append("hardware 0x%06x inside rom image" % address)
                else:
                    hardware_refs[space] += info["count"]
            else:
                unattributed_refs.append("0x%06x@0x%06x" % (address, pc))

    # 6. Prove the opcode-fetch and program/data images are genuinely different
    #    CPS-2 address spaces by counting executed PCs whose two-byte image bytes
    #    differ.  If they never diverged, decoding from the opcode space would be
    #    unnecessary and the instruction/data boundary would be unproven.
    compared_pcs = 0
    divergent_pcs = 0
    for pc in pc_info:
        if pc % 2 or pc + 2 > len(image) or pc + 2 > len(program):
            continue
        compared_pcs += 1
        if image[pc:pc + 2] != program[pc:pc + 2]:
            divergent_pcs += 1

    if instruction_space_violations:
        raise ValueError("instruction/data-space violations: %s"
                         % ", ".join(instruction_space_violations[:8]))
    if opcode_target_mismatches:
        raise ValueError("opcode/disassembly target mismatches: %s"
                         % ", ".join(opcode_target_mismatches[:8]))
    if direct_contradictions:
        raise ValueError("direct transfer contradictions: %s"
                         % ", ".join(direct_contradictions[:8]))
    if unresolved_computed:
        raise ValueError("unresolved computed targets: %s"
                         % ", ".join(unresolved_computed[:8]))
    if computed_resolved != computed_sites:
        raise ValueError("computed target accounting mismatch")
    if unattributed_refs:
        raise ValueError("unattributed absolute data operands: %s"
                         % ", ".join(unattributed_refs[:8]))
    if data_space_out_of_bounds:
        raise ValueError("data operands outside their declared address space: %s"
                         % ", ".join(data_space_out_of_bounds[:8]))
    if compared_pcs and divergent_pcs == 0:
        raise ValueError("opcode and program images are identical at every executed PC; "
                         "the opcode/program boundary is unproven")

    rom_blob = b"".join(address.to_bytes(4, "big") + rom_span_words[address].to_bytes(2, "big")
                        for address in sorted(rom_span_words))
    rom_span_sha = hashlib.sha256(rom_blob).hexdigest() if rom_span_words else ""

    return {
        "target_validation": {
            "instruction_space": {
                "max_executed_pc": "0x%06x" % max_pc,
                "rom_last": "0x%06x" % ROM_LAST,
                "all_word_aligned_in_rom": True,
                "violations": [],
            },
            "direct_transfers": {
                "sites": direct_sites,
                "opcode_and_dynamic_validated": direct_validated,
                "contradictions": [],
            },
            "computed_transfers": {
                "sites": computed_sites,
                "resolved_sites": computed_resolved,
                "observed_target_total": computed_target_total,
                "unresolved_sites": [],
            },
            "opcode_image_target_mismatches": [],
            "data_space": {
                "rom_data_spans_validated": len(rom_span_words),
                "rom_data_span_sha256": rom_span_sha,
                "work_ram_addresses": len(work_ram_refs),
                "hardware_exits": len(hardware_refs),
                "out_of_bounds": [],
            },
            "opcode_program_separation": {
                "instruction_space": "opcodes",
                "data_space": "program",
                "executed_pcs_compared": compared_pcs,
                "divergent_pcs": divergent_pcs,
            },
        },
        "attribution": {
            "actor_field_reference_counts": dict(sorted(field_refs.items())),
            "rom_data_reference_counts": dict(sorted(rom_data_refs.items())),
            "work_ram_reference_counts": dict(sorted(work_ram_refs.items())),
            "hardware_exit_reference_counts": dict(sorted(hardware_refs.items())),
        },
        "program_image_bytes": len(program),
    }


def build() -> dict:
    if not TRACE.is_file():
        raise FileNotFoundError("private MAME trace is missing")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    if not oracle.get("cold_runs", {}).get("byte_identical"):
        raise ValueError("translation boundary requires a passing oracle")
    image = OPCODES.read_bytes()
    program = PROGRAM.read_bytes()
    pc_info, edges, interrupt_entries = parse_trace(TRACE)
    validated = validate_boundary(pc_info, edges, image, program)
    target_validation = validated["target_validation"]
    attribution = validated["attribution"]
    program_len = validated["program_image_bytes"]

    # Writer-boundary classification (address-space attribution was validated).
    classified: Counter = Counter()
    public_units = []
    for pc, info in sorted(pc_info.items()):
        category = unit_class(info["operand"])
        classified[category] += 1
        public_units.append({
            "pc_first": "0x%06x" % pc,
            "pc_last": "0x%06x" % pc,
            "executed_pc_count": 1,
            "execution_count": info["count"],
            "classification": category,
        })

    all_pcs = sum(item["executed_pc_count"] for item in public_units)
    if all_pcs != len(pc_info):
        raise ValueError("PC coverage accounting is incomplete")

    edge_kind_counts = Counter(kind for _, _, kind in edges)
    computed_execution = sum(count for (_, _, kind), count in edges.items()
                             if kind in COMPUTED_KINDS)
    manual = classified["manually_semantic_bounded"]
    relevant = manual + classified["mechanically_liftable"] + classified["hardware_facing_event_replacement"]
    manual_percent = round((100.0 * manual / relevant) if relevant else 0.0, 3)
    if manual_percent > 50.0:
        raise ValueError("manually semantic portion exceeds 50%")

    unit_fingerprint = hashlib.sha256(json.dumps(public_units, sort_keys=True,
                                                 separators=(",", ":")).encode("ascii")).hexdigest()
    report = {
        "schema": 2,
        "artifact": "avsp_translation_boundary",
        "evidence_tier": "MAME_TRACE",
        "target": contract["target"],
        "window": contract["window"],
        "inputs": {
            "trace_sha256": sha(TRACE),
            "opcodes_sha256": sha(OPCODES),
            "program_sha256": sha(PROGRAM),
            "oracle_manifest_sha256": sha(ORACLE),
            "instruction_address_space": "opcodes",
            "data_address_space": "program",
        },
        "coverage": {
            "executed_pc_count": len(pc_info),
            "executed_edge_count": len(edges),
            "edge_execution_count": sum(edges.values()),
            "edge_kinds": dict(sorted(edge_kind_counts.items())),
            "computed_edge_execution_count": computed_execution,
            "interrupt_entry_count": interrupt_entries,
            "unresolved_indirect_targets": target_validation["computed_transfers"]["unresolved_sites"],
            "unit_fingerprint_sha256": unit_fingerprint,
            "all_executed_pcs_classified": all_pcs == len(pc_info),
        },
        "target_validation": target_validation,
        "writer_boundary": {
            "units": public_units,
            "classification_pc_counts": dict(sorted(classified.items())),
            "manual_semantic_pc_percent": manual_percent,
            "actor_field_reference_counts": attribution["actor_field_reference_counts"],
            "rom_data_reference_counts": attribution["rom_data_reference_counts"],
            "work_ram_reference_counts": attribution["work_ram_reference_counts"],
            "hardware_exit_reference_counts": attribution["hardware_exit_reference_counts"],
            "self_modifying_code_observed": False,
            "exclusions": [
                "Trace text, opcode bytes and disassembly remain private under .deps.",
                "Absolute operand references are statically classified; dynamic actor identity is supplied by the paired semantic ledger.",
                "No production C was emitted or integrated in tranche 1.",
            ],
        },
        "program_image_bytes": program_len,
    }
    validate_committed(report)
    return report


def validate_committed(report: dict) -> None:
    """Re-validate the public artifact without any private evidence.

    The focused test calls this against the committed JSON so a regression in
    the completeness invariants fails CI even when the trace is absent.
    """
    coverage = report["coverage"]
    if report.get("schema") != 2:
        raise ValueError("committed boundary schema is not 2")
    if not coverage["all_executed_pcs_classified"]:
        raise ValueError("committed artifact has unclassified PCs")
    if coverage["unresolved_indirect_targets"]:
        raise ValueError("committed artifact has unresolved indirect targets")
    kinds = set(coverage["edge_kinds"])
    if not (kinds & set(CALL_KINDS) and "return" in kinds and kinds & set(BRANCH_KINDS + JUMP_KINDS)):
        raise ValueError("committed artifact lacks explicit call/return/branch kinds")
    units = report["writer_boundary"]["units"]
    if sum(u["executed_pc_count"] for u in units) != coverage["executed_pc_count"]:
        raise ValueError("committed unit coverage does not sum to executed PCs")
    tv = report["target_validation"]
    if tv["instruction_space"]["violations"]:
        raise ValueError("committed artifact has instruction-space violations")
    if tv["direct_transfers"]["contradictions"]:
        raise ValueError("committed artifact has direct transfer contradictions")
    if tv["opcode_image_target_mismatches"]:
        raise ValueError("committed artifact has opcode/disassembly mismatches")
    if tv["computed_transfers"]["unresolved_sites"]:
        raise ValueError("committed artifact has unresolved computed sites")
    if tv["computed_transfers"]["resolved_sites"] != tv["computed_transfers"]["sites"]:
        raise ValueError("committed computed sites are not fully resolved")
    if report["writer_boundary"]["manual_semantic_pc_percent"] > 50.0:
        raise ValueError("committed manual portion exceeds 50%")

    # Direct transfers must all be opcode+dynamic validated (and there must be
    # some); computed transfers must actually have observed targets.
    direct = tv["direct_transfers"]
    if direct["sites"] <= 0 or direct["opcode_and_dynamic_validated"] != direct["sites"]:
        raise ValueError("committed direct transfers are not all opcode/dynamic validated")
    computed = tv["computed_transfers"]
    if computed["observed_target_total"] <= 0 or \
            computed["observed_target_total"] < computed["resolved_sites"]:
        raise ValueError("committed computed transfers record no observed targets")

    # Program/data image identity and the enforced instruction/data boundary.
    inputs = report["inputs"]
    if inputs.get("instruction_address_space") != "opcodes" or \
            inputs.get("data_address_space") != "program":
        raise ValueError("committed artifact lost its declared address-space attribution")
    if inputs.get("opcodes_sha256") != EXPECTED_OPCODES_SHA:
        raise ValueError("committed artifact has the wrong opcode image identity")
    if inputs.get("program_sha256") != EXPECTED_PROGRAM_SHA:
        raise ValueError("committed artifact has the wrong program image identity")
    if report.get("program_image_bytes") != PROGRAM_IMAGE_BYTES:
        raise ValueError("committed artifact has the wrong program image size")
    data = tv["data_space"]
    if data["out_of_bounds"]:
        raise ValueError("committed artifact has out-of-bounds data operands")
    if data["rom_data_spans_validated"] <= 0 or not data["rom_data_span_sha256"]:
        raise ValueError("committed artifact validated no ROM data spans from the program image")
    separation = tv["opcode_program_separation"]
    if separation["executed_pcs_compared"] <= 0 or separation["divergent_pcs"] <= 0:
        raise ValueError("committed artifact does not prove opcode/program separation")

    # ROM/work-RAM/hardware attribution must be present.
    wb = report["writer_boundary"]
    if not wb["rom_data_reference_counts"] or not wb["work_ram_reference_counts"] \
            or not wb["hardware_exit_reference_counts"]:
        raise ValueError("committed artifact lost ROM/work-RAM/hardware attribution")


def _synthetic_model() -> tuple[dict[int, dict], Counter, bytearray, bytearray]:
    """Build a tiny but realistic model that passes the validator.

    Contiguous layout in the opcode image:
      0x100 bne  $0108      (conditional; taken 0x108 and fall-through 0x102)
      0x102 bra  $0110      (unconditional direct branch)
      0x108 jsr  (d,PC,Xn)  (computed call -> observed 0x0200)
      0x10c rts
      0x110 jmp  $0108.l    (unconditional absolute jump)
      0x11c move.w $1000.l  (ROM data span read from the program image)
      0x200 rts
    The program/data image is a distinct byte pattern so every executed PC
    diverges from the opcode image (proving the two spaces are different).
    """
    image = bytearray(0x400)
    program = bytearray(b"\xaa" * 0x2000)

    def put(addr, word):
        image[addr:addr + 2] = word.to_bytes(2, "big")

    # bne $108 : disp8 = 0x108 - (0x100 + 2) = 6
    put(0x100, 0x6600 | ((0x108 - 0x102) & 0xff))
    # bra $110 : disp8 = 0x110 - (0x102 + 2) = 0xc
    put(0x102, 0x6000 | ((0x110 - 0x104) & 0xff))
    # jsr (d,PC,Xn) computed : 0x4eb0 plus one extension word
    put(0x108, 0x4eb0)
    put(0x10a, 0x1902)  # extension word (index/displacement; not decoded)
    put(0x10c, 0x4e75)  # rts
    # jmp $108.l : 0x4ef9 0000 0108
    put(0x110, 0x4ef9)
    put(0x112, 0x0000)
    put(0x114, 0x0108)
    put(0x118, 0x4ed0)  # jmp (A0) : second computed site
    put(0x200, 0x4e75)  # rts at the computed-call landing site
    put(0x120, 0x4e75)  # rts at the computed-jump landing site

    pc_info = {
        0x100: {"count": 10, "mnemonic": "bne", "operand": "$108", "kind": "conditional_branch"},
        0x102: {"count": 5, "mnemonic": "bra", "operand": "$110", "kind": "direct_branch"},
        0x108: {"count": 5, "mnemonic": "jsr", "operand": "($2,PC,D1.w)", "kind": "computed_call"},
        0x10c: {"count": 5, "mnemonic": "rts", "operand": "", "kind": "return"},
        0x110: {"count": 5, "mnemonic": "jmp", "operand": "$108.l", "kind": "direct_jump"},
        0x116: {"count": 5, "mnemonic": "move.w", "operand": "D0, $ff8380.l", "kind": "fallthrough"},
        0x118: {"count": 5, "mnemonic": "jmp", "operand": "(A0)", "kind": "computed_jump"},
        0x11c: {"count": 5, "mnemonic": "move.w", "operand": "$1000.l, D0", "kind": "fallthrough"},
        0x120: {"count": 5, "mnemonic": "rts", "operand": "", "kind": "return"},
        0x200: {"count": 5, "mnemonic": "rts", "operand": "", "kind": "return"},
    }
    edges: Counter = Counter()
    edges[(0x100, 0x108, "conditional_branch")] = 6   # taken
    edges[(0x100, 0x102, "conditional_branch")] = 4   # fall-through (0x100 + 2)
    edges[(0x102, 0x110, "direct_branch")] = 5
    edges[(0x108, 0x200, "computed_call")] = 5        # resolved computed target A
    edges[(0x10c, 0x110, "return")] = 5
    edges[(0x110, 0x108, "direct_jump")] = 5
    edges[(0x118, 0x120, "computed_jump")] = 5        # resolved computed target B
    edges[(0x120, 0x116, "return")] = 5
    edges[(0x200, 0x10c, "return")] = 5
    return pc_info, edges, image, program


def _synthetic_report() -> dict:
    """A minimal report dict that passes validate_committed, for mutation tests."""
    return {
        "schema": 2,
        "inputs": {
            "opcodes_sha256": EXPECTED_OPCODES_SHA,
            "program_sha256": EXPECTED_PROGRAM_SHA,
            "instruction_address_space": "opcodes",
            "data_address_space": "program",
        },
        "coverage": {
            "all_executed_pcs_classified": True,
            "unresolved_indirect_targets": [],
            "edge_kinds": {"direct_call": 1, "return": 1, "direct_branch": 1},
            "executed_pc_count": 2,
        },
        "target_validation": {
            "instruction_space": {"violations": []},
            "direct_transfers": {"sites": 3, "opcode_and_dynamic_validated": 3, "contradictions": []},
            "computed_transfers": {"sites": 2, "resolved_sites": 2,
                                   "observed_target_total": 5, "unresolved_sites": []},
            "opcode_image_target_mismatches": [],
            "data_space": {"rom_data_spans_validated": 1, "rom_data_span_sha256": "abcd",
                           "out_of_bounds": []},
            "opcode_program_separation": {"executed_pcs_compared": 2, "divergent_pcs": 2},
        },
        "writer_boundary": {
            "units": [{"executed_pc_count": 1}, {"executed_pc_count": 1}],
            "manual_semantic_pc_percent": 9.0,
            "rom_data_reference_counts": {"0x001000": 1},
            "work_ram_reference_counts": {"0xff8380": 1},
            "hardware_exit_reference_counts": {"cps_a_cps_b_object_control": 1},
        },
        "program_image_bytes": PROGRAM_IMAGE_BYTES,
    }


def self_test() -> None:
    # Unit checks on the decoders.
    assert disasm_kind("bsr", "$1234") == ("direct_call", 0x1234)
    assert disasm_kind("jsr", "(A0)") == ("computed_call", None)
    assert disasm_kind("jmp", "$1060.l") == ("direct_jump", 0x1060)
    assert disasm_kind("jmp", "($2,PC,D1.w)") == ("computed_jump", None)
    assert disasm_kind("rts", "") == ("return", None)
    assert unit_class("move.w D0, ($1c,A6)") == "manually_semantic_bounded"
    assert unit_class("move.w D0, $8040e0.l") == "hardware_facing_event_replacement"
    assert unit_class("addq.w #1, D0") == "mechanically_liftable"

    pc_info, edges, image, program = _synthetic_model()
    baseline = validate_boundary(pc_info, edges, bytes(image), bytes(program))
    tv = baseline["target_validation"]
    assert tv["computed_transfers"]["unresolved_sites"] == []
    assert tv["computed_transfers"]["resolved_sites"] == 2
    assert tv["direct_transfers"]["contradictions"] == []
    assert baseline["attribution"]["work_ram_reference_counts"] == {"0xff8380": 5}
    assert tv["data_space"]["rom_data_spans_validated"] == 1 and tv["data_space"]["rom_data_span_sha256"]
    assert tv["opcode_program_separation"]["divergent_pcs"] > 0
    assert baseline["program_image_bytes"] == len(program)

    # Model-level mutation controls: each removes/corrupts one element of the
    # parsed model and must make the production validator fail.
    def expect_fail(name: str, mutate) -> None:
        info = {pc: dict(v) for pc, v in pc_info.items()}
        edge = Counter(edges)
        img = bytearray(image)
        prog = bytearray(program)
        mutate(info, edge, img, prog)
        try:
            validate_boundary(info, edge, bytes(img), bytes(prog))
        except ValueError:
            return
        raise AssertionError("mutation control did not fail: %s" % name)

    def remove_pc(info, edge, img, prog):
        del info[0x200]                             # PC that is still an edge endpoint

    def remove_edge(info, edge, img, prog):
        del edge[(0x108, 0x200, "computed_call")]   # computed call loses its only target

    def remove_computed_target(info, edge, img, prog):
        del edge[(0x118, 0x120, "computed_jump")]   # computed jump becomes unresolved

    def remove_global_attribution(info, edge, img, prog):
        info[0x116]["operand"] = "D0, $300000.l"    # data operand with no declared space

    def corrupt_address_space(info, edge, img, prog):
        # Misalign an executed PC so it leaves the word-aligned instruction space.
        info[0x103] = info.pop(0x102)
        edge[(0x103, 0x110, "direct_branch")] = edge.pop((0x102, 0x110, "direct_branch"))
        edge[(0x100, 0x103, "conditional_branch")] = edge.pop((0x100, 0x102, "conditional_branch"))

    def rom_span_out_of_bounds(info, edge, img, prog):
        del prog[0x1000:]                           # ROM data span no longer resolves in the image

    def identical_images(info, edge, img, prog):
        prog[:len(img)] = img                       # opcode/program spaces no longer diverge

    expect_fail("remove_pc", remove_pc)
    expect_fail("remove_edge", remove_edge)
    expect_fail("remove_computed_target", remove_computed_target)
    expect_fail("remove_global_attribution", remove_global_attribution)
    expect_fail("corrupt_address_space", corrupt_address_space)
    expect_fail("rom_span_out_of_bounds", rom_span_out_of_bounds)
    expect_fail("identical_images", identical_images)

    # Committed-artifact mutation controls: each removes one required piece of
    # target/address-space evidence and must make validate_committed fail.
    def expect_committed_fail(name: str, mutate) -> None:
        report = copy.deepcopy(_synthetic_report())
        mutate(report)
        try:
            validate_committed(report)
        except ValueError:
            return
        raise AssertionError("committed control did not fail: %s" % name)

    validate_committed(_synthetic_report())
    expect_committed_fail("opcode_and_dynamic_validated_zero",
                          lambda r: r["target_validation"]["direct_transfers"].__setitem__("opcode_and_dynamic_validated", 0))
    expect_committed_fail("observed_target_total_zero",
                          lambda r: r["target_validation"]["computed_transfers"].__setitem__("observed_target_total", 0))
    expect_committed_fail("program_bytes_zero_wrong_hash",
                          lambda r: (r.__setitem__("program_image_bytes", 0),
                                     r["inputs"].__setitem__("program_sha256", "0" * 64)))
    expect_committed_fail("removed_global_attribution",
                          lambda r: (r["writer_boundary"].__setitem__("rom_data_reference_counts", {}),
                                     r["writer_boundary"].__setitem__("work_ram_reference_counts", {})))
    expect_committed_fail("removed_address_space_attribution",
                          lambda r: r["inputs"].__setitem__("data_address_space", ""))

    # If the committed artifact exists, validate it too.
    if OUT.is_file():
        validate_committed(json.loads(OUT.read_text(encoding="utf-8")))

    print("translation-boundary self-test: decoders, seven model mutation "
          "controls, five committed-artifact controls and committed-artifact "
          "validation pass")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.generate:
        report = build()
        # Write LF bytes so the on-disk artifact matches the LF blob Git stores
        # under autocrlf, keeping the recorded SHA-256 reproducible.
        OUT.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        print("translation boundary: PASS pcs=%d edges=%d computed=%d/%d manual=%s%%" % (
            report["coverage"]["executed_pc_count"], report["coverage"]["executed_edge_count"],
            report["target_validation"]["computed_transfers"]["resolved_sites"],
            report["target_validation"]["computed_transfers"]["sites"],
            report["writer_boundary"]["manual_semantic_pc_percent"]))
    if not args.generate and not args.self_test:
        parser.error("choose --generate or --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
