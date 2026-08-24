#!/usr/bin/env python3
import hashlib
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
require(hashlib.sha256((ROOT / "data/oracle05_street_alien_ai.json").read_bytes()).hexdigest() == contract["oracle05_sha256"], "ORACLE-05 identity drift")
require(hashlib.sha256((ROOT / "data/oracle06_round1_encounter.json").read_bytes()).hexdigest() == contract["oracle06_sha256"], "ORACLE-06 identity drift")
core = (HERE / "street_alien_ai_bench.c").read_text()
require(not re.search(r"\bjo_|\bsl[A-Z]|spr[A-Z]|VDP1|VDP2", core), "AI core has Saturn/render dependency")
require("avsp_alien_ai_rng_step" in core and "target->x" in core and
        "runtime->contact_damage" in core, "bounded AI authorities missing")
require(not re.search(r"3982|4214|4252|4253|4301|4372|5190|5470", core), "AI core embeds oracle absolute frames")
translated = subprocess.run(["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")], check=True, capture_output=True, text=True).stdout.strip()
command = (f"cd '{translated}' && mkdir -p build/port_v2/street_alien_ai_bench && "
           "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
           "tests/port_v2/street_alien_ai_bench/street_alien_ai_bench.c "
           "tests/port_v2/street_alien_ai_bench/street_alien_ai_test.c "
           "-o build/port_v2/street_alien_ai_bench/ai_test && "
           "./build/port_v2/street_alien_ai_bench/ai_test")
subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)
print("SALVAGE-11 portable contract and provenance: PASS")
