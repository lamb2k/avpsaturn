#!/usr/bin/env python3
"""Recover the VDP2 priority programming from WRITE traces.

Reading the VDP2 register block is impossible in this instrument: the
companion probe shows every view returning zeros while its colour-RAM
control reads fine. The registers are still written, though, so this
tool watches the writes instead of the state.

It sets an SH-2 memory write breakpoint on each priority register,
through both the cached and uncached views, resumes, and records for
every hit the writing PC, the register file, a disassembly window and a
backtrace. The written value is recovered from the SH-2 store operand
rather than by reading the register back.

A run in which no breakpoint fires is reported as such. That is a real
result with a specific meaning -- the registers are not written by SH-2
stores in the observed window, which points at an SCU DMA transfer from
a work-RAM shadow -- and it is never reported as "priority is zero".
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_mshvsf_saturn_mcp import (  # noqa: E402
    McpClient, dump_region, parse_status, wait_and_pause)

DEFAULT_ENDPOINT = "http://127.0.0.1:9640/mcp"

PRIORITY_REGISTERS = {
    0x0E0: "SPCTL",
    0x0F0: "PRISA",
    0x0F2: "PRISB",
    0x0F4: "PRISC",
    0x0F6: "PRISD",
    0x0F8: "PRINA",
    0x0FA: "PRINB",
    0x0FC: "PRIR",
}
VIEW_BASES = (0x05F80000, 0x25F80000)
CPUS = ("master", "slave")

PC_RE = re.compile(r"\bPC[:=]\s*(?:0x)?([0-9a-fA-F]{8})")


CONTROL_WINDOWS = ((0x06000000, 0x2000),
                   (0x00200000, 0x2000))


def find_control_address(client: McpClient):
    """An address the game demonstrably writes, chosen empirically.

    Watching only the VDP2 registers cannot distinguish "nothing writes
    them" from "the watchpoint mechanism is inert". So the run also
    watches a high-work-RAM long observed CHANGING between two frames,
    and that control must fire; if it does not, the run proves nothing
    about VDP2.
    """
    for base, length in CONTROL_WINDOWS:
        before = dump_region(client, base, length, 0x100)
        _, start_frame = parse_status(client.call("debug_status"))
        for _ in range(30):
            client.call("resume")
            client.call("pause")
            _, now = parse_status(client.call("debug_status"))
            if now != start_frame:
                break
        after = dump_region(client, base, length, 0x100)
        for offset in range(0, length - 3, 4):
            if before[offset:offset + 4] != after[offset:offset + 4]:
                return base + offset
    return None


def add_watchpoints(client: McpClient) -> list[dict]:
    added = []
    for cpu in CPUS:
        for base in VIEW_BASES:
            for offset, name in PRIORITY_REGISTERS.items():
                address = base + offset
                try:
                    client.call("breakpoint_add", {
                        "cpu": cpu,
                        "type": "memory",
                        "address": f"0x{address:08X}",
                        "write": True,
                        "read": False,
                    })
                except Exception as error:
                    added.append({"cpu": cpu, "register": name,
                                  "address": f"0x{address:08x}",
                                  "error": str(error)})
                    continue
                added.append({"cpu": cpu, "register": name,
                              "address": f"0x{address:08x}"})
    return added


def remove_watchpoints(client: McpClient) -> None:
    for cpu in CPUS:
        for base in VIEW_BASES:
            for offset in PRIORITY_REGISTERS:
                try:
                    client.call("breakpoint_remove", {
                        "cpu": cpu, "type": "memory",
                        "address": f"0x{base + offset:08X}"})
                except Exception:
                    pass


def collect_hit(client: McpClient, status_text: str) -> dict:
    hit = {"status": status_text.strip().splitlines()[:6]}
    for cpu in CPUS:
        try:
            registers = client.call("registers_get", {"cpu": cpu})
        except Exception as error:
            hit[cpu] = {"error": str(error)}
            continue
        entry = {"registers": registers.strip().splitlines()[:8]}
        match = PC_RE.search(registers)
        if match:
            pc = int(match.group(1), 16)
            entry["pc"] = f"0x{pc:08x}"
            try:
                entry["disassembly"] = client.call("disassemble", {
                    "cpu": cpu, "address": f"0x{max(pc - 8, 0):08X}",
                    "count": 8}).strip().splitlines()
            except Exception as error:
                entry["disassembly"] = [f"error: {error}"]
        try:
            entry["backtrace"] = client.call(
                "backtrace", {"cpu": cpu}).strip().splitlines()[:8]
        except Exception as error:
            entry["backtrace"] = [f"error: {error}"]
        hit[cpu] = entry
    return hit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--arm-frame", type=int, required=True,
                        help="pause here, then arm the watchpoints")
    parser.add_argument("--hits", type=int, default=6)
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    client = McpClient(args.endpoint)
    status = wait_and_pause(client, args.arm_frame)
    state, frame = parse_status(status)
    if state != "stopped":
        raise SystemExit(f"could not pause at frame {args.arm_frame}")

    # Memory breakpoints are only reliable on the debug interpreter
    # core; on the fast core they can silently never fire.
    core_note = None
    try:
        core_note = client.call(
            "set_debug_option", {"cpu_core": "interpreter"}).strip()
    except Exception as error:
        core_note = f"error: {error}"

    # A code breakpoint at the master CPU's own PC must fire almost
    # immediately. It separates "memory watchpoints are inert" from
    # "the breakpoint mechanism as a whole is inert".
    code_control = {"address": None, "fired": False}
    try:
        registers = client.call("registers_get", {"cpu": "master"})
        match = PC_RE.search(registers)
        if match:
            code_control["address"] = f"0x{int(match.group(1), 16):08x}"
            client.call("breakpoint_add", {
                "cpu": "master", "type": "code",
                "address": f"0x{int(match.group(1), 16):08X}"})
            client.call("resume")
            stopped = client.call("wait_for_stop", {"timeout_ms": 8000})
            state_after, _ = parse_status(stopped)
            code_control["fired"] = state_after == "stopped"
            client.call("breakpoint_remove", {
                "cpu": "master", "type": "code",
                "address": f"0x{int(match.group(1), 16):08X}"})
    except Exception as error:
        code_control["error"] = str(error)

    control_address = find_control_address(client)
    control_hit = False
    if control_address is not None:
        try:
            client.call("breakpoint_add", {
                "cpu": "master", "type": "memory",
                "address": f"0x{control_address:08X}",
                "write": True, "read": False})
        except Exception:
            control_address = None

    watchpoints = add_watchpoints(client)
    armed = [w for w in watchpoints if "error" not in w]
    hits = []
    try:
        for _ in range(args.hits):
            client.call("resume")
            stopped = client.call(
                "wait_for_stop", {"timeout_ms": args.timeout_ms})
            try:
                state, frame = parse_status(stopped)
            except ValueError:
                state, frame = "unknown", -1
            if state != "stopped":
                break
            hit = collect_hit(client, stopped)
            hit["frame"] = frame
            if control_address is not None and any(
                    f"{control_address:08x}" in line.lower()
                    for line in hit["status"]):
                control_hit = True
                continue
            hits.append(hit)
    finally:
        remove_watchpoints(client)
        if control_address is not None:
            try:
                client.call("breakpoint_remove", {
                    "cpu": "master", "type": "memory",
                    "address": f"0x{control_address:08X}"})
            except Exception:
                pass

    report = {
        "schema": "mshvsf-vdp2-write-trace-v0",
        "armed_frame": args.arm_frame,
        "watchpoints_armed": len(armed),
        "watchpoints_failed": [w for w in watchpoints if "error" in w],
        "registers_watched": sorted(set(PRIORITY_REGISTERS.values())),
        "views_watched": [f"0x{b:08x}" for b in VIEW_BASES],
        "hit_count": len(hits),
        "hits": hits,
        "cpu_core_note": core_note,
        "code_breakpoint_control": code_control,
        "positive_control": {
            "address": None if control_address is None
            else f"0x{control_address:08x}",
            "method": "a high-work-RAM long observed changing between "
                      "two frames, watched for writes",
            "fired": control_hit,
        },
        "conclusion":
            "no control address could be selected: no work-RAM long was "
            "observed changing across a frame, so the run has no proof "
            "that the watchpoint mechanism works and proves NOTHING "
            "about VDP2"
            if control_address is None else
            "the write-watchpoint mechanism did not fire even on a "
            "control address the game demonstrably writes; this run "
            "proves NOTHING about how VDP2 priority is programmed"
            if not control_hit else
            "no SH-2 store to any VDP2 priority register in the observed "
            "window; the block is written by something other than SH-2 "
            "stores (an SCU DMA from a work-RAM shadow is the candidate) "
            "-- this is NOT evidence that the priorities are zero"
            if not hits else
            f"{len(hits)} SH-2 write(s) to VDP2 priority registers "
            f"captured with writer PCs",
    }
    args.output.write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    print(f"vdp2 write trace: {len(armed)} watchpoints armed, "
          f"{len(hits)} hit(s); write control "
          f"{'FIRED' if control_hit else 'DID NOT FIRE'}; code-breakpoint "
          f"control {'FIRED' if code_control['fired'] else 'DID NOT FIRE'}")
    return 0 if control_hit else 3


if __name__ == "__main__":
    raise SystemExit(main())
