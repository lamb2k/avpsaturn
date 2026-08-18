"""ROM layout words vs captured object geometry.

Prepares the next gate milestone: reproduce object positions from the ROM
layout table instead of the recorded RAM geometry.

For each selector-6 assembly, this tool finds the oracle pose whose
frame's palette-27 command set carries the assembly's tile codes, pairs
each ROM layout word with the command that has the same code, and prints
the object's captured screen geometry (left/right/top/bottom) next to the
signed layout words and a few derived differences:

* ``dB = screen_bottom - layout_y_signed`` — if the layout Y word is a
  pixel offset of the object's bottom edge from a per-frame anchor, this
  is identical for every entry of the pose.
* ``dL / dC / dR = screen_left|centre|right - layout_x_signed`` — the
  X relationship is not yet known; the table keeps the candidates
  visible until it is cracked.

Screen coordinates use the same 1024-ring unwrapped space as the oracle
composer (verify_pose_gate.compose_assembly). No pixels are decoded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402
import verify_pose_gate as gate  # noqa: E402


def _spread(values: list[int]) -> str:
    return "const" if len(set(values)) == 1 else f"{min(values)}..{max(values)}"


def main() -> None:
    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    geometry = gate.load_frame_geometry()
    frames = gate.header_table("avsp_boss_source_frames")

    for assembly in scripts.get("assemblies", []):
        addr = assembly["address"]
        codes = {int(e["code"], 16)
                 for e in assembly["entries"][:assembly.get("count", 0)]}
        match = None
        for pose_index, frame in enumerate(frames):
            spec = geometry.get(frame)
            if spec is None:
                continue
            entries = avsp.decode_object_entries(gate.read_words(spec["path"]))
            by_offset = {e["offset"]: e for e in entries}
            if any(o not in by_offset for o in spec["offsets"]):
                continue
            run_codes = set()
            commands = []
            for offset in spec["offsets"]:
                entry = by_offset[offset]
                x = ((entry["x"] & 0x3FF) + spec["shift_x"]) & 0x3FF
                y = ((entry["y"] & 0x3FF) + spec["shift_y"]) & 0x3FF
                run_codes.add(entry["code"] & 0xFFFF)
                commands.append((entry["code"] & 0xFFFF,
                                 x - avsp.VISIBLE_LEFT,
                                 y - avsp.VISIBLE_TOP,
                                 entry["width"] // 16, entry["height"] // 16))
            if codes == run_codes:
                match = (pose_index, frame, spec, commands)
                break
        if match is None:
            print(f"{addr}: no pose with a matching code set")
            continue
        pose_index, frame, spec, commands = match
        by_code = {c: (x, y, nx, ny) for c, x, y, nx, ny in commands}
        print(f"{addr}: pose {pose_index} (frame {frame}) "
              f"pivot=({spec['pivot_x']},{spec['pivot_bottom']}) "
              f"origin=({assembly.get('origin_x')},{assembly.get('origin_y')})")
        d_bottoms, d_tops, d_lefts, d_centres, d_rights = [], [], [], [], []
        for entry in assembly["entries"][:assembly.get("count", 0)]:
            code = int(entry["code"], 16)
            lx = entry["layout_x_signed"]
            ly = entry["layout_y_signed"]
            x, y, nx, ny = by_code[code]
            left, top = x, y
            right, bottom = x + nx * 16, y + ny * 16
            centre = left + nx * 8
            d_bottom, d_top = bottom - ly, top - ly
            d_left, d_centre, d_right = left - lx, centre - lx, right - lx
            d_bottoms.append(d_bottom)
            d_tops.append(d_top)
            d_lefts.append(d_left)
            d_centres.append(d_centre)
            d_rights.append(d_right)
            print(f"  code=0x{code:04x} L={left:4d} R={right:4d} "
                  f"T={top:4d} B={bottom:4d}  "
                  f"lx={lx:5d} ly={ly:5d}  "
                  f"dB={d_bottom:5d} dT={d_top:5d}  "
                  f"dL={d_left:5d} dC={d_centre:5d} dR={d_right:5d}")
        print(f"  spread: dB={_spread(d_bottoms)} dT={_spread(d_tops)} "
              f"dL={_spread(d_lefts)} dC={_spread(d_centres)} "
              f"dR={_spread(d_rights)}")
        print()


if __name__ == "__main__":
    main()
