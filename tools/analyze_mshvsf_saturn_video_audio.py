#!/usr/bin/env python3
"""Analyse the reference title's VDP2 colour ownership and SCSP slot activity.

The VDP1 analysis answered how actors are drawn. This tool answers the two
questions left over: which hardware owns sprite colour, and how audio events
reach the SCSP.

Both answers are partly negative, and the negatives are the useful part:

* The VDP2 register block reads back as all zeros through the debug interface,
  so layer enables, plane maps, priorities and scroll values cannot be decoded
  from this capture at all. That is an instrument limit, recorded as such.
* Colour RAM *is* readable, and every VDP1 ``CMDCOLR`` bank measured at the four
  anchors resolves into a populated colour-RAM bank, which pins colour ownership
  to VDP2 without needing a single VDP2 register.
* Only three of thirty-two SCSP slots hold any non-zero register content, and
  their registers do not change across the whole combat window, while sound RAM
  changes by roughly 16 KiB per transition. A per-event slot key-on model does
  not fit that evidence.

Raw captures stay private. This report contains counts, offsets, hashes and
booleans, not register or memory contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: SCSP has 32 voice slots of 32 bytes each, then a common register region.
SCSP_SLOT_COUNT = 32
SCSP_SLOT_BYTES = 0x20
SCSP_COMMON_BASE = SCSP_SLOT_COUNT * SCSP_SLOT_BYTES

#: Colour RAM holds 16-colour banks of 16 two-byte entries.
CRAM_BANK_ENTRIES = 16
CRAM_ENTRY_BYTES = 2
CRAM_BANK_BYTES = CRAM_BANK_ENTRIES * CRAM_ENTRY_BYTES

PAGE_SIZE = 4096


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_offsets(before: bytes, after: bytes) -> list[int]:
    return [i for i, (a, b) in enumerate(zip(before, after)) if a != b]


def load_regions(capture_root: Path) -> list[dict[str, object]]:
    session = json.loads((capture_root / "session.json").read_text(encoding="utf-8"))
    anchors: list[dict[str, object]] = []
    for summary in session["anchors"]:
        frame = int(summary["captured_frame"])
        label = str(summary["label"])
        anchor_dir = capture_root / ("%05d_%s" % (frame, label))
        manifest = json.loads((anchor_dir / "manifest.json").read_text(encoding="utf-8"))
        regions: dict[str, bytes] = {}
        for region in manifest["regions"]:
            data = (anchor_dir / region["file"]).read_bytes()
            if len(data) != region["bytes"] or sha256(data) != region["sha256"]:
                raise RuntimeError("Raw capture failed manifest validation: %s" % anchor_dir)
            regions[region["name"]] = data
        anchors.append({"label": label, "frame": frame, "regions": regions})
    return anchors


def analyse_vdp2(anchor: dict[str, object], vdp1_banks: list[int]) -> dict[str, object]:
    regions = anchor["regions"]
    cram = regions["vdp2_cram"]
    regs = regions["vdp2_regs"]
    vram = regions["vdp2_vram"]

    populated = [
        index
        for index in range(len(cram) // CRAM_BANK_BYTES)
        if any(cram[index * CRAM_BANK_BYTES : (index + 1) * CRAM_BANK_BYTES])
    ]
    populated_set = set(populated)

    # In colour-bank mode CMDCOLR addresses a colour-RAM entry; the low bits are
    # the entry index and each 16-colour bank covers CRAM_BANK_ENTRIES of them.
    resolved = []
    for bank in vdp1_banks:
        entry = bank & 0x7FF
        cram_bank = entry // CRAM_BANK_ENTRIES
        resolved.append(
            {
                "cmdcolr": "0x%04X" % bank,
                "candidate_cram_entry": entry,
                "candidate_cram_bank": cram_bank,
                "cram_bank_is_populated": cram_bank in populated_set,
            }
        )

    return {
        "vdp2_registers_nonzero_bytes": sum(1 for byte in regs if byte),
        "vdp2_registers_readable": any(regs),
        "vdp2_vram_sha256": sha256(vram),
        "color_ram_bytes": len(cram),
        "color_ram_nonzero_bytes": sum(1 for byte in cram if byte),
        "color_ram_banks_total": len(cram) // CRAM_BANK_BYTES,
        "color_ram_banks_populated": len(populated),
        "vdp1_color_banks_referenced": len(vdp1_banks),
        "vdp1_color_bank_resolution": resolved,
        "all_referenced_banks_populated": all(
            item["cram_bank_is_populated"] for item in resolved
        ),
    }


def analyse_scsp(anchor: dict[str, object]) -> dict[str, object]:
    regs = anchor["regions"]["scsp_regs"]
    slots = []
    for index in range(SCSP_SLOT_COUNT):
        block = regs[index * SCSP_SLOT_BYTES : (index + 1) * SCSP_SLOT_BYTES]
        if any(block):
            slots.append(
                {
                    "slot": index,
                    "nonzero_bytes": sum(1 for byte in block if byte),
                    "sha256": sha256(block),
                }
            )
    common = regs[SCSP_COMMON_BASE:]
    return {
        "slots_total": SCSP_SLOT_COUNT,
        "slots_with_nonzero_registers": [item["slot"] for item in slots],
        "active_slot_count": len(slots),
        "slot_detail": slots,
        "common_region_nonzero_offsets": [
            "0x%03X" % (SCSP_COMMON_BASE + i) for i, byte in enumerate(common) if byte
        ],
        "sound_ram_sha256": sha256(anchor["regions"]["sound_ram"]),
    }


def compare(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    left = before["regions"]
    right = after["regions"]

    slot_changes = []
    for index in range(SCSP_SLOT_COUNT):
        lo = index * SCSP_SLOT_BYTES
        hi = lo + SCSP_SLOT_BYTES
        diff = len(changed_offsets(left["scsp_regs"][lo:hi], right["scsp_regs"][lo:hi]))
        if diff:
            slot_changes.append({"slot": index, "changed_bytes": diff})

    common_changed = changed_offsets(
        left["scsp_regs"][SCSP_COMMON_BASE:], right["scsp_regs"][SCSP_COMMON_BASE:]
    )
    sound_ram_changed = changed_offsets(left["sound_ram"], right["sound_ram"])
    cram_changed = changed_offsets(left["vdp2_cram"], right["vdp2_cram"])

    return {
        "from": before["label"],
        "to": after["label"],
        "frame_delta": int(after["frame"]) - int(before["frame"]),
        "scsp_slots_changed": slot_changes,
        "scsp_slot_registers_identical": not slot_changes,
        "scsp_common_changed_offsets": [
            "0x%03X" % (SCSP_COMMON_BASE + offset) for offset in common_changed
        ],
        "sound_ram_changed_bytes": len(sound_ram_changed),
        "sound_ram_changed_pages": sorted(
            {offset // PAGE_SIZE for offset in sound_ram_changed}
        ),
        "color_ram_changed_bytes": len(cram_changed),
        "color_ram_changed_banks": sorted(
            {offset // CRAM_BANK_BYTES for offset in cram_changed}
        ),
        "vdp2_vram_identical": left["vdp2_vram"] == right["vdp2_vram"],
        "vdp2_registers_identical": left["vdp2_regs"] == right["vdp2_regs"],
    }


def build_report(capture_root: Path, control_flow_path: Path) -> dict[str, object]:
    anchors = load_regions(capture_root)
    control_flow = json.loads(control_flow_path.read_text(encoding="utf-8"))
    banks_by_label = {
        item["label"]: [int(bank, 16) for bank in item["color_banks"]]
        for item in control_flow["anchors"]
    }

    anchor_reports = []
    for anchor in anchors:
        label = str(anchor["label"])
        anchor_reports.append(
            {
                "label": label,
                "captured_frame": anchor["frame"],
                "vdp2": analyse_vdp2(anchor, banks_by_label.get(label, [])),
                "scsp": analyse_scsp(anchor),
            }
        )

    transitions = [compare(a, b) for a, b in zip(anchors, anchors[1:])]

    registers_blocked = all(
        not report["vdp2"]["vdp2_registers_readable"] for report in anchor_reports
    )
    colour_join_holds = all(
        report["vdp2"]["all_referenced_banks_populated"] for report in anchor_reports
    )
    slots_static = all(item["scsp_slot_registers_identical"] for item in transitions)
    active_slots = {report["scsp"]["active_slot_count"] for report in anchor_reports}
    sound_ram_moves = all(item["sound_ram_changed_bytes"] > 0 for item in transitions)

    return {
        "title": "MSHvSF Saturn VDP2 colour ownership and SCSP slot activity",
        "purpose": "Close the VDP2 and audio gaps left by the VDP1 command analysis",
        "evidence_class": "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP",
        "method": (
            "Compare the VDP2 register block, colour RAM, VDP2 VRAM, SCSP register "
            "block and sound RAM at the four normal-hit anchors, and resolve every "
            "measured VDP1 CMDCOLR bank into a colour-RAM bank."
        ),
        "anchors": anchor_reports,
        "transitions": transitions,
        "findings": [
            {
                "id": "VDP2-1",
                "claim": (
                    "The VDP2 register block reads back as all zeros, so layer enables, "
                    "plane maps, priorities and scroll values cannot be decoded from "
                    "this capture."
                ),
                "holds": registers_blocked,
                "consequence": (
                    "VDP2 layer responsibility stays UNRESOLVED for an instrument "
                    "reason, not for lack of analysis. Resolving it needs a different "
                    "instrument, not a better parser."
                ),
                "falsification": (
                    "A capture in which any VDP2 register byte is non-zero, which would "
                    "show the register block is in fact readable."
                ),
                "evidence": "MEASURED",
            },
            {
                "id": "VDP2-2",
                "claim": (
                    "Every VDP1 sprite colour bank measured at every anchor resolves "
                    "into a populated 16-colour bank of VDP2 colour RAM."
                ),
                "holds": colour_join_holds,
                "consequence": (
                    "VDP2 owns sprite colour for the VDP1 actor path. Colour-bank mode "
                    "sprites cost colour-RAM banks, which is a VDP2 budget, not a VDP1 "
                    "texture budget."
                ),
                "falsification": (
                    "A referenced CMDCOLR bank whose colour-RAM bank is entirely zero, "
                    "which would mean the bank index is being read wrongly."
                ),
                "evidence": "MEASURED",
            },
            {
                "id": "SCSP-1",
                "claim": (
                    "Only a small fixed set of SCSP slots holds any register content, "
                    "and their registers are byte-identical across the whole window."
                ),
                "holds": slots_static and len(active_slots) == 1,
                "consequence": (
                    "Attack and impact audio are not delivered by keying a fresh SCSP "
                    "slot per game event in this window."
                ),
                "falsification": (
                    "An anchor at which a previously-zero slot becomes non-zero, or at "
                    "which any active slot's registers differ from another anchor's."
                ),
                "evidence": "MEASURED",
            },
            {
                "id": "SCSP-2",
                "claim": (
                    "Sound RAM changes on every transition while the slot registers do "
                    "not, which fits a continuously-playing buffer that a sound program "
                    "refills rather than per-event slot key-on."
                ),
                "holds": slots_static and sound_ram_moves,
                "consequence": (
                    "The audio adapter should model a mixed stream plus a small static "
                    "slot set, and treat per-event routing as a sound-program concern."
                ),
                "falsification": (
                    "A trace showing slot key-on writes between the captured anchors, "
                    "which a four-frame sample would miss; or an anchor whose sound RAM "
                    "is unchanged while audio is audibly playing."
                ),
                "evidence": "INFERRED",
            },
        ],
        "limits": [
            "Four sampled frames cannot show a register write that happens between them; only a write trace can.",
            "A static slot register set does not prove which sample is playing or which cue it represents.",
            "Colour-bank resolution assumes CMDCOLR's low bits are a colour-RAM entry index in colour-bank mode; the join succeeding is consistent with that, not a proof of the bit width.",
            "VDP2 VRAM stability during combat says nothing about load-time layer ownership.",
            "No count, slot index, bank index or page total here is a budget for any other title.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, default=ROOT / ".deps" / "mshvsf_saturn_state")
    parser.add_argument(
        "--control-flow",
        type=Path,
        default=ROOT / "data" / "mshvsf_saturn_vdp1_control_flow.json",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data" / "mshvsf_saturn_vdp2_scsp.json"
    )
    args = parser.parse_args()

    report = build_report(args.capture_root, args.control_flow)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    for finding in report["findings"]:
        print("%s holds=%s %s" % (finding["id"], finding["holds"], finding["claim"][:70]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
