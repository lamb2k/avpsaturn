"""Recover the Chrysalis boss play sequence straight from captured work RAM.

Each ``workram_NNNNN.bin`` dump (covering ``0xff8000..0xffffff``) contains the
boss actor struct at ``0xffa3c0``.  Its current animation-script record pointer
is ``w1c:w1e`` (struct words at ``0x1c``/``0x1e``).  Every record is 16 bytes:
``u16 duration`` @0, ``u16 flags`` @2, ``u32 assembly`` @4.  Reading that pointer
for every captured frame gives the *ground-truth* ordered sequence of assemblies
the game actually displays -- no need to reconstruct the ROM loop/jump structure
(which is what the static program decoder overruns on for the linear action/KO
programs).

The tool:
  * decodes the record for every frame,
  * cross-checks the held-assembly run length against the record ``duration``
    (sanity: the two should agree for non-hold records),
  * compresses consecutive identical assemblies into runs,
  * decodes every referenced selector-6 assembly (tile command list),
  * dumps the full trace + runs + assemblies to a JSON for the generator.

Read-only: it emits a JSON ledger and prints a short summary.
"""
from __future__ import annotations

import glob
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decode_avsp_animation_scripts as das  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / ".deps" / "mame" / "actorprobe"
ROM = PROBE / "rom_window_13c_13f.bin"
BASE = 0x13C000
W1C_OFFSET = 0x23dc
W1E_OFFSET = 0x23de
ASM_FIRST = 0x13DE00
ASM_LAST = 0x13F000

CAPTURES = [
    ("action", ROOT / ".deps" / "mame" / "boss_actions"),
    ("ko", ROOT / ".deps" / "mame" / "boss_ko"),
]


def read_record(data: bytes, pointer: int) -> dict | None:
    offset = pointer - BASE
    if offset < 0 or offset + 8 > len(data):
        return None
    duration = struct.unpack_from(">H", data, offset)[0]
    flags = struct.unpack_from(">H", data, offset + 2)[0]
    assembly = struct.unpack_from(">I", data, offset + 4)[0]
    return {"duration": duration, "flags": flags, "assembly": assembly}


def read_pointer(path: Path) -> int | None:
    with path.open("rb") as fh:
        fh.seek(W1C_OFFSET)
        hi = struct.unpack_from(">H", fh.read(2))[0]
        fh.seek(W1E_OFFSET)
        lo = struct.unpack_from(">H", fh.read(2))[0]
    return (hi << 16) | lo


def read_samples(path: Path) -> dict[int, dict[str, int]]:
    samples: dict[int, dict[str, int]] = {}
    if not path.exists():
        return samples
    lines = path.read_text(encoding="ascii").splitlines()
    header = lines[0].split("\t")
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(header):
            continue
        row = dict(zip(header, parts))
        try:
            frame = int(row["frame"])
        except (KeyError, ValueError):
            continue
        samples[frame] = {
            key: int(row[key], 10) for key in
            ("active", "action", "state", "substate", "animation")
            if key in row
        }
    return samples


def main() -> None:
    data = ROM.read_bytes()
    offset_data = (PROBE / "offset_program.bin").read_bytes()
    layout_data = (PROBE / "offset_full_program.bin").read_bytes()

    frames: dict[int, dict] = {}
    for cname, croot in CAPTURES:
        samples = read_samples(croot / "samples.tsv")
        for path in glob.glob(str(croot / "workram_*.bin")):
            p = Path(path)
            frame = int(p.name[len("workram_"):-len(".bin")])
            if frame in frames:
                continue  # dedupe the action/ko overlap; keep first-seen
            pointer = read_pointer(p)
            if pointer is None:
                continue
            rec = read_record(data, pointer)
            if rec is None:
                continue
            frames[frame] = {
                "frame": frame,
                "capture": cname,
                "pointer": pointer,
                "duration": rec["duration"],
                "flags": rec["flags"],
                "assembly": rec["assembly"],
                **{k: v for k, v in samples.get(frame, {}).items()},
            }

    ordered = [frames[f] for f in sorted(frames)]
    print(f"Traced {len(ordered)} frames: "
          f"{ordered[0]['frame']}..{ordered[-1]['frame']}")

    # --- Compress into runs of identical assembly. ---------------------------
    runs: list[dict] = []
    for rec in ordered:
        if runs and runs[-1]["assembly"] == rec["assembly"]:
            runs[-1]["end_frame"] = rec["frame"]
            runs[-1]["run_len"] += 1
        else:
            runs.append({
                "assembly": rec["assembly"],
                "record": rec["pointer"],
                "claimed_duration": rec["duration"],
                "flags": rec["flags"],
                "start_frame": rec["frame"],
                "end_frame": rec["frame"],
                "run_len": 1,
                "action": rec.get("action"),
                "state": rec.get("state"),
                "substate": rec.get("substate"),
            })

    # --- Sanity: run_len should match claimed_duration for non-hold records. -
    mismatches = 0
    for run in runs:
        if run["claimed_duration"] < 0x8000 and \
                run["run_len"] != run["claimed_duration"]:
            mismatches += 1
            if mismatches <= 8:
                print(f"  runlen!=duration: 0x{run['assembly']:06x} "
                      f"frames {run['start_frame']}..{run['end_frame']} "
                      f"run_len={run['run_len']} "
                      f"claimed={run['claimed_duration']} "
                      f"action={run['action']}")
    print(f"Runs: {len(runs)}  (run_len!=claimed_duration: {mismatches})")

    # --- Distinct assemblies, decode each. ----------------------------------
    assembly_set = sorted({run["assembly"] for run in runs})
    print(f"Distinct assemblies in the play sequence: {len(assembly_set)}")
    in_range = [a for a in assembly_set if ASM_FIRST <= a < ASM_LAST]
    out_range = [a for a in assembly_set if not (ASM_FIRST <= a < ASM_LAST)]
    print(f"  in [0x{ASM_FIRST:06x},0x{ASM_LAST:06x}): {len(in_range)}")
    if out_range:
        print(f"  OUT OF RANGE ({len(out_range)}): "
              f"{[hex(a) for a in out_range]}")
    assemblies = [das.decode_assembly(data, BASE, a, offset_data, layout_data)
                  for a in assembly_set]
    bad = [a["address"] for a in assemblies
           if a.get("status") not in ("decoded_structure",)]
    if bad:
        print(f"  assemblies not cleanly decoded: {bad}")

    # --- Compact run view grouped by (action, state, substate). -------------
    print("\nPlay-sequence runs (assembly x claimed_duration, "
          "action/state/substate):")
    for run in runs:
        hold = "HOLD" if run["claimed_duration"] >= 0x8000 else ""
        print(f"  {run['start_frame']:5d}..{run['end_frame']:<5d} "
              f"asm=0x{run['assembly']:06x} d={run['claimed_duration']:5d} "
              f"(run {run['run_len']:3d}) a/s/ss="
              f"{run['action']}/{run['state']}/{run['substate']} {hold}")

    out = {
        "schema": 1,
        "note": ("ground-truth boss play sequence from captured work-RAM "
                 "w1c:w1e record pointers; ROM assembly refs, no archives"),
        "window_base": f"0x{BASE:06x}",
        "assembly_range": [f"0x{ASM_FIRST:06x}", f"0x{ASM_LAST:06x}"],
        "frame_count": len(ordered),
        "frames": ordered,
        "runs": runs,
        "assemblies": assemblies,
    }
    dest = ROOT / "data" / "boss_play_sequence.json"
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="ascii")
    print(f"\nWrote {dest}")


if __name__ == "__main__":
    main()
