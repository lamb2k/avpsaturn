#!/usr/bin/env python3
"""Strict host compile and real stable-entry mutations for REIMPLEMENT-13."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "data/spec02_round1_executable_contract.json"
EXPECTED = "6cb1208a190b4977f2f73eb48b181fda08063266e45f1d8efcbc47b7fdc264a4"
assert hashlib.sha256(SPEC.read_bytes()).hexdigest() == EXPECTED
assert json.loads(SPEC.read_text())["status"] == "ACCEPTED"
source = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text()
header = (ROOT / "src/port_v2/gameplay/round1/round1.h").read_text()

def wsl(path):
    return subprocess.run(["wsl.exe", "wslpath", "-a", str(path).replace("\\", "/")],
                          check=True, capture_output=True, text=True).stdout.strip()

def run(body, header_body, passes):
    with tempfile.TemporaryDirectory(prefix="round1-entry-") as name:
        temp = Path(name); (temp / "round1.c").write_text(body)
        (temp / "round1.h").write_text(header_body)
        command = (f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{wsl(temp)}' '{wsl(temp / 'round1.c')}' "
                   f"tests/port_v2/round1/round1_entry_test.c -o '{wsl(temp / 'test')}' && "
                   f"'{wsl(temp / 'test')}'")
        result = subprocess.run(["wsl.exe", "bash", "-lc", command], capture_output=True)
        assert (result.returncode == 0) == passes

run(source, header, True)
for before, after in (
    ("runtime->route_state = AVSP_ROUND1_ROUTE_ENTRY_STATE;", "runtime->route_state = 4;"),
    ("{20u, 20u, 16u, 32u}", "{20u, 20u, 16u, 31u}"),
    ("{192u, 128u, 128u, 128u}", "{128u, 128u, 128u, 128u}"),
    ("runtime->rng_seed = AVSP_ROUND1_INITIAL_RNG;", "runtime->rng_seed = 1u;"),
):
    assert before in source
    run(source.replace(before, after), header, False)
print("REIMPLEMENT-13 stable entry host differential: PASS (4 real mutations)")
