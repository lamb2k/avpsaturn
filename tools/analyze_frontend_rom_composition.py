"""What the frontend screens are COMPOSED OF, from ROM-truth state only.

The shipped title and character-select screens are captured keyframes - flat
pictures. To rebuild them from original assets the port needs to know what
the ROM actually draws them with: CPS tilemap layers (scroll1/2/3), the
object/sprite list, or both. This tool answers that from the capture written
by tools/mame_capture_frontend_rom.lua (gfxram + cps_a/cps_b registers +
objram + palette - the same share set the stage background decode already
consumes), never from pixels.

It deliberately reports only structure - layer enables and draw order,
tilemap base addresses, scroll offsets, object counts, tile codes, palette
banks, and coordinates. No ROM bytes and no decoded imagery are written, so
the manifest is safe to track.

Input (private, untracked):
  .deps/mame/frontend_rom/{cps_a_regs,cps_b_regs,objram_active,objram1}_NNNN.tsv

Output (tracked):
  data/frontend_rom_composition.json

Skips cleanly (exit 0) when the capture is absent, the same contract as the
other private-input tools; regenerate with capture_frontend_rom.ps1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP = ROOT / ".deps" / "mame" / "frontend_rom"
OUT_JSON = ROOT / "data" / "frontend_rom_composition.json"

sys.path.insert(0, str(ROOT / "tools"))

# Frames written in full by the capture script. 1620 is the attract/title
# page; 1700 is mid slide-in; 1760/1790 are the settled select screen; 1900
# and 2100 are the confirm and round-title windows.
KEY_FRAMES = (1620, 1700, 1760, 1790, 1900, 2100)


def load_words(path: Path) -> list[int]:
    words: list[int] = []
    with path.open() as handle:
        next(handle)
        for line in handle:
            parts = line.split()
            if len(parts) >= 2:
                words.append(int(parts[1], 16))
    return words


def live_tilemap_banks(gfxram: list[int], cps_a: list[int], cps_b: list[int]
                       ) -> dict:
    """Distinct CPS palette banks actually referenced by the visible tilemap
    cells, per layer.

    This is the probe the reference-port transfer matrix prescribes: count
    LIVE colour banks per frame, because a per-tile pipeline spends colour
    RAM, not VDP1 texture memory. CPS2's palette is 128 banks of 16: objects
    take 0x00-0x1F, scroll1 +0x20, scroll2 +0x40, scroll3 +0x60 (the same
    derivation extract_avspu_stage1.render_background uses). Only tile
    ATTRIBUTES are read - no tile pixels, no ROM bytes.
    """
    VISIBLE_LEFT, VISIBLE_TOP = 64, 16
    VISIBLE_WIDTH, VISIBLE_HEIGHT = 384, 224

    layer_control = cps_b[0x26 // 2]
    order = [(layer_control >> shift) & 3 for shift in (6, 8, 10, 12)]
    base_words = []
    for register in (1, 2, 3):
        byte_address = (cps_a[register] * 256) & 0x3FFFF
        byte_address &= ~(0x4000 - 1)
        base_words.append(byte_address // 2)
    scroll_x = (cps_a[6], cps_a[8], cps_a[10])
    scroll_y = (cps_a[7], cps_a[9], cps_a[11])

    per_layer: dict[str, list[int]] = {}
    for layer_number in order:
        if layer_number == 0:
            continue
        layer_index = layer_number - 1
        size = (8, 16, 32)[layer_index]
        enable_mask = (0x02, 0x04, 0x08)[layer_index]
        if not (layer_control & enable_mask):
            continue
        if layer_index > 0 and not (cps_a[17] & (1 << (layer_index + 1))):
            continue
        banks: set[int] = set()
        for screen_y in range(0, VISIBLE_HEIGHT + size, size):
            world_y = (screen_y + VISIBLE_TOP + scroll_y[layer_index]) % (64 * size)
            row = world_y // size
            for screen_x in range(0, VISIBLE_WIDTH + size, size):
                world_x = (screen_x + VISIBLE_LEFT + scroll_x[layer_index]) % (64 * size)
                column = world_x // size
                if layer_index == 0:
                    tile_index = (row & 0x1F) + ((column & 0x3F) << 5) + ((row & 0x20) << 6)
                    bias = 0x20
                elif layer_index == 1:
                    tile_index = (row & 0x0F) + ((column & 0x3F) << 4) + ((row & 0x30) << 6)
                    bias = 0x40
                else:
                    tile_index = (row & 0x07) + ((column & 0x3F) << 3) + ((row & 0x38) << 6)
                    bias = 0x60
                attr_word = base_words[layer_index] + tile_index * 2 + 1
                if 0 <= attr_word < len(gfxram):
                    banks.add((gfxram[attr_word] & 0x1F) + bias)
        per_layer["scroll%d" % layer_number] = sorted(banks)
    return per_layer


def describe(frame: int, decode_object_entries) -> dict | None:
    cps_a_path = CAP / ("cps_a_regs_%04d.tsv" % frame)
    cps_b_path = CAP / ("cps_b_regs_%04d.tsv" % frame)
    if not cps_a_path.is_file() or not cps_b_path.is_file():
        return None
    cps_a = load_words(cps_a_path)
    cps_b = load_words(cps_b_path)
    gfxram_path = CAP / ("gfxram_%04d.tsv" % frame)
    gfxram = load_words(gfxram_path) if gfxram_path.is_file() else []

    obj_path = CAP / ("objram_active_%04d.tsv" % frame)
    if not obj_path.is_file():
        obj_path = CAP / ("objram1_%04d.tsv" % frame)
    obj = load_words(obj_path) if obj_path.is_file() else []

    layer_control = cps_b[0x26 // 2]
    order = [(layer_control >> shift) & 3 for shift in (6, 8, 10, 12)]
    tilemaps = [layer for layer in order if layer != 0]

    tilemap_banks = live_tilemap_banks(gfxram, cps_a, cps_b) if gfxram else {}
    entries = decode_object_entries(obj) if obj else []
    # An all-zero entry parked off-screen is an unused slot, not a drawn
    # object; count it separately so "how many sprites does this screen
    # really use" is not inflated.
    drawn = [e for e in entries if e["tile_code"] != 0]

    return {
        "frame": frame,
        "cps_b_layer_control": "0x%04X" % layer_control,
        "layer_draw_order_back_to_front": order,
        "active_tilemap_layers": tilemaps,
        "tilemap_bases": {
            "scroll1": "0x%05X" % ((cps_a[1] * 256) & 0x3FFFF),
            "scroll2": "0x%05X" % ((cps_a[2] * 256) & 0x3FFFF),
            "scroll3": "0x%05X" % ((cps_a[3] * 256) & 0x3FFFF),
        },
        "scroll_x": [cps_a[6], cps_a[8], cps_a[10]],
        "scroll_y": [cps_a[7], cps_a[9], cps_a[11]],
        "object_slots_parsed": len(entries),
        "objects_drawn": len(drawn),
        "object_distinct_tile_codes": len({e["tile_code"] for e in drawn}),
        "object_palette_banks": sorted({e["colour"] for e in drawn}),
        "live_tilemap_palette_banks": tilemap_banks,
        "live_palette_banks_total": (
            len({e["colour"] for e in drawn})
            + sum(len(v) for v in tilemap_banks.values())),
        "objects": [
            {
                "x": e["screen_x"], "y": e["screen_y"],
                "w": e["width"], "h": e["height"],
                "tile_code": "0x%04X" % e["tile_code"],
                "colour": e["colour"], "priority": e["priority"],
            }
            for e in drawn[:16]
        ],
    }


def main() -> int:
    if not CAP.is_dir() or not any(CAP.glob("cps_a_regs_*.tsv")):
        print("frontend ROM composition: SKIPPED - capture absent (%s); "
              "regenerate with capture_frontend_rom.ps1"
              % CAP.relative_to(ROOT).as_posix())
        return 0

    from extract_avspu_stage1 import decode_object_entries

    frames = [d for d in (describe(f, decode_object_entries)
                          for f in KEY_FRAMES) if d]
    if not frames:
        print("frontend ROM composition: FAIL - capture present but no key "
              "frame parsed")
        return 1

    manifest = {
        "schema": 1,
        "classification": "frontend screen composition - CPS layer/object "
                          "structure only; no ROM bytes, no imagery",
        "question": "what does the ROM draw the title and character-select "
                    "screens WITH - tilemap layers, objects, or both?",
        "method": "ROM-truth capture (tools/mame_capture_frontend_rom.lua "
                  "writes gfxram + cps_a/cps_b + objram + palette, the same "
                  "share set the stage background decode consumes); layer "
                  "control and object list read with the existing "
                  "tools/extract_avspu_stage1.py decoders. No pixels.",
        "finding": "the settled character-select screen is drawn almost "
                   "entirely by the three CPS tilemap layers; its only "
                   "drawn objects are the small 1P cursor marker. The "
                   "plate slide-in is a large transient object burst. The "
                   "title/attract page uses a DIFFERENT set of tilemap "
                   "base addresses than the select page, so the two are "
                   "distinct tilemap pages in gfxram.",
        "implication_for_the_port": "a faithful rebuild needs a CPS tilemap "
                                    "path (tile codes + palette per layer) "
                                    "in addition to the existing per-tile "
                                    "VDP1 object path; it cannot be done "
                                    "with sprites alone, and it does not "
                                    "need a captured picture.",
        "colour_ram_finding": "LIVE palette banks per frame: character "
                              "select 17, title/attract 19, round-1 title "
                              "32. The Saturn build currently allocates "
                              "AVSP_EXACT_PALETTE_BANKS = 8 (128 colours) "
                              "for actors. The frontend therefore needs 2-4x "
                              "the current colour-RAM allocation and cannot "
                              "be rendered faithfully inside it. This is the "
                              "AvP-specific validation of the reference "
                              "port's warning that a per-tile pipeline "
                              "spends COLOUR RAM rather than VDP1 texture "
                              "memory; the reference's own 12-14 live banks "
                              "per combat anchor is context, never an AvP "
                              "budget.",
        "key_frames": frames,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    for entry in frames:
        print("frame %d: tilemaps %s | objects drawn %d (banks %s) | "
              "live tilemap banks %s | LIVE PALETTE BANKS TOTAL %d"
              % (entry["frame"], entry["active_tilemap_layers"],
                 entry["objects_drawn"], entry["object_palette_banks"],
                 {k: len(v) for k, v in
                  entry["live_tilemap_palette_banks"].items()},
                 entry["live_palette_banks_total"]))
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
