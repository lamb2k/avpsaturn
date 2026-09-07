#!/usr/bin/env python3
"""Committed identity and negative controls for the first ORACLE-11 family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_scheduler", ROOT / "tools" / "analyze_oracle11_actor_scheduler.py")
assert SPEC and SPEC.loader
oracle11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle11)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle11.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-11 scheduler mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle11.validate(report)

mutant = copy.deepcopy(report)
mutant["pools"][0]["stride"] = 0x80
reject(mutant, "type-12 stride")

mutant = copy.deepcopy(report)
mutant["frame_scheduler"]["required_round1_order"] = [12, 20, 16, 24]
reject(mutant, "pool update order")

mutant = copy.deepcopy(report)
mutant["pools"][0]["required_round1_dispatch"] = []
reject(mutant, "dispatch mapping removed")

mutant = copy.deepcopy(report)
mutant["pools"][2]["release"]["order"] = "FIFO"
reject(mutant, "free-list order")

mutant = copy.deepcopy(report)
mutant["closure"]["classification"] = "PARTIAL"
reject(mutant, "unclosed classification")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["user09_status"] = "ACCEPTED"
reject(mutant, "inferred USER-09 approval")

rebuilt = oracle11.build_report()
assert oracle11.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-11 actor scheduler/lifecycle tests: PASS (6 mutations rejected)")

# This is an evidence-readiness check, not a runtime semantic mutation kill.
opcodes = oracle11.OPCODES.read_bytes()
readiness = oracle11.interactive_readiness(opcodes)
assert readiness == oracle11.interactive_readiness(opcodes), "readiness repeat drift"
assert readiness["status"] == "BLOCKED_MISSING_EXECUTABLE_TICK_CONTRACT"
assert readiness["production_implementation_authorized_by_this_audit"] is False
for address in (0x0011EA, 0x001060, 0x00808A, 0x008140, 0x014B44, 0x001092,
                0x017090, 0x00C772, 0x01613C):
    changed = bytearray(opcodes)
    changed[address] ^= 1
    try:
        oracle11.interactive_readiness(bytes(changed))
    except ValueError as error:
        assert str(error) == f"interactive scheduler source window drift: 0x{address:06x}"
    else:
        raise AssertionError(f"accepted changed scheduler source window {address:06x}")
print("Interactive scheduler readiness: BLOCKED (9 attributable identity controls; no runtime kills)")

# Write ownership controls are evidence-validation controls, not native kills.
guard = {"event": "guard_write", "address": "ff81bc", "pc": "008090",
         "data": "65535", "mask": "65280"}
assert oracle11.clock_guard_owner(guard) == "loop_00808a_set"
assert oracle11.clock_guard_owner(dict(guard)) == "loop_00808a_set"
for field, value in (("event", "opcode_fetch"), ("address", "ff81a6"),
                     ("pc", "000e92"), ("data", "0"), ("mask", "255")):
    mutant = dict(guard, **{field: value})
    try:
        oracle11.clock_guard_owner(mutant)
    except ValueError as error:
        assert str(error) == "unowned scheduler guard write"
    else:
        raise AssertionError(f"credited changed guard ownership: {field}")
print("Scheduler clock write provenance: PASS (5 attributable evidence controls; no runtime kills)")

wake = {"event": "control_write", "address": "ff81b8", "pc": "01715a",
        "data": "257", "mask": "255", "wake_counter": "5", "wake_request": "1",
        "participation": "1", "input1": "16"}
oracle11.validate_wake_write(wake)
oracle11.validate_wake_write(dict(wake))
for field, value, diagnostic in (
    ("pc", "000e92", "unowned wake-control writer"),
    ("address", "ff1744", "wake-control write arithmetic or field drift"),
    ("data", "0", "wake-control write arithmetic or field drift"),
    ("mask", "65280", "wake-control write arithmetic or field drift"),
    ("wake_counter", "4", "wake-control threshold guard drift"),
    ("wake_request", "0", "wake-control request guard drift"),
):
    try:
        oracle11.validate_wake_write(dict(wake, **{field: value}))
    except ValueError as error:
        assert str(error) == diagnostic
    else:
        raise AssertionError(f"credited changed wake control: {field}")
input_write = dict(wake, pc="017112", address="ff823a", mask="65280")
oracle11.validate_wake_write(input_write)
for field in ("participation", "input1"):
    try:
        oracle11.validate_wake_write(dict(input_write, **{field: "0"}))
    except ValueError as error:
        assert str(error) == "wake-control participating input guard drift"
    else:
        raise AssertionError(f"credited missing participating input: {field}")
print("Scheduler wake arithmetic/guards: PASS (8 attributable evidence controls; no native kills)")
increment = dict(wake, pc="01714e", address="ff1744", mask="65535",
                 wake_counter="65535", data="0")
oracle11.validate_wake_write(increment)
try:
    oracle11.validate_wake_write(dict(increment, data="65536"))
except ValueError:
    raise AssertionError("irrelevant bits outside the bus mask changed the selected write")
try:
    oracle11.validate_wake_write(dict(increment, data="1"))
except ValueError as error:
    assert str(error) == "wake-control write arithmetic or field drift"
else:
    raise AssertionError("accepted wrong counter wrap")
print("Scheduler counter width: PASS (1 arithmetic control; masked equivalent not credited)")
