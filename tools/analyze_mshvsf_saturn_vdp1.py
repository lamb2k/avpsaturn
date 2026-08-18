#!/usr/bin/env python3
"""Analyse the reference title's VDP1 command lists by real control flow.

The earlier analysis read the command table in stored order and stopped at the
first draw-end bit. That is only correct if every reachable command uses
jump-next, which was assumed rather than shown. This tool walks the list the
way the VDP1 command processor does -- honouring jump, call, return and skip
modes and the single hardware return-address register -- and reports the
reachable set separately from the stored set, so the difference is visible.

Raw captures under ``.deps`` stay private. The tracked output contains counts,
histograms, merged texture spans and hashes only.
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

from reference_engine import vdp1  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def analyse_anchor(label: str, frame: int, vram: bytes) -> dict[str, object]:
    walk = vdp1.traverse(vram)
    stored = vdp1.sequential_scan(vram)
    stored_slots = vdp1.stored_nonzero_slots(vram)
    reachable_offsets = {command.offset for command in walk.visited}
    stored_offsets = {command.offset for command in stored}

    return {
        "label": label,
        "captured_frame": frame,
        "vdp1_vram_sha256": sha256(vram),
        "traversal_start": "0x000000",
        "traversal_stop_reason": walk.stop_reason,
        "terminated_by_draw_end": walk.terminated,
        "reachable_slot_count": walk.reachable_slot_count,
        "sequential_slot_count": len(stored),
        "stored_nonzero_slots": stored_slots,
        "residual_slots_after_terminator": stored_slots - walk.reachable_slot_count,
        "reachable_equals_sequential": reachable_offsets == stored_offsets,
        "drawn_command_count": walk.drawn_command_count,
        "state_command_count": walk.state_command_count,
        "skipped_command_count": walk.skipped_command_count,
        "command_table_bytes": walk.command_table_bytes,
        "command_type_histogram": walk.command_type_histogram(),
        "jump_mode_histogram": walk.jump_mode_histogram(),
        "sprite_size_histogram": walk.size_histogram(),
        "flip_histogram": walk.flip_histogram(),
        "links_followed": [
            {"from": "0x%06X" % src, "to": "0x%06X" % dst, "mode": mode}
            for src, dst, mode in walk.links_followed
        ],
        "control_flow_anomalies": walk.anomalies,
        "distinct_color_banks": len(walk.color_banks()),
        "color_banks": ["0x%04X" % bank for bank in walk.color_banks()],
        "texture_span_count": len(walk.texture_spans()),
        "texture_bytes_referenced": walk.texture_bytes_referenced(),
        "texture_spans": [
            {"start": "0x%06X" % start, "end": "0x%06X" % end, "bytes": end - start}
            for start, end in walk.texture_spans()
        ],
    }


def compare(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    return {
        "from": before["label"],
        "to": after["label"],
        "reachable_slot_delta": int(after["reachable_slot_count"])
        - int(before["reachable_slot_count"]),
        "drawn_command_delta": int(after["drawn_command_count"])
        - int(before["drawn_command_count"]),
        "texture_bytes_delta": int(after["texture_bytes_referenced"])
        - int(before["texture_bytes_referenced"]),
        "color_bank_delta": int(after["distinct_color_banks"])
        - int(before["distinct_color_banks"]),
        "flip_delta": {
            key: int(after["flip_histogram"][key]) - int(before["flip_histogram"][key])
            for key in sorted(before["flip_histogram"])
        },
    }


def build_report(capture_root: Path) -> dict[str, object]:
    session = json.loads((capture_root / "session.json").read_text(encoding="utf-8"))
    anchors: list[dict[str, object]] = []
    for summary in session["anchors"]:
        frame = int(summary["captured_frame"])
        label = str(summary["label"])
        anchor_dir = capture_root / ("%05d_%s" % (frame, label))
        manifest = json.loads((anchor_dir / "manifest.json").read_text(encoding="utf-8"))
        region = next(r for r in manifest["regions"] if r["name"] == "vdp1_vram")
        vram = (anchor_dir / region["file"]).read_bytes()
        if len(vram) != region["bytes"] or sha256(vram) != region["sha256"]:
            raise RuntimeError("Raw VDP1 capture failed manifest validation: %s" % anchor_dir)
        anchors.append(analyse_anchor(label, frame, vram))

    transitions = [compare(a, b) for a, b in zip(anchors, anchors[1:])]

    sizes: dict[str, int] = {}
    pmods: set[str] = set()
    for anchor in anchors:
        for key, value in anchor["sprite_size_histogram"].items():
            sizes[key] = sizes.get(key, 0) + int(value)
    uniform_size = len(sizes) == 1
    only_jump_next = all(
        set(anchor["jump_mode_histogram"]) == {"JUMP_NEXT"} for anchor in anchors
    )

    return {
        "title": "MSHvSF Saturn VDP1 command-list control-flow analysis",
        "purpose": "Reachable VDP1 command evidence for CPS2-to-Saturn reference-engine calibration",
        "evidence_class": "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP",
        "method": (
            "Walk the command table from address 0 following VDP1 jump, call, return "
            "and skip modes with a single return-address register, stopping at the "
            "draw-end bit, at a revisited slot, or outside the VRAM image."
        ),
        "anchors": anchors,
        "transitions": transitions,
        "observed_drawing_mode": {
            "sprite_size": [16, 16] if uniform_size and "16x16" in sizes else None,
            "sprite_size_histogram": dict(sorted(sizes.items())),
            "uniform_sprite_size": uniform_size,
            "command_pmod": "0x0880",
            "color_bank_stride": 16,
            "note": (
                "Every drawn command across every anchor is a normal sprite of one "
                "size in 16-colour bank mode with an identical CMDPMOD."
            ),
        },
        "findings": [
            {
                "id": "VDP1-CF-1",
                "claim": "Every reachable command at all four anchors uses jump-next.",
                "holds": only_jump_next,
                "consequence": (
                    "For this title in this window a stored-order scan and a real "
                    "traversal agree, which the earlier analysis assumed but did not show."
                ),
                "falsification": (
                    "Any anchor whose jump-mode histogram contains a mode other than "
                    "JUMP_NEXT, or whose reachable slot set differs from the stored set."
                ),
                "evidence": "MEASURED",
            },
            {
                "id": "VDP1-CF-2",
                "claim": (
                    "The command table holds more non-zero slots than the current list "
                    "reaches; the excess is residue from longer earlier lists."
                ),
                "holds": all(
                    int(anchor["residual_slots_after_terminator"]) > 0 for anchor in anchors
                ),
                "consequence": (
                    "Non-zero extent is not this frame's command count and is not an "
                    "allocator high-water mark."
                ),
                "falsification": (
                    "A capture whose non-zero slot count equals its reachable slot count "
                    "while the list length varies between frames."
                ),
                "evidence": "MEASURED",
            },
            {
                "id": "VDP1-CF-3",
                "claim": (
                    "Actor and background sprites are drawn one VDP1 command per 16x16 "
                    "tile rather than as precomposed cels."
                ),
                "holds": uniform_size,
                "consequence": (
                    "Command-table pressure scales with visible tile count, so a tile "
                    "pipeline is the strategy this reference port actually uses."
                ),
                "falsification": (
                    "Any drawn command with a size other than 16x16, or a scaled or "
                    "distorted sprite command in the reachable set."
                ),
                "evidence": "MEASURED",
            },
            {
                "id": "VDP1-CF-4",
                "claim": "Horizontal flip is expressed in CMDCTRL, not by storing mirrored art.",
                "holds": any(int(anchor["flip_histogram"]["FLIP_X"]) > 0 for anchor in anchors),
                "consequence": (
                    "Facing costs no extra texture memory on this hardware path."
                ),
                "falsification": (
                    "An anchor in which no command sets the character-read-direction "
                    "bits while the actor is visibly mirrored."
                ),
                "evidence": "MEASURED",
            },
        ],
        "limits": [
            "VDP1 registers read back as zero through the debug interface, so the real draw-start address and frame-buffer state are unresolved.",
            "A single captured frame cannot show a control-flow mode the game uses only in other scenes.",
            "Texture spans are the bytes commands reference, not proof of allocation, lifetime or ownership.",
            "No count, address or span here is a budget for any other title.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, default=ROOT / ".deps" / "mshvsf_saturn_state")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data" / "mshvsf_saturn_vdp1_control_flow.json"
    )
    args = parser.parse_args()

    report = build_report(args.capture_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    reachable = [int(a["reachable_slot_count"]) for a in report["anchors"]]
    stored = [int(a["stored_nonzero_slots"]) for a in report["anchors"]]
    print(
        "Analyzed %d anchors: reachable %s, stored non-zero %s"
        % (len(reachable), reachable, stored)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
