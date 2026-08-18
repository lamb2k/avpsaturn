"""Pixel-exact gate: does the ROM assembly for each archive pose reproduce the
archive cel?

For each of the 29 archive poses we recover, purely from captured work RAM,
the ROM assembly the game actually displayed at the pose's source frame
(``avsp_boss_source_frames[pose]`` -> trace ``frames[]`` -> assembly).  That
assembly is composed from ROM tiles + ROM layout words (selector 6/10/2) via
``verify_pose_gate.compose_rom_pose`` and compared pixel-exactly against the
decoded archive cel (``verify_pose_gate.load_oracle_pose``).  Both facings are
tried per pose; a pass is 0 differing pixels on content crops.

Read-only: it prints a per-pose table and exits non-zero on any failure.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decode_avsp_animation_scripts as das  # noqa: E402
import verify_pose_gate as vp  # noqa: E402
import extract_avspu_stage1 as avsp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / ".deps" / "mame" / "actorprobe"
ROM = (PROBE / "rom_window_13c_13f.bin").read_bytes()
BASE = 0x13C000
OFFSET_DATA = (PROBE / "offset_program.bin").read_bytes()
LAYOUT_DATA = (PROBE / "offset_full_program.bin").read_bytes()
TRACE = ROOT / "data" / "boss_play_sequence.json"
BOSS_HEADER = ROOT / "generated" / "avsp_boss_animation.h"

CLIP_NAMES = ["idle", "leap", "walk", "attack", "hit", "ko"]


def header_table(name: str) -> list[int]:
    text = BOSS_HEADER.read_text(encoding="ascii", errors="ignore")
    match = re.search(name + r"\[[^\]]*\]\s*=\s*\{(.*?)\};", text, re.S)
    if not match:
        raise SystemExit(f"table {name} not found in {BOSS_HEADER.name}")
    return [int(v.strip(), 0) for v in match.group(1).split(",")
            if v.strip()]


OFFSET_WINDOW_BASE = 0x1E0000


def captured_code_set(geometry: dict, frame: int):
    spec = geometry.get(frame)
    if spec is None:
        return None
    entries = avsp.decode_object_entries(vp.read_words(spec["path"]))
    by_offset = {en["offset"]: en for en in entries}
    codes = set()
    for off in spec["offsets"]:
        en = by_offset.get(off)
        if en is None:
            continue
        y = (en["y"] & ~0x3FF) | (
            ((en["y"] & 0x3FF) + spec["shift_y"]) & 0x3FF)
        codes.add((en["code"] + ((y & 0x6000) << 3)) & 0xFFFF)
    return codes


def main() -> None:
    vp._GFX = (ROOT / ".deps" / "mame" / "captures" /
               "gfx_region.bin").read_bytes()
    trace = json.loads(TRACE.read_text(encoding="ascii"))
    frame_to_asm = {f["frame"]: f["assembly"] for f in trace["frames"]}
    source_frames = header_table("avsp_boss_source_frames")
    n_poses = len(source_frames)

    assemblies = {}
    for addr in sorted(frame_to_asm.values()):
        assemblies[addr] = das.decode_assembly(
            ROM, BASE, addr, OFFSET_DATA, LAYOUT_DATA,
            offset_window_base=OFFSET_WINDOW_BASE)

    def code_set(addr):
        d = assemblies[addr]
        if d.get("status") != "decoded_structure":
            return None
        return {int(e["code"], 16) for e in d["entries"][:d["count"]]}

    asm_codes = {a: code_set(a) for a in assemblies}
    geometry = vp.load_frame_geometry()

    print(f"{'pose':>4} {'frame':>6} {'assembly':>10} {'sel':>3} "
          f"{'facing':>6} {'diff':>5}  status")
    failures = 0
    pose_asm = {}
    for pose in range(n_poses):
        frame = source_frames[pose]
        ptr_asm = frame_to_asm.get(frame)
        if ptr_asm is None:
            print(f"{pose:>4} {frame:>6} {'-':>10} {'-':>3} "
                  f"{'-':>6} {'-':>5}  NO TRACE (idle path)")
            continue
        cap = captured_code_set(geometry, frame)
        matches = [a for a in assemblies if asm_codes.get(a) == cap]
        if ptr_asm in matches:
            asm_addr, how = ptr_asm, "ptr"
        elif matches:
            asm_addr, how = matches[0], "codes"
        else:
            asm_addr, how = ptr_asm, "ptr!"
        assembly = assemblies[asm_addr]
        if assembly.get("status") != "decoded_structure":
            print(f"{pose:>4} {frame:>6} 0x{asm_addr:06x} "
                  f"{assembly.get('selector','?'):>3} "
                  f"{'-':>6} {'-':>5}  DECODE FAIL {assembly.get('status')}")
            failures += 1
            continue
        sel = assembly["selector"]
        best = None
        for facing in (True, False):
            canvas = vp.compose_rom_pose(assembly, facing)
            crop, _ = vp.crop_to_content(canvas)
            oracle, _ = vp.load_oracle_pose(pose)
            ocrop, _ = vp.crop_to_content(oracle)
            diff = (None if crop.shape != ocrop.shape
                    else int(np.count_nonzero(crop != ocrop)))
            if best is None or (diff is not None and (
                    best[1] is None or diff < best[1])):
                best = (facing, diff)
        facing, diff = best
        if diff == 0:
            status = "PASS"
        elif diff is None:
            status = "FAIL shape"
        else:
            status = "FAIL"
        if diff != 0:
            failures += 1
        pose_asm[pose] = asm_addr
        print(f"{pose:>4} {frame:>6} 0x{asm_addr:06x} {sel:>3} "
              f"{int(facing):>6} {str(diff):>5}  {status} ({how})")

    print(f"\nPoses mapped: {len(pose_asm)}  (failures: {failures})")
    distinct = sorted(set(pose_asm.values()))
    print(f"Distinct pose assemblies: {len(distinct)}")
    for a in distinct:
        print(f"  0x{a:06x} sel={assemblies[a]['selector']}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
