#!/usr/bin/env python3
"""Drive one bounded debug-rig MCP savestate or framebuffer leg.

The caller owns process launch and teardown.  This helper never reloads a
state after the session has run: a load leg pauses immediately, loads once,
and only then advances through framebuffer_burst.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
TOOLS_SPEC = importlib.util.spec_from_file_location(
    "enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
TOOLS = importlib.util.module_from_spec(TOOLS_SPEC)
assert TOOLS_SPEC.loader is not None
TOOLS_SPEC.loader.exec_module(TOOLS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect(timeout: float):
    mcp = TOOLS.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + timeout
    while True:
        try:
            mcp.initialize()
            return mcp
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.1)


def wait_for_value(mcp, address: int, value: int, timeout: float) -> str:
    address_text = hex(address)
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory",
             address=address_text, write=True, value=hex(value))
    try:
        mcp.call("resume")
        deadline = time.time() + timeout
        stopped = "stopped: false"
        while time.time() < deadline and "stopped: true" not in stopped:
            remaining_ms = max(1, int((deadline - time.time()) * 1000))
            stopped = mcp.call(
                "wait_for_stop", timeout_ms=min(remaining_ms, 20000))
        if "stopped: true" not in stopped:
            raise TimeoutError(f"diagnostic value {value} was not reached")
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=address_text)
    # framebuffer_burst deliberately refuses a CPU-breakpoint halt.  Cross
    # one UI-owned frame boundary, then enter the ordinary paused state that
    # requestFrameStep owns.
    mcp.call("resume")
    mcp.call("pause")
    return stopped


def verify_manifest(path: Path, expected_frames: int) -> dict[str, object]:
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines or lines[0] != "frame\tfile\tsha256":
        raise ValueError("invalid framebuffer_burst manifest header")
    rows = []
    for line in lines[1:]:
        frame_text, name, expected = line.split("\t")
        image = path.parent / name
        actual = sha256(image)
        if actual != expected:
            raise ValueError(f"framebuffer identity drift: {name}")
        rows.append((int(frame_text), expected))
    if len(rows) != expected_frames:
        raise ValueError("framebuffer_burst row count drift")
    if any(right[0] != left[0] + 1 for left, right in zip(rows, rows[1:])):
        raise ValueError("framebuffer_burst is not cadence-1")
    sequence = "\n".join(f"{frame}\t{digest}" for frame, digest in rows)
    return {
        "frame_range": [rows[0][0], rows[-1][0]],
        "frame_count": len(rows),
        "unique_frame_hashes": len({digest for _, digest in rows}),
        "manifest_sha256": sha256(path),
        "canonical_frame_hash_sequence_sha256": hashlib.sha256(
            sequence.encode("ascii")).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("wait-burst", "wait-save", "load-burst"),
                        required=True)
    parser.add_argument("--target", type=int)
    parser.add_argument("--slot", type=int)
    parser.add_argument("--frames", type=int, default=31)
    parser.add_argument("--align-emulator-frame", type=int)
    parser.add_argument("--prefix", default="frame")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args()

    if args.mode.startswith("wait-") and args.target is None:
        parser.error("wait modes require --target")
    if args.mode.endswith("save") and args.slot is None:
        parser.error("wait-save requires --slot")
    if args.mode == "load-burst" and args.slot is None:
        parser.error("load-burst requires --slot")
    if args.mode.endswith("burst") and args.output is None:
        parser.error("burst modes require --output")

    inventory = json.loads((HERE / "inventory.json").read_text())
    symbols = TOOLS.symbols(inventory["required_readback_symbols"])
    mcp = connect(args.timeout)
    result: dict[str, object] = {
        "schema": 1,
        "mode": args.mode,
        "result": "PASS",
        "physical_saturn": "UNRUN",
    }

    if args.mode.startswith("wait-"):
        result["wait"] = {
            "symbol": "avsp_diag_live_frame",
            "address": f"0x{symbols['avsp_diag_live_frame']:08x}",
            "target": args.target,
            "stop": wait_for_value(
                mcp, symbols["avsp_diag_live_frame"], args.target,
                args.timeout),
        }
    else:
        # A load leg must be a fresh process.  Pause before the sole load and
        # do not resume independently; framebuffer_burst owns all advancement.
        mcp.call("pause")
        result["load_state"] = mcp.call("load_state", slot=args.slot)

    if args.mode == "wait-save":
        result["save_state"] = mcp.call("save_state", slot=args.slot)
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        if args.align_emulator_frame is not None:
            status = mcp.call("debug_status")
            match = re.search(r"^frame:\s+(\d+)$", status, re.MULTILINE)
            if match is None:
                raise RuntimeError("debug_status omitted emulator frame")
            current_frame = int(match.group(1))
            align_count = args.align_emulator_frame - current_frame
            if align_count < 0:
                raise RuntimeError(
                    "emulator already passed requested alignment frame: "
                    f"{current_frame} > {args.align_emulator_frame}")
            if align_count:
                align_output = output.parent / f"{output.name}-alignment"
                align_output.mkdir(parents=True, exist_ok=True)
                align_response = mcp.call(
                    "framebuffer_burst", directory=str(align_output),
                    frames=align_count, prefix="alignment")
                result["alignment_burst"] = align_response
                result["alignment_manifest"] = verify_manifest(
                    align_output / "manifest.tsv", align_count)
        burst_response = mcp.call(
            "framebuffer_burst", directory=str(output), frames=args.frames,
            prefix=args.prefix)
        result["framebuffer_burst"] = burst_response
        manifest_path = output / "manifest.tsv"
        if not manifest_path.is_file():
            raise RuntimeError(
                "framebuffer_burst did not create manifest.tsv: "
                f"{burst_response}")
        result["manifest"] = verify_manifest(
            manifest_path, args.frames)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
