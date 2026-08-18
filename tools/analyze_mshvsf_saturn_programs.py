#!/usr/bin/env python3
"""Derive a copyright-safe static inventory from private Saturn program members."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ADDRESS_RANGES = (
    ("high_work_ram_candidates", 0x06000000, 0x06100000),
    ("cartridge_dram_candidates", 0x22400000, 0x22800000),
    ("scsp_space_candidates", 0x25A00000, 0x25B00000),
    ("vdp1_space_candidates", 0x25C00000, 0x25D00000),
    ("vdp2_space_candidates", 0x25E00000, 0x25F00000),
)

CANONICAL_CONSTANTS = {
    0x22400000: "cartridge_dram_bank_0_base_candidate",
    0x22600000: "cartridge_dram_bank_1_base_candidate",
    0x25A00000: "scsp_space_base_candidate",
    0x25C00000: "vdp1_vram_base_candidate",
    0x25C80000: "vdp1_framebuffer_base_candidate",
    0x25E00000: "vdp2_vram_base_candidate",
    0x25E20000: "vdp2_vram_offset_0x20000_candidate",
    0x25E40000: "vdp2_vram_offset_0x40000_candidate",
    0x25E60000: "vdp2_vram_offset_0x60000_candidate",
}

FILENAME_PATTERN = re.compile(
    rb"(?i)[a-z0-9_]{1,24}\.(?:bin|pac|st2|adp)"
)
PRINTABLE_PATTERN = re.compile(rb"[ -~]{4,96}")

CANDIDATE_ROLES = {
    "00LOAD.BIN": "boot_or_load_orchestrator_candidate",
    "CPK.BIN": "saturn_platform_support_runtime_candidate",
    "CR.BIN": "data_or_resource_member_candidate",
    "MM.BIN": "game_content_index_or_loader_candidate",
    "MVSOPEN.BIN": "opening_mode_runtime_candidate",
    "SYS.BIN": "system_and_mode_loader_candidate",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def marker_offsets(data: bytes, marker: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = data.find(marker, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def unique_strings(data: bytes, pattern: re.Pattern[bytes]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for match in pattern.finditer(data):
        value = match.group().decode("ascii")
        key = value.lower()
        if key not in seen:
            seen.add(key)
            values.append(value)
    return values


def diagnostic_strings(data: bytes) -> list[str]:
    values = unique_strings(data, PRINTABLE_PATTERN)
    return [
        value
        for value in values
        if any(token in value.upper() for token in ("ERROR", "RAM", "DISC", "CD"))
    ][:32]


def address_leads(data: bytes) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, low, high in ADDRESS_RANGES:
        hits: list[dict[str, str]] = []
        count = 0
        for offset in range(0, len(data) - 3, 4):
            value = int.from_bytes(data[offset : offset + 4], "big")
            if low <= value < high:
                count += 1
                if len(hits) < 16:
                    hits.append({"file_offset": f"0x{offset:08x}", "value": f"0x{value:08x}"})
        result[name] = {
            "aligned_word_count": count,
            "sample": hits,
            "interpretation": "Static aligned-word candidates only; code/data context and runtime access remain unproven.",
        }
    exact: list[dict[str, object]] = []
    for value, label in CANONICAL_CONSTANTS.items():
        needle = value.to_bytes(4, "big")
        offsets = marker_offsets(data, needle)
        if offsets:
            exact.append(
                {
                    "value": f"0x{value:08x}",
                    "candidate_label": label,
                    "offsets": [f"0x{offset:08x}" for offset in offsets],
                }
            )
    result["exact_canonical_constants"] = exact
    return result


def load_capstone(path: Path):
    sys.path.insert(0, str(path.resolve()))
    import capstone  # type: ignore

    return capstone


def disassembly_sample(capstone, data: bytes, entry_offset: int) -> list[dict[str, str]]:
    decoder = capstone.Cs(
        capstone.CS_ARCH_SH,
        capstone.CS_MODE_SH2 | capstone.CS_MODE_BIG_ENDIAN,
    )
    result: list[dict[str, str]] = []
    for instruction in decoder.disasm(data[entry_offset : entry_offset + 128], entry_offset):
        result.append(
            {
                "offset": f"0x{instruction.address:08x}",
                "mnemonic": instruction.mnemonic,
                "operands": instruction.op_str,
            }
        )
        if len(result) == 16:
            break
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(".deps/mshvsf_saturn_members"),
    )
    parser.add_argument(
        "--capstone-dir",
        type=Path,
        default=Path(".deps/capstone"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mshvsf_saturn_program_inventory.json"),
    )
    args = parser.parse_args()

    private_manifest_path = args.input_dir / "private_manifest.json"
    private_manifest = json.loads(private_manifest_path.read_text(encoding="utf-8"))
    capstone = load_capstone(args.capstone_dir)

    members: list[dict[str, object]] = []
    for manifest_member in private_manifest["members"]:
        name = str(manifest_member["path"])
        path = args.input_dir / name
        data = path.read_bytes()
        digest = sha256(data)
        if digest != manifest_member["sha256"]:
            raise RuntimeError(f"Private member hash mismatch: {name}")

        markers = marker_offsets(data, b"MBI1")
        branch_over_header = data[:4] == bytes.fromhex("a0060009")
        has_header = branch_over_header and markers and markers[0] == 4 and len(data) >= 16
        header_word_08 = int.from_bytes(data[8:12], "big") if has_header else None
        header_word_0c = int.from_bytes(data[12:16], "big") if has_header else None
        boundary_matches = bool(
            has_header
            and header_word_0c is not None
            and header_word_0c + 4 <= len(data)
            and data[header_word_0c : header_word_0c + 4] == b"MBI1"
        )
        entry_offset = 0x10 if has_header else 0

        members.append(
            {
                "path": name,
                "bytes": len(data),
                "sha256": digest,
                "candidate_role": CANDIDATE_ROLES.get(name, "unclassified_member"),
                "role_confidence": "LOW",
                "first_32_bytes_hex": data[:32].hex(" "),
                "sh2_entry_evidence": {
                    "entry_offset": f"0x{entry_offset:08x}",
                    "branch_over_mbi1_header": bool(has_header),
                    "sample": disassembly_sample(capstone, data, entry_offset),
                    "interpretation": "Valid SH-2 instructions are static executable evidence; exact load address and runtime ownership remain unresolved.",
                },
                "mbi1_structure": {
                    "marker_offsets": [f"0x{offset:08x}" for offset in markers],
                    "header_word_0x08": f"0x{header_word_08:08x}" if header_word_08 is not None else None,
                    "header_word_0x0c": f"0x{header_word_0c:08x}" if header_word_0c is not None else None,
                    "header_word_0x0c_points_to_mbi1": boundary_matches,
                    "interpretation": "The marker and boundary relationship prove structure, but the MBI1 format and field semantics remain unresolved.",
                },
                "filename_references": unique_strings(data, FILENAME_PATTERN),
                "diagnostic_strings": diagnostic_strings(data),
                "address_leads": address_leads(data),
            }
        )

    output = {
        "title": "MSHvSF Saturn static program-member inventory",
        "status": "STATIC_ADDRESS_AND_MODULE_LEADS_FOUND_DYNAMIC_OWNERSHIP_UNRESOLVED",
        "source": {
            "disc_sha256": private_manifest["source_disc_sha256"],
            "private_manifest": str(private_manifest_path).replace("\\", "/"),
            "rights_boundary": "Only hashes, names, offsets, short instruction samples, and derived metadata are tracked. Extracted members remain ignored and private.",
        },
        "method": {
            "word_endianness": "big",
            "address_scan_alignment_bytes": 4,
            "disassembler": f"Capstone {capstone.__version__} SH-2 big-endian",
            "caution": "Address-shaped words and filenames are trace leads, not proof of access, residency, allocation, or subsystem ownership.",
        },
        "members": members,
        "established_findings": [
            "00LOAD.BIN contains SH-2 code and names SYS.BIN and CPK.BIN.",
            "MM.BIN, SYS.BIN, and MVSOPEN.BIN branch over an MBI1 header at file offset 0x4.",
            "For those three files, the big-endian word at offset 0x0c points to another MBI1 marker, establishing a repeatable module/container boundary relationship.",
            "MM.BIN statically names player, background, sound, and ADP package families already present in the disc manifest.",
            "SYS.BIN statically names additional BIN members and contains an EXT RAM ERROR diagnostic string.",
            "CPK.BIN contains exact aligned constants 0x22400000 and 0x22600000 plus constants in VDP1, VDP2, and SCSP address spaces.",
        ],
        "next_dynamic_proofs": [
            "Trace CD reads to establish which member loads each file and at what phase.",
            "Dump high work RAM and both cartridge banks at semantic route anchors to establish load addresses, residency, lifetimes, and high-water marks.",
            "Trace VDP1, VDP2, SCSP, DMA, and CD-block writes to assign hardware responsibility.",
            "Record master/slave SH-2 PCs around load, combat, collision, and transition anchors.",
        ],
        "avp_application": "Use the recovered module and address leads to design AvP ownership and high-water probes. Do not copy MSHvSF addresses, package sizes, or gameplay constants into AvP.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} with {len(members)} verified private-member inventories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
