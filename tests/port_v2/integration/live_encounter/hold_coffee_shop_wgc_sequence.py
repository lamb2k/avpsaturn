#!/usr/bin/env python3
"""Hold exact Coffee Shop diagnostic frames for window-only WGC evidence."""

import argparse
import importlib.util
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SOURCE_VISIBLE_FRAME_AT_DIAGNOSTIC_ZERO = 2041
INTERPRETER_APPROACH_FRAMES = 60
spec = importlib.util.spec_from_file_location(
    "button1_capture", HERE / "capture_button1_cadence.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def wait_frame(mcp, symbols, target, timeout):
    """Reach an exact frame without running the entire route in interpreter."""
    deadline = time.time() + timeout
    address = symbols["avsp_diag_live_frame"]
    mcp.call("pause")
    current = capture.tools.signed32(mcp.u32(address))
    if target - current > INTERPRETER_APPROACH_FRAMES:
        mcp.call("set_debug_option", cpu_core="dynarec")
        mcp.call("resume")
        while time.time() < deadline:
            current = capture.tools.signed32(mcp.u32(address))
            if current >= target - INTERPRETER_APPROACH_FRAMES:
                break
            time.sleep(0.002)
        mcp.call("pause")
    mcp.call("set_debug_option", cpu_core="interpreter")
    remaining = max(1.0, deadline - time.time())
    capture.wait_frame(mcp, symbols, target, remaining)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=int)
    parser.add_argument("--last", type=int)
    parser.add_argument("--frames", type=int, nargs="+")
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if args.frames:
        frames = tuple(args.frames)
        if args.first is not None or args.last is not None:
            raise ValueError("choose an explicit frame list or a frame range")
    else:
        if args.first is None or args.last is None:
            raise ValueError("Coffee Shop WGC frame range is required")
        if args.first < 0 or args.last < args.first:
            raise ValueError("invalid Coffee Shop WGC frame range")
        frames = range(args.first, args.last + 1)
    if not frames or any(frame < 0 for frame in frames) or any(
            right <= left for left, right in zip(frames, frames[1:])):
        raise ValueError("Coffee Shop WGC frames must be increasing")

    inventory = json.loads((HERE / "inventory.json").read_text())
    symbols = capture.tools.symbols(inventory["required_readback_symbols"])
    mcp = capture.tools.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.1)

    for frame in frames:
        diagnostic_frame = frame - SOURCE_VISIBLE_FRAME_AT_DIAGNOSTIC_ZERO
        if diagnostic_frame < 0:
            raise RuntimeError(
                f"source frame {frame} predates the native Coffee Shop ledger")
        wait_frame(mcp, symbols, diagnostic_frame, args.timeout)
        print(f"WGC_READY {frame}", flush=True)
        response = input().strip()
        if response != f"CAPTURED {frame}":
            raise RuntimeError(
                f"capture acknowledgement drift at {frame}: {response!r}")
    print("WGC_SEQUENCE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
