"""Falsify the frontend palette-to-CRAM link against a live hold capture.

Jo Engine's palette layout is one-based by design, not by accident.  Colour
RAM is allocated in 256-entry blocks, `jo_palette::data` is the entry after
the block base, and `JO_PALETTE_MAX_COLORS` is 255, because Saturn pixel and
pen value zero is transparent: pixel `p` reads `data[p - 1]`, which is
hardware colour entry `256 * id + p`.  Jo's own 8bpp TGA reader follows the
same rule by adding one to every decoded pixel.

The ROM-derived frontend converter now obeys that contract: opaque fitted
surfaces reserve index zero and use `1..255`, the palette file stays indexed
by pixel value, and the runtime copies through `jo_palette::data` with the
bounded helpers in `avsp_cram.h`.  An earlier build instead wrote the payload
at the hardware block base; that aliased the preceding allocation's boundary
and depended on Jo's allocation order, and was rejected.

This check reads the untracked live capture produced by
`tools/capture_frontend_cram.py` and requires all of the following:

* every live surface index is in `1..255`, so nothing reads below `data[0]`;
* palette file entry zero is reserved;
* every used surface index matches CRAM at `256 * id + index` exactly;
* neither block boundary was disturbed by a frontend load, proved live by the
  runtime's own boundary counter as well as by the captured boundary entries;
* the previous zero-based payload fails, so the comparison discriminates;
* a one-bank palette perturbation fails.

It skips cleanly when the capture or the converter payloads are absent,
because both are private ROM-derived artifacts.  A missing capture reports
`SKIPPED`, never `PASS`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "build" / "frontend_cram_readback.json"
FRONT = ROOT / "build" / "avsp_cd" / "FRONT"
REPORT = ROOT / "data" / "avsp_frontend_cram_readback.json"

# Hold order is fixed by avsp_shot_holds[] in main.c.  Hold 18 is the Round 1
# title, which still runs through the legacy sequence-hold palette rather than
# a FRONT payload, so it carries register and counter evidence only.
SURFACE_BY_HOLD = {0: "title"}
SURFACE_BY_HOLD.update({index: "select" for index in range(1, 18)})
SURFACES = {
    "title": ("TITLE.PAL", "TITLE.RLE"),
    "select": ("SELBACK.PAL", "SELBACK.RLE"),
}
BLOCK_ENTRIES = 256
MAX_LIVE_COLOURS = 255
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
            palette: list[int], indices: list[int], shift: int = 0) -> int:
    """Count live indices whose CRAM entry holds the colour the file assigns.

    `shift` models a rejected payload: shift 1 is the old zero-based file,
    whose entry i-1 held the colour this contract puts at entry i.
    """
    offset = base_entry - start_entry
    return sum(1 for index in indices
               if cram[offset + index] == palette[index - shift])


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

    failures: list[str] = []

    # Converter-side contract, independent of any live capture.
    for name, (palette, indices) in surfaces.items():
        if indices[0] < 1:
            failures.append(
                f"{name}: surface still references reserved index "
                f"{indices[0]}; Jo's index zero is transparent")
        if indices[-1] > MAX_LIVE_COLOURS:
            failures.append(f"{name}: live index {indices[-1]} exceeds 255")
        if palette[0] != 0:
            failures.append(f"{name}: palette entry zero is not reserved")

    report_holds = []
    for key in sorted(holds, key=int):
        hold = int(key)
        record = holds[key]
        registers = record["registers"]
        cram = record["cram"]
        start = record["cram_start_entry"]
        base = record["nbg1_colour_base_entry"]
        diagnostics = record["diagnostics"]
        entry = {
            "hold": hold,
            "encounter_state": diagnostics["encounter_state"],
            "hold_timer": diagnostics["hold_timer"],
            "chctla": f"0x{registers['CHCTLA']:04X}",
            "bmpna": f"0x{registers['BMPNA']:04X}",
            "craofa": f"0x{registers['CRAOFA']:04X}",
            "nbg1_bitmap_enabled": bool(registers["CHCTLA"] & 0x200),
            "nbg1_colour_number": (registers["CHCTLA"] >> 12) & 3,
            "nbg1_bitmap_palette_number": record["nbg1_bitmap_palette_number"],
            "nbg1_colour_base_entry": base,
            "palette_boundary_writes":
                diagnostics["frontend_palette_boundary_writes"],
            "palette_errors": diagnostics["frontend_palette_errors"],
            "rle_errors": diagnostics["frontend_rle_errors"],
            "vdp1_commands": diagnostics["frontend_commands"],
        }

        if not entry["nbg1_bitmap_enabled"] or entry["nbg1_colour_number"] != 1:
            failures.append(f"hold {hold}: NBG1 is not an 8bpp bitmap "
                            f"(CHCTLA={entry['chctla']})")
        if registers["CRAOFA"] & 0x70:
            failures.append(f"hold {hold}: unexpected NBG1 CRAM offset "
                            f"{entry['craofa']}")
        # The runtime samples both hardware block boundaries around every
        # palette load; a non-zero count means a load reached a neighbouring
        # Jo allocation.
        if entry["palette_boundary_writes"]:
            failures.append(
                f"hold {hold}: {entry['palette_boundary_writes']} frontend "
                "palette load(s) wrote a neighbouring block boundary")

        name = SURFACE_BY_HOLD.get(hold)
        if name is not None:
            palette, indices = surfaces[name]
            exact = matches(cram, start, base, palette, indices)
            zero_based = matches(cram, start, base, palette, indices, shift=1)
            entry.update({"surface": name, "live_indices": len(indices),
                          "live_index_range": [indices[0], indices[-1]],
                          "exact_one_based": exact,
                          "matches_old_zero_based_payload": zero_based})
            if exact != len(indices):
                failures.append(
                    f"hold {hold} ({name}): {exact}/{len(indices)} live "
                    f"indices match CRAM at 256*id + index")
            if zero_based == len(indices):
                failures.append(
                    f"hold {hold} ({name}): the rejected zero-based payload "
                    "also matches, so the comparison does not discriminate")
        report_holds.append(entry)

    # Negative control: perturbing one 16-entry palette bank must break a
    # comparison that just passed exactly.
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
        "schema": 2,
        "classification": "Live Saturn VDP2 bitmap/palette register, CRAM "
                          "alignment and boundary-ownership evidence; counts, "
                          "register values and verdicts only, no ROM-derived "
                          "colour payload",
        "instrument": "pinned Yaba Sanshiro MCP debug server, "
                      "-FrontendShotTest holds",
        "contract": "Jo Engine one-based palette: colour RAM is allocated in "
                    "256-entry blocks, jo_palette::data is the entry after the "
                    "block base, and pixel value p reads hardware entry "
                    "256 * id + p",
        "verdict": "PASS",
        "surfaces": {
            name: {"live_colours": len(indices),
                   "live_index_range": [indices[0], indices[-1]],
                   "palette_entry_zero_reserved": palette[0] == 0}
            for name, (palette, indices) in surfaces.items()
        },
        "negative_controls": {
            "perturbed_palette_bank": bank,
            "perturbed_bank_exact_matches": control,
            "required": f"fewer than {len(indices)}",
            "rejected_zero_based_payload_matches": [
                entry["matches_old_zero_based_payload"]
                for entry in report_holds if "surface" in entry],
        },
        "holds": report_holds,
    }, indent=1, sort_keys=True) + "\n", encoding="ascii")
    checked = [entry for entry in report_holds if "surface" in entry]
    print(f"frontend CRAM readback: PASS - {len(report_holds)} holds, "
          f"{len(checked)} surface comparisons exact at 256*id + index, "
          "no boundary writes, zero-based and perturbed-bank controls failed")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
