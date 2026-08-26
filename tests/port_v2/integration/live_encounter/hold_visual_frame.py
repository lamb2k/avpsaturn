#!/usr/bin/env python3
"""Pause pinned Yaba on a real INTEGRATE-04A action frame for visual QA."""
import importlib.util
import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py"
)
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
inventory = json.loads((HERE / "inventory.json").read_text())
parser = argparse.ArgumentParser()
parser.add_argument("--first", type=int, default=180)
parser.add_argument("--last", type=int, default=320)
args = parser.parse_args()
if args.first < 0 or args.last < args.first:
    raise ValueError("invalid visual-frame range")
symbols = tools.symbols(inventory["required_readback_symbols"])
mcp = tools.Mcp("http://127.0.0.1:9640/mcp")
deadline = time.time() + 180.0
while True:
    try:
        mcp.initialize()
        break
    except Exception:
        if time.time() >= deadline:
            raise
        time.sleep(0.1)
while time.time() < deadline:
    ready = mcp.u32(symbols["avsp_diag_runtime_ready"])
    frame = mcp.u32(symbols["avsp_diag_live_frame"])
    if ready == 1 and args.first <= frame <= args.last:
        mcp.call("pause")
        print(f"paused genuine target visual frame {frame}")
        break
    time.sleep(0.005)
else:
    raise TimeoutError("target visual frame was not observed")
