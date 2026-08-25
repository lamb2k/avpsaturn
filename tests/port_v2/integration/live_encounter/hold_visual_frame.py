#!/usr/bin/env python3
"""Pause pinned Yaba on a real INTEGRATE-04A action frame for visual QA."""
import importlib.util
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
    if ready == 1 and 180 <= frame <= 320:
        mcp.call("pause")
        print(f"paused genuine INTEGRATE-04A visual frame {frame}")
        break
    time.sleep(0.005)
else:
    raise TimeoutError("INTEGRATE-04A action frame was not observed")
