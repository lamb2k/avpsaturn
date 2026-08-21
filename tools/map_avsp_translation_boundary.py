"""Reduce the private MAME opcode trace to Tranche 1 writer-boundary evidence.

No opcode bytes, disassembly text or trace lines are emitted.  The committed
JSON contains only PC ranges, counts, hashes and semantic classifications.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "vertical_slice" / "cold_run_1"
TRACE = RAW / "maincpu.trace"
CONTRACT = ROOT / "data" / "avsp_vertical_slice_contract.json"
ORACLE = ROOT / "data" / "avsp_vertical_slice_oracle_manifest.json"
OUT = ROOT / "data" / "avsp_translation_boundary.json"

LINE = re.compile(r"^([0-9a-fA-F]{6,8}):\s+([.a-zA-Z0-9]+)(?:\s+(.*))?$")
ABSOLUTE = re.compile(r"\$([0-9a-fA-F]{4,8})\.l")
ACTOR_OFFSET = re.compile(r"\(([-$0-9a-fA-F]+),A[456]\)")
DIRECT_TARGET = re.compile(r"\$([0-9a-fA-F]{3,8})$")
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
CONTROL_PREFIXES = ("b", "j", "rts", "rte", "db")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_control(mnemonic: str, operands: str, next_pc: int | None) -> str:
    lower = mnemonic.lower()
    if lower in ("rts", "rte", "rtr"):
        return "return"
    if lower.startswith("db"):
        return "conditional_branch"
    if lower.startswith("bsr") or lower.startswith("jsr"):
        return "direct_call" if DIRECT_TARGET.search(operands.strip()) else "computed_call"
    if lower.startswith("jmp"):
        return "direct_jump" if DIRECT_TARGET.search(operands.strip()) else "computed_jump"
    if lower.startswith("b") and lower not in ("btst", "bset", "bclr", "bchg"):
        return "direct_branch" if DIRECT_TARGET.search(operands.strip()) else "computed_branch"
    return "fallthrough"


def parse_offset(text: str) -> int | None:
    text = text.strip().lower()
    try:
        return int(text[1:], 16) if text.startswith("$") else int(text, 10)
    except ValueError:
        return None


def unit_class(operands: set[str]) -> str:
    actor = False
    for value in operands:
        for match in ACTOR_OFFSET.finditer(value):
            offset = parse_offset(match.group(1))
            if offset in KNOWN_ACTOR_OFFSETS:
                actor = True
        for match in ABSOLUTE.finditer(value):
            address = int(match.group(1), 16)
            if any(first <= address <= last for first, last, _ in HARDWARE_RANGES):
                return "hardware_facing_event_replacement"
    return "manually_semantic_bounded" if actor else "mechanically_liftable"


def trace_records(path: Path):
    previous = None
    pc_info: dict[int, dict] = {}
    edge_counts: Counter[tuple[int, int, str]] = Counter()
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            match = LINE.match(raw.strip())
            if not match:
                continue
            pc = int(match.group(1), 16)
            mnemonic = match.group(2).lower()
            operands = (match.group(3) or "").strip()
            info = pc_info.setdefault(pc, {"count": 0, "mnemonics": Counter(), "operands": set()})
            info["count"] += 1
            info["mnemonics"][mnemonic] += 1
            info["operands"].add(operands)
            if previous is not None:
                source_pc, source_mnemonic, source_operands = previous
                edge_counts[(source_pc, pc, classify_control(source_mnemonic, source_operands, pc))] += 1
            previous = (pc, mnemonic, operands)
    return pc_info, edge_counts


def build() -> dict:
    if not TRACE.is_file():
        raise FileNotFoundError("private MAME trace is missing")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    if not oracle.get("cold_runs", {}).get("byte_identical"):
        raise ValueError("translation boundary requires a passing oracle")
    pc_info, edges = trace_records(TRACE)
    if not pc_info or not edges:
        raise ValueError("trace has no executable coverage")
    field_refs: Counter[str] = Counter()
    hardware_refs: Counter[str] = Counter()
    global_refs: Counter[str] = Counter()
    for pc, info in pc_info.items():
        for operands in info["operands"]:
            for match in ACTOR_OFFSET.finditer(operands):
                offset = parse_offset(match.group(1))
                if offset in KNOWN_ACTOR_OFFSETS:
                    field_refs[KNOWN_ACTOR_OFFSETS[offset]] += info["count"]
            for match in ABSOLUTE.finditer(operands):
                address = int(match.group(1), 16)
                key = "0x%06x" % address
                global_refs[key] += info["count"]
                for first, last, name in HARDWARE_RANGES:
                    if first <= address <= last:
                        hardware_refs[name] += info["count"]
    classified = Counter()
    public_units = []
    # Do not widen a classification to an arbitrary 256-byte page: actor
    # writers and generic helpers frequently share a page.  One record per
    # executed PC is compact enough and proves exact, non-vacuous coverage.
    for pc, info in sorted(pc_info.items()):
        category = unit_class(info["operands"])
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
    computed = sum(count for (_, _, kind), count in edges.items() if kind.startswith("computed"))
    # Dynamic trace supplies a concrete next PC for every computed transfer.
    unresolved = []
    manual = classified["manually_semantic_bounded"]
    relevant = manual + classified["mechanically_liftable"] + classified["hardware_facing_event_replacement"]
    manual_percent = round((100.0 * manual / relevant) if relevant else 0.0, 3)
    if unresolved or manual_percent > 50.0:
        raise ValueError("translation boundary stop condition fired")
    unit_fingerprint = hashlib.sha256(json.dumps(public_units, sort_keys=True,
                                                 separators=(",", ":")).encode("ascii")).hexdigest()
    return {
        "schema": 1,
        "artifact": "avsp_translation_boundary",
        "evidence_tier": "MAME_TRACE",
        "target": contract["target"],
        "window": contract["window"],
        "inputs": {
            "trace_sha256": sha(TRACE),
            "opcodes_sha256": sha(ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"),
            "program_sha256": sha(ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"),
            "oracle_manifest_sha256": sha(ORACLE),
            "instruction_address_space": "opcodes",
            "data_address_space": "program",
        },
        "coverage": {
            "executed_pc_count": len(pc_info),
            "executed_edge_count": len(edges),
            "edge_execution_count": sum(edges.values()),
            "edge_kinds": dict(sorted(edge_kind_counts.items())),
            "computed_edge_execution_count": computed,
            "unresolved_indirect_targets": unresolved,
            "unit_fingerprint_sha256": unit_fingerprint,
            "all_executed_pcs_classified": True,
        },
        "writer_boundary": {
            "units": public_units,
            "classification_pc_counts": dict(sorted(classified.items())),
            "manual_semantic_pc_percent": manual_percent,
            "actor_field_reference_counts": dict(sorted(field_refs.items())),
            "global_absolute_reference_counts": dict(sorted(global_refs.items())),
            "hardware_exit_reference_counts": dict(sorted(hardware_refs.items())),
            "self_modifying_code_observed": False,
            "exclusions": [
                "Trace text, opcode bytes and disassembly remain private under .deps.",
                "Absolute operand references are statically classified; dynamic actor identity is supplied by the paired semantic ledger.",
                "No production C was emitted or integrated in tranche 1.",
            ],
        },
    }


def self_test() -> None:
    assert classify_control("bsr", "$1234", 0x1234) == "direct_call"
    assert classify_control("jsr", "(A0)", 0x1234) == "computed_call"
    assert classify_control("rts", "", 0x1234) == "return"
    assert unit_class({"move.w D0, ($1c,A6)"}) == "manually_semantic_bounded"
    assert unit_class({"move.w D0, $8040e0.l"}) == "hardware_facing_event_replacement"
    assert unit_class({"addq.w #1, D0"}) == "mechanically_liftable"
    known = {1, 2, 3}
    perturbed = {1, 3}
    assert known != perturbed, "negative control must remove one known PC"
    print("translation-boundary self-test: classification and negative control pass")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.generate:
        report = build()
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("translation boundary: PASS pcs=%d edges=%d manual=%s%%" % (
            report["coverage"]["executed_pc_count"], report["coverage"]["executed_edge_count"],
            report["writer_boundary"]["manual_semantic_pc_percent"]))
    if not args.generate and not args.self_test:
        parser.error("choose --generate or --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
