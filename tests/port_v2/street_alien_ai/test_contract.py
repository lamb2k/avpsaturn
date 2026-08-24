#!/usr/bin/env python3
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(value, message):
    if not value:
        raise AssertionError(message)


contract = json.loads((HERE / "contract.json").read_text())
source = ROOT / "src/port_v2/gameplay/street_alien_ai/street_alien_ai.c"
header = ROOT / "src/port_v2/gameplay/street_alien_ai/street_alien_ai.h"
compat_header = ROOT / "tests/port_v2/street_alien_ai_bench/street_alien_ai_bench.h"
compat_source = ROOT / "tests/port_v2/street_alien_ai_bench/street_alien_ai_bench.c"
body = source.read_text()
require(source.is_file() and header.is_file(), "production class-1F interface missing")
require(not re.search(r"\bjo_|\bsl[A-Z]|spr[A-Z]|VDP1|VDP2", body), "production AI has Saturn/render dependency")
require("../../../src/port_v2/gameplay/street_alien_ai/street_alien_ai.h" in compat_header.read_text(), "salvage compatibility include drifted")
require("avsp_alien_ai_step" not in compat_source.read_text(), "compatibility translation unit owns AI behavior")
require(contract["fallback_present"] is False and contract["adapter_deletion_condition"].startswith("delete with SALVAGE-11"), "fallback or permanent adapter introduced")
translated = subprocess.run(["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")], check=True, capture_output=True, text=True).stdout.strip()
command = (f"cd '{translated}' && mkdir -p build/port_v2/street_alien_ai && "
           "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
           "src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
           "tests/port_v2/street_alien_ai_bench/street_alien_ai_test.c "
           "-Itests/port_v2/street_alien_ai_bench "
           "-o build/port_v2/street_alien_ai/ai_test && "
           "./build/port_v2/street_alien_ai/ai_test")
subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)
print("PROMOTE-11 production street alien AI contract: PASS")
