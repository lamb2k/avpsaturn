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
spec = importlib.util.spec_from_file_location(
    "button1_capture", HERE / "capture_button1_cadence.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if args.first < 0 or args.last < args.first:
        raise ValueError("invalid Coffee Shop WGC frame range")

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
    mcp.call("set_debug_option", cpu_core="interpreter")

    for frame in range(args.first, args.last + 1):
        diagnostic_frame = frame - SOURCE_VISIBLE_FRAME_AT_DIAGNOSTIC_ZERO
        if diagnostic_frame < 0:
            raise RuntimeError(
                f"source frame {frame} predates the native Coffee Shop ledger")
        capture.wait_frame(mcp, symbols, diagnostic_frame, args.timeout)
        print(f"WGC_READY {frame}", flush=True)
        response = input().strip()
        if response != f"CAPTURED {frame}":
            raise RuntimeError(
                f"capture acknowledgement drift at {frame}: {response!r}")
    print("WGC_SEQUENCE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
