#!/usr/bin/env python3
"""Print the current playable-slice debugger state for bounded diagnosis."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "enemy_readback", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
inventory = json.loads((HERE / "inventory.json").read_text())
required = inventory["required_readback_symbols"]
all_symbols = tools.symbols(required)
symbols = {name: all_symbols[name] for name in required}
mcp = tools.Mcp("http://127.0.0.1:9640/mcp")
mcp.initialize()
mcp.call("pause")
result = {name: tools.signed32(mcp.u32(address))
          for name, address in symbols.items()}
print(json.dumps(result, indent=2, sort_keys=True))
if len(sys.argv) > 1 and sys.argv[1] == "--resume":
    mcp.call("resume")
