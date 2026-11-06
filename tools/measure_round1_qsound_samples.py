#!/usr/bin/env python3
"""Size the QSound sample set the Round 1 source route really keys on (read-only).

Replays the retained QSound register stream and records, per key-on, the channel's
bank/start/end/loop/pitch. MAME qsound_device layout: registers 8*ch+0 bank (applies
to channel ch+1), +1 start, +2 pitch, +3 phase (key-on when written), +4 loop,
+5 end, +6 volume. Addresses count 8-bit sample bytes.

Reports the union of sample bytes (the size if samples stay 8-bit PCM, which the SCSP
plays natively) and at reduced rate, plus voice concurrency against 32 SCSP slots.
Tier: SOURCE_CAPTURE. Numbers only.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QSOUND_HZ = 24038.0  # pitch 0x1000 plays at about this rate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", default="oracle11_audio_sample_descriptors_a")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    regs = [0] * 256
    # Bank register 8*ch applies to channel ch+1.
    keys, voices = {}, collections.Counter()
    frame_active: dict[int, set] = collections.defaultdict(set)
    frames_seen = writes = keyons = 0
    channel_active = {}
    touched: set = set()
    last_frame = None

    def commit() -> None:
        nonlocal keyons
        for channel in touched:
            bank = regs[(channel - 1) * 8 & 0x7F] & 0x7F
            start, pitch, loop, end = (regs[channel * 8 + n] for n in (1, 2, 4, 5))
            if end == start:
                continue
            keyons += 1
            key = (bank, start, end, loop)
            voices[key] += 1
            keys.setdefault(key, []).append(pitch)
        touched.clear()

    with (ROOT / ".deps/mame" / args.capture / "qsound.tsv").open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="	"):
            if not row["register"]:
                continue
            frame = int(row["frame"])
            if frame != last_frame:
                # Key a voice from the registers after the frame's writes.
                commit()
                frame_active[last_frame] = {c for c in channel_active if channel_active[c]}
                last_frame = frame
            reg, value = int(row["register"], 16), int(row["value"], 16)
            writes += 1
            regs[reg & 255] = value
            if reg >= 0x80:
                continue
            channel, sub = reg >> 3, reg & 7
            if sub in (1, 5):
                touched.add(channel)
            if sub == 6:
                channel_active[channel] = value != 0
    commit()
    intervals: dict[int, list] = collections.defaultdict(list)
    for (bank, start, end, _loop) in keys:
        low, high = min(start, end), max(start, end)
        intervals[bank].append((low, high))
    union = 0
    for bank, rows in intervals.items():
        rows.sort()
        top = -1
        for low, high in rows:
            if low > top:
                union += high - low
                top = high
            elif high > top:
                union += high - top
                top = high
    reduced = 0.0
    rate_histogram = collections.Counter()
    for key, pitches in keys.items():
        peak = max(pitches)
        hz = peak / 0x1000 * QSOUND_HZ
        rate_histogram[int(hz // 4000) * 4000] += 1
        size = abs(key[2] - key[1])
        reduced += size * min(1.0, 11025.0 / max(hz, 1.0))
    result = {"tier": "SOURCE_CAPTURE", "capture": args.capture, "register_writes": writes,
              "key_ons": keyons, "distinct_sample_keys": len(keys),
              "banks_used": sorted(intervals), "union_bytes_8bit": union,
              "scsp_ram_bytes": 524288,
              "union_bytes_if_capped_11025hz_upper_estimate": int(reduced),
              "peak_active_channels_upper_bound": max(len(v) for v in frame_active.values() if v is not None),
              "peak_rate_histogram_hz": dict(sorted(rate_histogram.items())),
              "top_keys_by_size": sorted(
                  ({"bank": k[0], "bytes": abs(k[2] - k[1]), "key_ons": voices[k],
                    "peak_pitch": max(keys[k]), "looped": k[3] != k[2]}
                   for k in keys), key=lambda r: -r["bytes"])[:12],
              "looped_keys": sum(1 for k in keys if k[3] != k[2])}
    args.output.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps(result)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
