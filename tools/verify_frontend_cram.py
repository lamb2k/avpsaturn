"""Falsify the frontend palette-to-CRAM link against a live hold capture.

An 8bpp NBG1 bitmap takes its colour base from the NBG1 bitmap palette-number
field, which only supplies colour-address bits 8-10: the base is always a whole
256-entry CRAM block, `256 * palette id`.  Jo's CRAM allocator returns
`jo_palette::data` one entry above that base, which is what its 4bpp sprite
path expects and is wrong for a bitmap surface.  Before the fix every live
frontend surface index matched CRAM at `base + 1`; the surface therefore
rendered the colour of `index - 1`.

This check reads the untracked live capture produced by
`tools/capture_frontend_cram.py`, requires an exact match at the block base for
every palette index the surface actually uses, requires the off-by-one reading
to fail, and runs a negative control that perturbs one 16-entry palette bank
and must break the same comparison.  It skips cleanly when the capture or the
converter payloads are absent, because both are private ROM-derived artifacts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "build" / "frontend_cram_readback.json"
FRONT = ROOT / "build" / "avsp_cd" / "FRONT"
REPORT = ROOT / "data" / "avsp_frontend_cram_readback.json"

# Hold order is fixed by avsp_shot_holds[] in main.c.  Hold 15 is the Round 1
# title, which still runs through the legacy sequence-hold palette rather than
# a FRONT payload, so it carries register evidence only.
SURFACE_BY_HOLD = {0: "title"}
SURFACE_BY_HOLD.update({index: "select" for index in range(1, 15)})
SURFACES = {
    "title": ("TITLE.PAL", "TITLE.RLE"),
    "select": ("SELBACK.PAL", "SELBACK.RLE"),
}
BANK_ENTRIES = 16


def palette_entries(path: Path) -> list[int]:
    data = path.read_bytes()
    return [int.from_bytes(data[i * 2:i * 2 + 2], "big")
            for i in range(len(data) // 2)]


def live_indices(path: Path) -> list[int]:
    """Palette indices the run-length encoded surface actually references."""
    data = path.read_bytes()
    return sorted({data[offset + 1] for offset in range(0, len(data), 2)})


def matches(cram: list[int], start_entry: int, base_entry: int,
            palette: list[int], indices: list[int]) -> int:
    offset = base_entry - start_entry
    return sum(1 for index in indices if cram[offset + index] == palette[index])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, default=CAPTURE)
    parser.add_argument("--front", type=Path, default=FRONT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()

    if not args.capture.is_file() or not (args.front / "TITLE.PAL").is_file():
        print("frontend CRAM readback: SKIPPED - live capture absent")
        return 0

    capture = json.loads(args.capture.read_text(encoding="ascii"))
    holds = capture["holds"]
    surfaces = {
        name: (palette_entries(args.front / pal), live_indices(args.front / rle))
        for name, (pal, rle) in SURFACES.items()
    }

    report_holds = []
    failures = []
    for key in sorted(holds, key=int):
        hold = int(key)
        record = holds[key]
        registers = record["registers"]
        cram = record["cram"]
        start = record["cram_start_entry"]
        base = record["nbg1_colour_base_entry"]
        entry = {
            "hold": hold,
            "encounter_state": record["diagnostics"]["encounter_state"],
            "hold_timer": record["diagnostics"]["hold_timer"],
            "chctla": f"0x{registers['CHCTLA']:04X}",
            "bmpna": f"0x{registers['BMPNA']:04X}",
            "craofa": f"0x{registers['CRAOFA']:04X}",
            "nbg1_bitmap_enabled": bool(registers["CHCTLA"] & 0x200),
            "nbg1_colour_number": (registers["CHCTLA"] >> 12) & 3,
            "nbg1_bitmap_palette_number": record["nbg1_bitmap_palette_number"],
            "nbg1_colour_base_entry": base,
        }

        if not entry["nbg1_bitmap_enabled"] or entry["nbg1_colour_number"] != 1:
            failures.append(f"hold {hold}: NBG1 is not an 8bpp bitmap "
                            f"(CHCTLA={entry['chctla']})")
        if registers["CRAOFA"] & 0x70:
            failures.append(f"hold {hold}: unexpected NBG1 CRAM offset "
                            f"{entry['craofa']}")

        name = SURFACE_BY_HOLD.get(hold)
        if name is not None:
            palette, indices = surfaces[name]
            at_base = matches(cram, start, base, palette, indices)
            at_next = matches(cram, start, base + 1, palette, indices)
            entry.update({"surface": name, "live_indices": len(indices),
                          "exact_at_base": at_base,
                          "exact_at_base_plus_one": at_next})
            if at_base != len(indices):
                failures.append(
                    f"hold {hold} ({name}): {at_base}/{len(indices)} live "
                    f"indices match CRAM at block base {base}")
            if at_next == len(indices):
                failures.append(
                    f"hold {hold} ({name}): payload also matches at base + 1, "
                    "so the comparison does not discriminate")
        report_holds.append(entry)

    # Negative control: shifting one 16-entry bank of the expected palette must
    # break the base comparison for a surface that just passed it exactly.
    control_hold = holds["0"]
    palette, indices = surfaces["title"]
    perturbed = list(palette)
    bank = min(indices[-1] // BANK_ENTRIES, 15)
    for offset in range(BANK_ENTRIES):
        perturbed[bank * BANK_ENTRIES + offset] ^= 0x0210
    control = matches(control_hold["cram"], control_hold["cram_start_entry"],
                      control_hold["nbg1_colour_base_entry"], perturbed,
                      indices)
    if control == len(indices):
        failures.append(
            f"negative control: perturbing palette bank {bank} still matched")

    if failures:
        for line in failures:
            print(f"frontend CRAM readback: FAIL - {line}")
        return 1

    args.report.write_text(json.dumps({
        "schema": 1,
        "classification": "Live Saturn VDP2 bitmap/palette register and CRAM "
                          "alignment evidence; counts and register values "
                          "only, no ROM-derived colour data",
        "instrument": "pinned Yaba Sanshiro MCP debug server, "
                      "-FrontendShotTest holds",
        "rule": "an 8bpp NBG1 bitmap reads CRAM from 256 * palette id, while "
                "Jo's allocator returns jo_palette::data one entry above that "
                "base",
        "negative_control": {
            "perturbed_palette_bank": bank,
            "exact_at_base": control,
            "required": "fewer than %d" % len(indices),
        },
        "holds": report_holds,
    }, indent=1, sort_keys=True) + "\n", encoding="ascii")
    checked = [entry for entry in report_holds if "surface" in entry]
    print(f"frontend CRAM readback: PASS - {len(report_holds)} holds, "
          f"{len(checked)} surface comparisons exact at the block base, "
          f"negative control failed as required")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
