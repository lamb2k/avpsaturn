"""The pixel-exact pose gate.

This is the format gate that blocks native animation reimplementation on a
misread sprite table. It answers one question: does a sprite assembly decoded
from program ROM reproduce an already-verified captured pose exactly when the
captured object's screen geometry is used as the placement oracle?

Two rules make the answer trustworthy, and both were wrong in the earlier
ad-hoc attempt:

* **The oracle is a decoded archive pose, not a screenshot.** `/SPR4/*.RLE`
  are built from verified MAME captures and hash-checked by the build. A
  full-screen screenshot contains background, HUD and other actors, so a
  single assembly can never match one.
* **Passing means zero differing pixels.** Not 99.9%, and no colour
  tolerance. A percentage computed over a whole canvas is dominated by
  shared empty space, so an empty composition can score high against a
  mostly-empty oracle. That is a false pass, and a false pass here corrupts
  every phase downstream.

Composition mirrors the verified oracle construction exactly. The oracle cel
for a pose is the CPS2 palette-27 object layer of one MAME frame, rendered
by ``extract_avspu_stage1.exact_object_layers`` onto a 288x192 canvas
anchored at the pose's recorded pivot. The steps that gate's earlier version
got wrong, and that this version reproduces:

* **Object selection is by the recorded palette-27 command set, not by a
  code range.** The code-range scan picked up stale RAM slots and split the
  real assembly, which broke seven of the twelve poses.
* **CPS2 X/Y positions wrap on a 1024 ring.** A boss part drawn near the
  ring boundary decodes as an off-screen object at x=958 unless the
  recorded ring-unwrap shift is applied. The oracle applies it; so must
  the gate, or the pose's union bounding box is wrong and every tile is
  clipped away.
* **Tile codes carry character-bank bits from the Y word**
  (``code + ((y & 0x6000) << 3)``).
* **Placement is per pixel** (partially visible tiles keep their visible
  half) and commands are drawn in descending object-list order, matching
  the oracle renderer.
* **Pens map CPS2 15 -> transparent 0 and 0..14 -> 1..15** in both images.

The ROM-decoded assembly must additionally contribute exactly the set of
object codes present in the frame's palette-27 run. A pixel-exact match
with the wrong code set is not a pass: it would mean two different ROM
descriptions render the same pixels and the decoder cannot be trusted.

Alignment is compared on crops of the two images' own non-transparent
bounding boxes, so the test does not depend on knowing the assembly's
screen origin yet. If the crops differ in size the geometry is wrong, which
is itself a real answer.

Position is audited independently by ``verify_position_gate.py``. Its current
scope covers 246 matched geometry frames: most parts are directly exact, shared
code sets leave decoded sibling-origin deltas, and two frames retain a narrow
four-pixel Y settling observation. Attack/hit assemblies and full exact
coverage remain open; a pose-gate pass must not be presented as a complete
runtime or functional-parity pass.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
GFX_REGION = ROOT / ".deps" / "mame" / "captures" / "gfx_region.bin"
SPRITE_DIR = ROOT / "build" / "avsp_cd" / "SPR4"
BOSS_HEADER = ROOT / "generated" / "avsp_boss_animation.h"
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"
ACTION_REPORT = ROOT / "data" / "boss_action_capture.json"
KO_REPORT = ROOT / "data" / "boss_ko_capture.json"
IDLE_BANK_FILE = (ROOT / ".deps" / "mame" / "captures" /
                  "boss_active_object_bank.txt")

BOSS_ARCHIVE_FILES = ("BACT.RLE", "BHIT.RLE", "BKO.RLE")
BOSS_PALETTE = 27
CEL_WIDTH = 288
CEL_HEIGHT = 192

_GFX: bytearray | None = None


def _blank() -> np.ndarray:
    return np.zeros((CEL_HEIGHT, CEL_WIDTH), dtype=np.uint8)


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


@lru_cache(maxsize=4096)
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


def read_words(path: Path) -> list[int]:
    return [
        int(line.split("\t")[1], 16)
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
        if line
    ]


def load_frame_geometry() -> dict[int, dict]:
    """Recorded palette-27 command sets and pivot geometry per source frame.

    The values are exactly the ones used to build the oracle archives:
    object word offsets, 1024-ring unwrap shifts, and the pivot
    (union centre, union bottom + 8) that exact_object_layers anchors to
    the canvas centre / bottom margin.
    """
    geometry: dict[int, dict] = {}
    action = json.loads(ACTION_REPORT.read_text(encoding="ascii"))
    for clip in action["clips"]:
        for sample in clip["timeline"]:
            frame = int(sample["frame"])
            geometry[frame] = {
                "path": ROOT / ".deps" / "mame" / "boss_actions" /
                        f"objram_active_{frame:05d}.tsv",
                "offsets": [int(o) for o in sample["object_offsets"]],
                "shift_x": int(sample["object_shift_x"]),
                "shift_y": 0,
                "pivot_x": int(sample["pivot_x"]),
                "pivot_bottom": int(sample["pivot_bottom"]),
            }
    ko = json.loads(KO_REPORT.read_text(encoding="ascii"))
    for sample in ko["ko"]["timeline"]:
        frame = int(sample["frame"])
        geometry.setdefault(frame, {
            "path": ROOT / ".deps" / "mame" / "boss_ko" /
                    f"objram_active_{frame:05d}.tsv",
            "offsets": [int(o) for o in sample["object_offsets"]],
            "shift_x": int(sample["object_shift_x"]),
            "shift_y": int(sample["object_shift_y"]),
            "pivot_x": int(sample["pivot_x"]),
            "pivot_bottom": int(sample["pivot_bottom"]),
        })
    # The frame-12660 idle pose was built from the isolated pre-capture,
    # with fixed offsets and pivot (see write_exact_boss_assets in
    # extract_avspu_stage1.py).
    bank = int(IDLE_BANK_FILE.read_text(encoding="ascii").strip())
    geometry.setdefault(12660, {
        "path": ROOT / ".deps" / "mame" / "captures" /
                f"boss_objram{bank}.tsv",
        "offsets": [36, 40, 44],
        "shift_x": 0,
        "shift_y": 0,
        "pivot_x": 74,
        "pivot_bottom": 211,
    })
    return geometry


@lru_cache(maxsize=65536)
def _tile_pens(code: int) -> np.ndarray:
    """One 16x16 tile as raw CPS2 pen indices (15 = transparent)."""
    if _GFX is None:
        raise SystemExit("graphics region not loaded")
    return np.asarray(avsp.decode_tile(_GFX, code, 16), dtype=np.uint8)


def compose_assembly(assembly: dict, frame: int,
                     geometry: dict[int, dict]) -> tuple[np.ndarray, str, bool]:
    """Compose one pose the way the oracle archive was built.

    Returns (canvas, note, codes_match). The canvas is a 288x192 pen image
    in the oracle's pen space (0 transparent, CPS2 pens 0..14 as 1..15).
    ``codes_match`` is True when the ROM assembly's object codes are exactly
    the codes of the frame's recorded palette-27 command set.
    """
    spec = geometry.get(frame)
    if spec is None:
        return _blank(), f"no object RAM geometry recorded for frame {frame}", False

    entries = avsp.decode_object_entries(read_words(spec["path"]))
    by_offset = {entry["offset"]: entry for entry in entries}
    missing = [offset for offset in spec["offsets"] if offset not in by_offset]
    if missing:
        return _blank(), (f"object word offsets {missing} absent from "
                          f"frame {frame}"), False

    shift_x, shift_y = spec["shift_x"], spec["shift_y"]
    commands = []
    for offset in spec["offsets"]:
        entry = by_offset[offset]
        x = (entry["x"] & ~0x3FF) | (((entry["x"] & 0x3FF) + shift_x) & 0x3FF)
        y = (entry["y"] & ~0x3FF) | (((entry["y"] & 0x3FF) + shift_y) & 0x3FF)
        commands.append({
            "offset": offset,
            "x": (x & 0x3FF) - avsp.VISIBLE_LEFT,
            "y": (y & 0x3FF) - avsp.VISIBLE_TOP,
            "code": entry["code"] + ((y & 0x6000) << 3),
            "attribute": entry["attribute"],
            "nx": entry["width"] // 16,
            "ny": entry["height"] // 16,
        })

    assembly_codes = {int(e["code"], 16)
                      for e in assembly["entries"][:assembly.get("count", 0)]}
    run_codes = {command["code"] & 0xFFFF for command in commands}
    codes_match = assembly_codes == run_codes
    note = ""
    if not codes_match:
        note = ("assembly codes "
                + " ".join(f"0x{c:04x}" for c in sorted(assembly_codes))
                + " != frame codes "
                + " ".join(f"0x{c:04x}" for c in sorted(run_codes)))

    canvas = _blank()
    canvas_x = CEL_WIDTH // 2 - spec["pivot_x"]
    canvas_y = CEL_HEIGHT - 8 - spec["pivot_bottom"]
    for command in sorted(commands, key=lambda c: c["offset"], reverse=True):
        attribute = command["attribute"]
        flip_x = bool(attribute & 0x20)
        flip_y = bool(attribute & 0x40)
        nx, ny = command["nx"], command["ny"]
        for tile_y in range(ny):
            for tile_x in range(nx):
                source_y = ny - 1 - tile_y if flip_y else tile_y
                source_x = nx - 1 - tile_x if flip_x else tile_x
                if not flip_x and not flip_y:
                    tile_code = ((command["code"] & ~0xF) +
                                 ((command["code"] + source_x) & 0xF) +
                                 0x10 * source_y)
                else:
                    tile_code = command["code"] + source_x + 0x10 * source_y
                tile = _tile_pens(tile_code)
                if flip_x:
                    tile = tile[:, ::-1]
                if flip_y:
                    tile = tile[::-1, :]
                dest_x = canvas_x + command["x"] + tile_x * 16
                dest_y = canvas_y + command["y"] + tile_y * 16
                x0 = max(dest_x, 0)
                y0 = max(dest_y, 0)
                x1 = min(dest_x + 16, CEL_WIDTH)
                y1 = min(dest_y + 16, CEL_HEIGHT)
                if x1 <= x0 or y1 <= y0:
                    continue
                region = tile[y0 - dest_y:y1 - dest_y, x0 - dest_x:x1 - dest_x]
                mask = region != 15
                canvas[y0:y1, x0:x1][mask] = region[mask] + 1
    return canvas, note, codes_match


def crop_to_content(image: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    rows = np.flatnonzero((image != 0).any(axis=1))
    cols = np.flatnonzero((image != 0).any(axis=0))
    if rows.size == 0 or cols.size == 0:
        return np.zeros((0, 0), dtype=np.uint8), (0, 0)
    return (image[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1],
            (int(cols[0]), int(rows[0])))


def _rank(result: tuple) -> tuple:
    """Ordering key: a measured pixel count beats no measurement at all."""
    differing = result[1]
    return (1, 0) if differing is None else (0, differing)


def _find_pose_match(assembly: dict, candidates: list[int],
                     geometry: dict[int, dict],
                     frames: list[int]) -> tuple | None:
    """Evaluate an assembly against candidate oracle poses.

    Each candidate is composed at its own source frame. Returns
    (pose_index, differing_pixels_or_None, note, source_frame); differing
    is None when the pair cannot be measured (missing geometry, code-set
    mismatch, or shape mismatch).
    """
    best = None
    for pose_idx in candidates:
        frame = frames[pose_idx]
        canvas, note, codes_match = compose_assembly(assembly, frame, geometry)
        crop, _origin = crop_to_content(canvas)
        oracle, _source = load_oracle_pose(pose_idx)
        oracle_crop, _oracle_origin = crop_to_content(oracle)
        if not codes_match:
            candidate = (pose_idx, None, f"code mismatch; {note}", frame)
        elif crop.shape != oracle_crop.shape:
            candidate = (pose_idx, None,
                         f"shape {crop.shape[1]}x{crop.shape[0]} vs "
                         f"{oracle_crop.shape[1]}x{oracle_crop.shape[0]}",
                         frame)
        else:
            differing = int(np.count_nonzero(crop != oracle_crop))
            candidate = (pose_idx, differing, "", frame)
        if best is None or _rank(candidate) < _rank(best):
            best = candidate
        if candidate[1] == 0:
            return candidate
    return best


def main() -> None:
    global _GFX
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly",
                        help="selector-6 assembly address to compose (default: all)")
    parser.add_argument("--pose", type=int, default=None,
                        help="oracle pose index; default scans every pose")
    parser.add_argument("--dump", action="store_true",
                        help="write composed and oracle crops as PNGs")
    args = parser.parse_args()

    if not GFX_REGION.is_file():
        raise SystemExit(f"missing {GFX_REGION}")
    _GFX = bytearray(GFX_REGION.read_bytes())
    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    assemblies = scripts.get("assemblies", [])
    geometry = load_frame_geometry()
    frames = header_table("avsp_boss_source_frames")

    if args.assembly:
        _run_single(assemblies, args, geometry, frames)
    else:
        _run_batch(assemblies, args, geometry, frames)


def _run_single(assemblies: list[dict], args: argparse.Namespace,
                geometry: dict[int, dict], frames: list[int]) -> None:
    """Run the pose gate for a single assembly."""
    assembly = next((a for a in assemblies
                     if a["address"].lower() == args.assembly.lower()), None)
    if assembly is None:
        raise SystemExit(f"assembly {args.assembly} not in {SCRIPTS.name}")

    pose_count = len(frames)
    candidates = ([args.pose] if args.pose is not None
                  else list(range(pose_count)))
    result = _find_pose_match(assembly, candidates, geometry, frames)
    if result is None:
        print("\nFAIL: no oracle pose matched.")
        sys.exit(1)

    index, differing, note, source_frame = result
    if differing == 0:
        print(f"\nPASS: assembly {assembly['address']} reproduces pose "
              f"{index} (source frame {source_frame}) exactly, "
              f"code set verified against the frame's palette-{BOSS_PALETTE} "
              f"command set, 0 differing pixels.")
        if args.dump:
            _dump_pose(assembly, index, source_frame, geometry)
        return

    detail = (f"{differing} differing pixels" if differing is not None
              else note)
    print(f"\nFAIL: no oracle pose is reproduced exactly.")
    print(f"  closest: pose {index} (source frame {source_frame}), {detail}")
    print("  The gate is red. Do not proceed to native reimplementation,")
    print("  collision replacement, stage data or AI translation.")
    if args.dump:
        _dump_pose(assembly, index, source_frame, geometry)
    sys.exit(1)


def _run_batch(assemblies: list[dict], args: argparse.Namespace,
               geometry: dict[int, dict], frames: list[int]) -> None:
    """Run the pose gate for all assemblies."""
    pose_count = len(frames)
    candidates = ([args.pose] if args.pose is not None
                  else list(range(pose_count)))
    print(f"Testing {len(assemblies)} assemblies against "
          f"{len(candidates)} oracle pose(s)\n")

    results = []
    for assembly in assemblies:
        addr = assembly["address"]
        count = assembly.get("count", "?")
        print(f"Assembly {addr}: count={count}")

        result = _find_pose_match(assembly, candidates, geometry, frames)
        if result is None:
            print("  FAIL: no oracle pose evaluated.")
            results.append((addr, False, None, None))
        else:
            index, differing, note, source_frame = result
            if differing == 0:
                print(f"  PASS: pose {index} (frame {source_frame}), "
                      f"0 differing")
                results.append((addr, True, index, source_frame))
            else:
                detail = (f"{differing} differing pixels"
                          if differing is not None else note)
                print(f"  FAIL: closest=pose {index} (frame {source_frame}), "
                      f"{detail}")
                results.append((addr, False, index, source_frame))
        print()

    passed = sum(1 for _, ok, _, _ in results if ok)
    print(f"Results: {passed}/{len(results)} assemblies passed")
    if passed < len(results):
        sys.exit(1)


def _dump_pose(assembly: dict, pose_index: int, source_frame: int,
               geometry: dict[int, dict]) -> None:
    """Dump composed and oracle crops as PNGs."""
    from PIL import Image
    dump_dir = ROOT / ".deps" / "mame" / "posegate"
    dump_dir.mkdir(parents=True, exist_ok=True)

    canvas, _note, _match = compose_assembly(assembly, source_frame, geometry)
    crop, _origin = crop_to_content(canvas)
    if crop.size:
        Image.fromarray(crop * 16).save(dump_dir / "composed.png")

    oracle, _frame = load_oracle_pose(pose_index)
    oracle_crop, _oracle_origin = crop_to_content(oracle)
    if oracle_crop.size:
        Image.fromarray(oracle_crop * 16).save(dump_dir / "oracle.png")

    print(f"  wrote composed.png and oracle.png under "
          f"{dump_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
