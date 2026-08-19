#!/usr/bin/env python3
"""Replay the exact street-alien HIT/KO anchors with script control flow.

This check answers one bounded question: can the animation-record pointer
trajectory be produced by the ROM animation records alone? A GAP result is a
successful measurement, not a failing tool run: it proves that translated
state logic must reproduce external pointer writes before the runtime can use
these anchors without a capture-derived schedule.

The tracked manifest contains addresses, counts, hashes and mismatch metadata
only. It never serializes ROM or capture bytes.
"""

from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "enemy_actions"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
SPANS = ROOT / "data" / "avsp_anim_records.json"
OUTPUT = ROOT / "data" / "avsp_anchor_anim_replay.json"
ACTOR_OFFSET = 0x2000
ANIM_OFFSET = ACTOR_OFFSET + 0x1C
ANCHORS = (("hit", 5191, 5226), ("ko", 5330, 5469))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pointer(frame: int) -> int:
    data = (CAPTURE_ROOT / f"workram_{frame:05d}.bin").read_bytes()
    return struct.unpack_from(">I", data, ANIM_OFFSET)[0]


def record(program: bytes, address: int) -> tuple[int, int, int]:
    if address < 0 or address + 16 > len(program):
        raise ValueError(f"animation record 0x{address:08X} is outside the program image")
    duration, flags = struct.unpack_from(">HH", program, address)
    if flags & 0x8000:
        if address + 20 > len(program):
            raise ValueError(f"jump record 0x{address:08X} is truncated")
        next_address = struct.unpack_from(">I", program, address + 16)[0]
    else:
        next_address = address + 16
    return duration, flags, next_address


def in_spans(address: int, need: int, span_doc: dict) -> bool:
    for span in span_doc["spans"]:
        base = int(span["base"], 16)
        size = int(span["bytes"])
        if base <= address and address - base + need <= size:
            return True
    return False


def replay(program: bytes, start: int, frames: int) -> list[int]:
    address = start
    duration, _, _ = record(program, address)
    hold = duration
    output = []
    for _ in range(frames):
        output.append(address)
        hold -= 1
        while hold <= 0:
            _, _, address = record(program, address)
            duration, _, _ = record(program, address)
            if duration != 0:
                hold = duration
    return output


def main() -> None:
    if not PROGRAM.exists():
        print(f"SKIP: private program image not present: {PROGRAM.relative_to(ROOT)}")
        return
    missing = [
        frame
        for _, start, end in ANCHORS
        for frame in range(start, end + 1)
        if not (CAPTURE_ROOT / f"workram_{frame:05d}.bin").exists()
    ]
    if missing:
        print(f"SKIP: {len(missing)} private anchor work-RAM frames are absent")
        return

    program = PROGRAM.read_bytes()
    span_doc = json.loads(SPANS.read_text(encoding="utf-8"))
    clips = {}
    all_exact = True
    for name, start, end in ANCHORS:
        actual = [read_pointer(frame) for frame in range(start, end + 1)]
        predicted = replay(program, actual[0], len(actual))
        mismatches = [i for i, pair in enumerate(zip(actual, predicted)) if pair[0] != pair[1]]
        observed = sorted(set(actual))
        missing_spans = [address for address in observed if not in_spans(address, 16, span_doc)]
        if missing_spans:
            raise SystemExit(
                f"{name}: observed records missing from shipped spans: "
                + ", ".join(f"0x{address:08X}" for address in missing_spans)
            )
        first = None
        if mismatches:
            index = mismatches[0]
            first = {
                "actual_record": f"0x{actual[index]:08X}",
                "frame": start + index,
                "predicted_record": f"0x{predicted[index]:08X}",
            }
            all_exact = False
        clips[name] = {
            "actual_record_histogram": {
                f"0x{address:08X}": count
                for address, count in sorted(Counter(actual).items())
            },
            "entry_record": f"0x{actual[0]:08X}",
            "first_mismatch": first,
            "frame": {"count": len(actual), "end": end, "start": start},
            "mismatches": len(mismatches),
            "observed_records": [f"0x{address:08X}" for address in observed],
            "observed_records_in_shipped_spans": len(observed),
            "result": "EXACT" if not mismatches else "GAP_EXTERNAL_REPOINT",
        }

    document = {
        "classification": "host animation-record replay check - addresses and counts only",
        "inputs": {
            "animation_spans": {
                "path": "data/avsp_anim_records.json",
                "sha256": sha256(SPANS),
            },
            "capture_route": ".deps/mame/enemy_actions",
            "program_image": {
                "path": ".deps/mame/actorprobe/decrypted_program_2m.bin",
                "sha256": sha256(PROGRAM),
            },
        },
        "method": "seed once from the anchor entry record, render it, then apply only record duration and explicit jump control flow once per frame",
        "result": "EXACT" if all_exact else "GAP_EXTERNAL_REPOINT",
        "runtime_decision": (
            "ROM-driven HIT/KO permitted"
            if all_exact
            else "preserve ADAPTED HIT/KO fallback and count GAP until the class 0x1F state routine's animation-pointer writes are translated"
        ),
        "schema": 1,
        "clips": clips,
    }
    rendered = json.dumps(document, indent=1, sort_keys=True) + "\n"
    OUTPUT.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"anchor animation replay: {document['result']}")
    for name in ("hit", "ko"):
        clip = clips[name]
        print(
            f"  {name}: {clip['frame']['count']} frames, {clip['mismatches']} mismatches, "
            f"first={clip['first_mismatch']}"
        )


if __name__ == "__main__":
    main()
