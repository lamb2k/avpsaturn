#!/usr/bin/env python3
"""Pause the pinned QA-12 image on or immediately after a requested frame."""
import argparse
import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIVE = ROOT / "tests/port_v2/integration/live_encounter"
spec = importlib.util.spec_from_file_location(
    "enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
symbols = tools.symbols(json.loads((LIVE / "inventory.json").read_text())[
    "required_readback_symbols"])
parser = argparse.ArgumentParser()
parser.add_argument("--frame", type=int, required=True)
parser.add_argument("--timeout", type=float, default=180.0)
parser.add_argument("--resume", action="store_true",
                    help="resume an emulator already paused at an earlier frame")
args = parser.parse_args()
mcp = tools.Mcp("http://127.0.0.1:9640/mcp")
deadline = time.time() + args.timeout
while True:
    try:
        mcp.initialize()
        mcp.call("set_debug_option", cpu_core="interpreter")
        break
    except Exception:
        if time.time() >= deadline:
            raise
        time.sleep(0.1)
if args.resume:
    mcp.call("resume")
while time.time() < deadline:
    try:
        ready = mcp.u32(symbols["avsp_diag_runtime_ready"])
        frame = mcp.u32(symbols["avsp_diag_live_frame"])
        if ready == 1 and frame >= args.frame:
            mcp.call("pause")
            print(frame)
            break
    except Exception:
        time.sleep(0.1)
        continue
    time.sleep(0.005)
else:
    raise TimeoutError(f"QA-12 frame {args.frame} was not observed")
