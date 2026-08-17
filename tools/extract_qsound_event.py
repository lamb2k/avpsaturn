#!/usr/bin/env python3
"""Extract one capture-exact QSound event as Saturn-ready signed PCM."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import wave
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_wave(path: Path) -> tuple[wave._wave_params, tuple[int, ...]]:
    with wave.open(str(path), "rb") as source:
        params = source.getparams()
        if params.nchannels != 2 or params.sampwidth != 2 or params.comptype != "NONE":
            raise ValueError(f"{path} must be uncompressed stereo 16-bit PCM")
        payload = source.readframes(params.nframes)
    return params, struct.unpack(f"<{len(payload) // 2}h", payload)


def read_completed_writes(path: Path) -> list[dict[str, int]]:
    writes: list[dict[str, int]] = []
    with path.open("r", newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            if row["port"] != "d002":
                continue
            writes.append(
                {
                    "frame": int(row["frame"]),
                    "pc": int(row["pc"], 16),
                    "register": int(row["register"], 16),
                    "value": int(row["value"], 16),
                }
            )
    return writes


def require_voice_start(
    writes: list[dict[str, int]], voice: int, start_frame: int
) -> dict[str, int]:
    base = voice << 3
    frame_writes = [write for write in writes if write["frame"] == start_frame]
    final_values = {write["register"]: write["value"] for write in frame_writes}
    required = {
        "bank": ((voice - 1) & 15) << 3,
        "address": base + 1,
        "rate": base + 2,
        "phase": base + 3,
        "loop_length": base + 4,
        "end_address": base + 5,
        "volume": base + 6,
    }
    missing = [name for name, register in required.items() if register not in final_values]
    if missing:
        raise ValueError(
            f"QSound voice {voice} has no complete start at frame {start_frame}: "
            + ", ".join(missing)
        )
    return {name: final_values[register] for name, register in required.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--idle-wav", type=Path, required=True)
    parser.add_argument("--action-wav", type=Path, required=True)
    parser.add_argument("--qsound-writes", type=Path, required=True)
    parser.add_argument("--output-pcm", type=Path, required=True)
    parser.add_argument("--output-header", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--voice", type=int, required=True)
    parser.add_argument("--action-frame", type=int, required=True)
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--end-frame", type=int, required=True)
    args = parser.parse_args()

    if not 0 <= args.voice < 16:
        raise ValueError("--voice must be 0..15")
    if not args.action_frame <= args.start_frame < args.end_frame:
        raise ValueError("event frame ordering is invalid")

    idle_params, idle = read_wave(args.idle_wav)
    action_params, action = read_wave(args.action_wav)
    if idle_params != action_params:
        raise ValueError("idle and action WAV formats or lengths differ")

    difference = tuple(action_sample - idle_sample for idle_sample, action_sample in zip(idle, action))
    if any(sample < -32768 or sample > 32767 for sample in difference):
        raise ValueError("differential capture clips signed 16-bit PCM")
    active_frames = [
        index
        for index in range(idle_params.nframes)
        if difference[index * 2] != 0 or difference[index * 2 + 1] != 0
    ]
    if not active_frames:
        raise ValueError("differential capture is silent")
    first_frame = active_frames[0]
    last_frame = active_frames[-1]
    event_samples = difference[first_frame * 2 : (last_frame + 1) * 2]

    # SGL/Jo Engine's 16-bit PCM mode consumes signed, big-endian samples.
    args.output_pcm.parent.mkdir(parents=True, exist_ok=True)
    args.output_pcm.write_bytes(struct.pack(f">{len(event_samples)}h", *event_samples))

    writes = read_completed_writes(args.qsound_writes)
    voice_start = require_voice_start(writes, args.voice, args.start_frame)
    target_volume_register = (args.voice << 3) + 6
    if not any(
        write["frame"] == args.end_frame
        and write["register"] == target_volume_register
        and write["value"] == 0
        for write in writes
    ):
        raise ValueError("capture does not stop the target voice at the declared end frame")

    left = event_samples[0::2]
    right = event_samples[1::2]
    report = {
        "schema": 1,
        "source": "deterministic MAME 0.289 QSound HLE differential capture",
        "action": "predator_warrior_weapon",
        "action_input_frame": args.action_frame,
        "qsound": {
            "voice": args.voice,
            "start_frame": args.start_frame,
            "end_frame": args.end_frame,
            **{name: f"0x{value:04x}" for name, value in voice_start.items()},
        },
        "wave": {
            "channels": idle_params.nchannels,
            "sample_bits": idle_params.sampwidth * 8,
            "sample_rate": idle_params.framerate,
            "first_difference_frame": first_frame,
            "last_difference_frame": last_frame,
            "event_sample_frames": last_frame - first_frame + 1,
            "duration_seconds": (last_frame - first_frame + 1)
            / idle_params.framerate,
            "left_peak": max(abs(sample) for sample in left),
            "right_peak": max(abs(sample) for sample in right),
            "idle_sha256": sha256(args.idle_wav),
            "action_sha256": sha256(args.action_wav),
        },
        "saturn_pcm": {
            "format": "signed-16-bit-big-endian-stereo",
            "sample_rate": idle_params.framerate,
            "bytes": args.output_pcm.stat().st_size,
            "sha256": sha256(args.output_pcm),
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_header.parent.mkdir(parents=True, exist_ok=True)
    args.output_header.write_text(
        "#ifndef GENERATED_AVSP_AUDIO_H\n"
        "#define GENERATED_AVSP_AUDIO_H\n\n"
        '#define AVSP_GUN_PCM_FILE "GUN.PCM"\n'
        '#define AVSP_GUN_PCM_DIRECTORY "AUDIO"\n'
        f"#define AVSP_GUN_PCM_BYTES {args.output_pcm.stat().st_size}\n"
        f"#define AVSP_GUN_PCM_SAMPLE_RATE {idle_params.framerate}\n"
        "#define AVSP_GUN_PCM_CHANNELS 2\n\n"
        "#endif\n",
        encoding="ascii",
    )
    print(
        f"Extracted {report['wave']['duration_seconds']:.6f}s QSound event "
        f"({report['saturn_pcm']['bytes']} bytes, {report['saturn_pcm']['sha256']})"
    )


if __name__ == "__main__":
    main()
