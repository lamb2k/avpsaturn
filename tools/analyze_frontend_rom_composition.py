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


def describe(frame: int, decode_object_entries) -> dict | None:
    cps_a_path = CAP / ("cps_a_regs_%04d.tsv" % frame)
    cps_b_path = CAP / ("cps_b_regs_%04d.tsv" % frame)
    if not cps_a_path.is_file() or not cps_b_path.is_file():
        return None
    cps_a = load_words(cps_a_path)
    cps_b = load_words(cps_b_path)

    obj_path = CAP / ("objram_active_%04d.tsv" % frame)
    if not obj_path.is_file():
        obj_path = CAP / ("objram1_%04d.tsv" % frame)
    obj = load_words(obj_path) if obj_path.is_file() else []

    layer_control = cps_b[0x26 // 2]
    order = [(layer_control >> shift) & 3 for shift in (6, 8, 10, 12)]
    tilemaps = [layer for layer in order if layer != 0]

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
        "key_frames": frames,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    for entry in frames:
        print("frame %d: tilemaps %s bases %s | objects drawn %d "
              "(slots %d, codes %d, banks %s)"
              % (entry["frame"], entry["active_tilemap_layers"],
                 list(entry["tilemap_bases"].values()),
                 entry["objects_drawn"], entry["object_slots_parsed"],
                 entry["object_distinct_tile_codes"],
                 entry["object_palette_banks"]))
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
