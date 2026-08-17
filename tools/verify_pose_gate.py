"""The pixel-exact pose gate.

This is the gate that blocks native reimplementation, collision replacement and
AI translation. It answers one question: does a sprite assembly decoded from
program ROM reproduce an already-verified captured pose exactly?

Two rules make the answer trustworthy, and both were wrong in the earlier
ad-hoc attempt:

* **The oracle is a decoded archive pose, not a screenshot.** `/SPR4/*.RLE` are
  built from verified MAME captures and hash-checked by the build. A
  full-screen screenshot contains background, HUD and other actors, so a single
  assembly can never match one.
* **Passing means zero differing pixels.** Not 99.9%, and no colour tolerance.
  A percentage computed over a whole canvas is dominated by shared empty space,
  so an empty composition can score high against a mostly-empty oracle. That is
  a false pass, and a false pass here corrupts every phase downstream.

Alignment is handled by comparing the two images cropped to their own
non-transparent bounding boxes, so the test does not depend on knowing the
assembly's screen origin yet. If the crops differ in size the geometry is
wrong, which is itself a real answer.

The composition below is the current *hypothesis* about the selector-6 packed
long. It is expected to fail until the format is right; that is the point of a
gate. Change `compose_assembly` as the interpretation improves, never the
comparison.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_avspu_stage1 import decode_tile  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
GFX_REGION = ROOT / ".deps" / "mame" / "captures" / "gfx_region.bin"
SPRITE_DIR = ROOT / "build" / "avsp_cd" / "SPR4"
BOSS_HEADER = ROOT / "generated" / "avsp_boss_animation.h"
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"

BOSS_ARCHIVE_FILES = ("BACT.RLE", "BHIT.RLE", "BKO.RLE")
CEL_WIDTH = 288
CEL_HEIGHT = 192
TRANSPARENT_PEN = 0


def rle_decode(data: bytes) -> bytes:
    """Count/value RLE, matching rle_decode_bytes in extract_avspu_stage1."""
    if len(data) % 2:
        raise ValueError("RLE payload has an odd byte count")
    out = bytearray()
    for offset in range(0, len(data), 2):
        count = data[offset]
        if count == 0:
            raise ValueError("RLE payload contains a zero-length run")
        out.extend(bytes((data[offset + 1],)) * count)
    return bytes(out)


def header_table(name: str) -> list[int]:
    text = BOSS_HEADER.read_text(encoding="ascii", errors="ignore")
    match = re.search(name + r"\[[^\]]*\]\s*=\s*\{(.*?)\};", text, re.S)
    if not match:
        raise SystemExit(f"table {name} not found in {BOSS_HEADER.name}")
    return [int(value.strip(), 0) for value in match.group(1).split(",")
            if value.strip()]


def unpack_4bpp(packed: bytes, width: int, height: int) -> np.ndarray:
    """High-nibble-first 4bpp to one byte per pixel."""
    raw = np.frombuffer(packed, dtype=np.uint8)
    pixels = np.empty(raw.size * 2, dtype=np.uint8)
    pixels[0::2] = raw >> 4
    pixels[1::2] = raw & 0x0F
    return pixels.reshape(height, width)


def load_oracle_pose(pose_index: int) -> tuple[np.ndarray, int]:
    """Decode one verified archive pose to a 288x192 pen-index image."""
    offsets = header_table("avsp_boss_rle_offsets")
    archives = header_table("avsp_boss_rle_archives")
    lengths = header_table("avsp_boss_rle_bytes")
    frames = header_table("avsp_boss_source_frames")
    if not 0 <= pose_index < len(offsets):
        raise SystemExit(f"pose {pose_index} outside 0..{len(offsets) - 1}")

    archive_path = SPRITE_DIR / BOSS_ARCHIVE_FILES[archives[pose_index]]
    if not archive_path.is_file():
        raise SystemExit(f"missing oracle archive {archive_path}; run build.ps1")
    blob = archive_path.read_bytes()
    start = offsets[pose_index]
    payload = blob[start:start + lengths[pose_index]]
    decoded = rle_decode(payload)
    expected = CEL_WIDTH * CEL_HEIGHT // 2
    if len(decoded) != expected:
        raise SystemExit(
            f"pose {pose_index} decoded to {len(decoded)} bytes, expected "
            f"{expected}; the archive layout assumption is wrong")
    return unpack_4bpp(decoded, CEL_WIDTH, CEL_HEIGHT), frames[pose_index]


def compose_assembly(assembly: dict, gfx: bytearray) -> np.ndarray:
    """HYPOTHESIS under test: build a pose from a selector-6 assembly.

    Current reading of each entry: the packed long carries a tile code in its
    low word and attributes in its high word, whose low byte is the palette
    bank.  Budget (not tile_count) is the real entry count.  Layout words are
    signed pixel offsets on a 16-pixel tile grid.
    """
    canvas = np.zeros((CEL_HEIGHT, CEL_WIDTH), dtype=np.uint8)
    origin_x = CEL_WIDTH // 2
    origin_y = CEL_HEIGHT - 8
    placed = 0
    entry_count = assembly.get("budget", assembly.get("tile_count", 4))
    for entry in assembly["entries"][:entry_count]:
        packed = int(entry["packed_source"], 16)
        code = packed & 0xFFFF
        attributes = (packed >> 16) & 0xFFFF
        # A negative-looking packed long is not a tile reference under this
        # reading; skip rather than fabricate a tile.
        if attributes in (0xFFFF,) or code == 0xFFFF:
            continue
        tile = np.array(decode_tile(gfx, code, 16).convert("P"), dtype=np.uint8)
        x = origin_x + int(entry["layout_x_signed"])
        y = origin_y + int(entry["layout_y_signed"])
        if x < 0 or y < 0 or x + 16 > CEL_WIDTH or y + 16 > CEL_HEIGHT:
            continue
        region = canvas[y:y + 16, x:x + 16]
        mask = tile != TRANSPARENT_PEN
        region[mask] = tile[mask]
        placed += 1
    if placed == 0:
        print("  WARNING: no tiles placed; composition produced an empty image")
    return canvas


def crop_to_content(image: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    rows = np.flatnonzero((image != TRANSPARENT_PEN).any(axis=1))
    cols = np.flatnonzero((image != TRANSPARENT_PEN).any(axis=0))
    if rows.size == 0 or cols.size == 0:
        return np.zeros((0, 0), dtype=np.uint8), (0, 0)
    return (image[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1],
            (int(cols[0]), int(rows[0])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", default="0x13dea0",
                        help="selector-6 assembly address to compose")
    parser.add_argument("--pose", type=int, default=None,
                        help="oracle pose index; default scans every pose")
    parser.add_argument("--dump", action="store_true",
                        help="write composed and oracle crops as PNGs")
    args = parser.parse_args()

    if not GFX_REGION.is_file():
        raise SystemExit(f"missing {GFX_REGION}")
    gfx = bytearray(GFX_REGION.read_bytes())
    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    assembly = next((a for a in scripts.get("assemblies", [])
                     if a["address"].lower() == args.assembly.lower()), None)
    if assembly is None:
        raise SystemExit(f"assembly {args.assembly} not in {SCRIPTS.name}")

    composed = compose_assembly(assembly, gfx)
    crop, origin = crop_to_content(composed)
    print(f"assembly {args.assembly}: {assembly['tile_count']} tiles declared, "
          f"composed content {crop.shape[1]}x{crop.shape[0]} at {origin}")

    pose_count = len(header_table("avsp_boss_rle_offsets"))
    candidates = ([args.pose] if args.pose is not None
                  else list(range(pose_count)))

    best = None
    for pose_index in candidates:
        oracle, source_frame = load_oracle_pose(pose_index)
        oracle_crop, oracle_origin = crop_to_content(oracle)
        if crop.shape != oracle_crop.shape:
            note = (f"shape {crop.shape[1]}x{crop.shape[0]} vs "
                    f"{oracle_crop.shape[1]}x{oracle_crop.shape[0]}")
            if best is None:
                best = (pose_index, None, note, source_frame)
            continue
        differing = int(np.count_nonzero(crop != oracle_crop))
        if best is None or best[1] is None or differing < best[1]:
            best = (pose_index, differing, "", source_frame)
        if differing == 0:
            print(f"\nPASS: assembly {args.assembly} reproduces pose "
                  f"{pose_index} (source frame {source_frame}) exactly, "
                  f"{crop.shape[1]}x{crop.shape[0]} pixels, 0 differing.")
            return

    print("\nFAIL: no oracle pose is reproduced exactly.")
    if best is not None:
        index, differing, note, source_frame = best
        detail = (f"{differing} differing pixels" if differing is not None
                  else f"no shape match ({note})")
        print(f"  closest: pose {index} (source frame {source_frame}), {detail}")
    print("  The gate is red. Do not proceed to native reimplementation,")
    print("  collision replacement, stage data or AI translation.")

    if args.dump:
        from PIL import Image
        # Generated images are ignored build output, never repository content.
        dump_dir = ROOT / ".deps" / "mame" / "posegate"
        dump_dir.mkdir(parents=True, exist_ok=True)
        Image.fromarray(crop * 16).save(dump_dir / "composed.png")
        oracle, _ = load_oracle_pose(candidates[0])
        oracle_crop, _ = crop_to_content(oracle)
        Image.fromarray(oracle_crop * 16).save(dump_dir / "oracle.png")
        print(f"  wrote composed.png and oracle.png under "
              f"{dump_dir.relative_to(ROOT)}")
    sys.exit(1)


if __name__ == "__main__":
    main()
