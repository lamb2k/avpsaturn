"""Reference interpreter for the AvP CPS2 animation scripts.

Walks the raw script bytes (rom window 0x13C000-0x13F000) exactly the way the
SH-2 animation updater does, so the C interpreter (step 3) can be ported and
host-tested against a known-correct model:

* read a 16-byte pose record at the current address:
    +0 duration (u16)
    +2 flags   (u16): bit 15 = jump/loop marker; bits 14-8 = 7-bit sequence
       index; bits 7-0 = parameter byte
    +4 assembly pointer (u32, absolute ROM address of the selector-6 assembly)
    +8..+15 tail (unlabeled; left unconsumed by the interpreter)
* hold that pose for ``duration`` frames, then:
    - if flags & 0x8000 (negative): jump to the u32 stored at address+16;
    - otherwise: advance to address+16.

The eight-byte tail and the interaction-table consumers of its first two bytes
are intentionally NOT interpreted here; they are proven separately (step 1's
pose/position gates) before any consumer is added.

Run as a script to self-test against ``data/avsp_animation_scripts.json``:
for every decoded program the interpreter must reproduce the exact
per-frame (assembly, duration) sequence, including the loop-back.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_WINDOW = ROOT / ".deps" / "mame" / "actorprobe" / "rom_window_13c_13f.bin"
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"
BASE = 0x13C000


def _u16(data: bytes, off: int) -> int:
    return struct.unpack_from(">H", data, off)[0]


def _u32(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def read_pose(data: bytes, base: int, addr: int):
    """Decode one 16-byte pose record; returns the fields or None if out of range."""
    off = addr - base
    if off < 0 or off + 16 > len(data):
        return None
    duration = _u16(data, off)
    flags = _u16(data, off + 2)
    assembly = _u32(data, off + 4)
    return {
        "address": addr,
        "duration": duration,
        "flags": flags,
        "flip_flag": bool(flags & 0x8000),
        "sequence_index": (flags >> 8) & 0x7F,
        "param_byte": flags & 0xFF,
        "assembly": assembly,
        "tail": data[off + 8:off + 16],
    }


def next_address(data: bytes, base: int, pose) -> int:
    """Where the updater points after ``pose``'s duration has run out."""
    if pose["flags"] & 0x8000:
        off = pose["address"] - base + 16
        if off + 4 <= len(data):
            target = _u32(data, off)
            if BASE <= target < BASE + len(data):
                return target
    return pose["address"] + 16


def run(data: bytes, base: int, start: int, frames: int):
    """Interpret ``frames`` frames of animation beginning at ``start``.

    Returns a list of one dict per rendered frame with the pose that was shown.
    """
    out = []
    addr = start
    for _ in range(frames):
        pose = read_pose(data, base, addr)
        if pose is None:
            break
        # A pose with duration 0 still consumes the pointer slot; hold nothing.
        if pose["duration"] > 0:
            out.append({
                "address": pose["address"],
                "assembly": pose["assembly"],
                "sequence_index": pose["sequence_index"],
                "param_byte": pose["param_byte"],
                "flip_flag": pose["flip_flag"],
            })
            addr = next_address(data, base, pose)
    return out


def _cycle(data: bytes, base: int, start: int, cap: int = 1024):
    """Walk a full loop from ``start`` and return the ordered pose records
    (one entry per distinct record address) plus the jump pointer used to
    close the loop.  Stops when the walk returns to ``start``."""
    records = []
    addr = start
    for _ in range(cap):
        pose = read_pose(data, base, addr)
        if pose is None:
            break
        records.append(pose)
        nxt = next_address(data, base, pose)
        if nxt == start:
            return records
        addr = nxt
    return records


def self_test() -> int:
    if not ROM_WINDOW.is_file():
        print(f"missing {ROM_WINDOW}", file=sys.stderr)
        return 2
    data = ROM_WINDOW.read_bytes()
    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    failures = 0
    for prog in scripts.get("programs", []):
        start = int(prog["start"], 16)
        json_records = [r for r in prog["records"] if r["kind"] == "pose"]
        interp = _cycle(data, BASE, start)
        # Compare assembly order, durations, and the loop-back.
        ok = len(interp) == len(json_records)
        details = []
        if ok:
            for a, b in zip(interp, json_records):
                ja = int(b["assembly"], 16)
                if a["assembly"] != ja or a["duration"] != b["duration"] \
                        or a["sequence_index"] != b["sequence_index"] \
                        or a["param_byte"] != b["param_byte"]:
                    ok = False
                    details.append(f"  {a['address']:06x} "
                                   f"(asm 0x{a['assembly']:06x} d{a['duration']}) "
                                   f"!= json {b['address']} "
                                   f"(asm {b['assembly']} d{b['duration']})")
                    break
        # The loop must close: last record's next_address == start.
        if ok and interp:
            if next_address(data, BASE, interp[-1]) != start:
                ok = False
                details.append(f"  loop does not close: next={interp[-1]['address'] + 16:#06x} != start {start:#06x}")
        total = sum(p["duration"] for p in interp)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{status}] {prog['start']}  {len(interp)} poses, cycle={total}f, "
              f"{len(interp[0]['tail']) if interp else 0}-byte tail unconsumed")
        for d in details:
            print(d)
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="0x13cc18",
                        help="hex start address of the program to interpret")
    parser.add_argument("--frames", type=int, default=48,
                        help="number of frames to render")
    parser.add_argument("--self-test", action="store_true",
                        help="verify every decoded program loops correctly")
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(self_test())

    data = ROM_WINDOW.read_bytes()
    start = int(args.start, 16)
    frames = run(data, BASE, start, args.frames)
    print(f"Interpreting {len(frames)} frames from {start:#06x}")
    prev = None
    for i, f in enumerate(frames):
        mark = "" if f["assembly"] == prev else "  <-- new pose"
        prev = f["assembly"]
        print(f"frame {i:>3}  asm 0x{f['assembly']:06x}  seq {f['sequence_index']} "
              f"param {f['param_byte']}{mark}")


if __name__ == "__main__":
    main()
