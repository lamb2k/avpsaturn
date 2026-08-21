#!/usr/bin/env python3
"""Bounded ONE_EMULATOR diagnostic for the isolated prototype runtime."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "http://127.0.0.1:9640/mcp"
REQUIRED = (
    "prototype_diag_ready",
    "prototype_diag_frame",
    "prototype_diag_player_x",
    "prototype_diag_player_lane",
    "prototype_diag_inject_input",
    "prototype_diag_seen_input",
    "prototype_diag_render_heartbeat",
)


class Mcp:
    def __init__(self) -> None:
        self.next_id = 0
        self.session: str | None = None

    def post(self, method: str, params: dict) -> dict:
        self.next_id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self.next_id,
                           "method": method, "params": params}).encode()
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = urllib.request.Request(ENDPOINT, data=body, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.session = session
            text = response.read().decode()
        for line in text.splitlines():
            if line.startswith("data:"):
                text = line[5:].strip()
                break
        return json.loads(text) if text.strip() else {}

    def initialize(self) -> None:
        self.post("initialize", {"protocolVersion": "2024-11-05",
                                  "capabilities": {},
                                  "clientInfo": {"name": "avp-prototype-v1",
                                                 "version": "1"}})
        self.post("notifications/initialized", {})

    def call(self, name: str, **arguments) -> str:
        result = self.post("tools/call", {"name": name,
                                          "arguments": arguments})
        if "error" in result:
            raise RuntimeError(f"{name}: {result['error']}")
        return "\n".join(item.get("text", "")
                         for item in result["result"].get("content", []))

    def read(self, address: int, length: int) -> bytes:
        text = self.call("memory_read", address=hex(address), length=length)
        data = bytearray()
        for line in text.splitlines():
            match = re.match(r"^[0-9A-Fa-f]+:\s+((?:[0-9A-Fa-f]{2} ?)+)", line)
            if match:
                data += bytes(int(pair, 16) for pair in match.group(1).split())
        if len(data) < length:
            raise RuntimeError(f"short memory read at {address:#x}: {text}")
        return bytes(data[:length])

    def u32(self, address: int) -> int:
        return int.from_bytes(self.read(address, 4), "big")

    def write_u32(self, address: int, value: int) -> None:
        result = self.call("memory_write", address=hex(address), size="long",
                           value=hex(value))
        if "error" in result.lower() or "fail" in result.lower():
            raise RuntimeError(f"memory_write rejected payload: {result}")


def symbols(nm: Path, elf: Path) -> dict[str, int]:
    output = subprocess.run([str(nm), "--target=coff-sh", str(elf)],
                            check=True, capture_output=True, text=True).stdout
    found: dict[str, int] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("_"):
            found.setdefault(parts[2][1:], int(parts[0], 16))
    missing = [name for name in REQUIRED if name not in found]
    if missing:
        raise SystemExit("missing prototype diagnostics: " + ", ".join(missing))
    return found


def wait_for_mcp(deadline: float) -> Mcp:
    while time.monotonic() < deadline:
        client = Mcp()
        try:
            client.initialize()
            return client
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            time.sleep(0.5)
    raise SystemExit("pinned emulator MCP endpoint did not become ready")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emulator", type=Path, required=True)
    parser.add_argument("--nm", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=10)
    args = parser.parse_args()
    cue = ROOT / "build/prototype_v1/prototype_v1.cue"
    elf = ROOT / "game.elf"
    if not cue.is_file() or not elf.is_file():
        raise SystemExit("build the prototype before emulator verification")
    syms = symbols(args.nm, elf)
    process = subprocess.Popen(
        [str(args.emulator), "-nb", "-a", "-i", str(cue)],
        cwd=cue.parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        mcp = wait_for_mcp(time.monotonic() + 30)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if mcp.u32(syms["prototype_diag_ready"]) == 1:
                break
            time.sleep(0.25)
        else:
            raise SystemExit("prototype runtime did not reach ready")
        first_frame = mcp.u32(syms["prototype_diag_frame"])
        first_heartbeat = mcp.u32(syms["prototype_diag_render_heartbeat"])
        first_x = mcp.u32(syms["prototype_diag_player_x"])
        mcp.write_u32(syms["prototype_diag_inject_input"], 2)
        injected_value = mcp.u32(syms["prototype_diag_inject_input"])
        if injected_value != 2:
            raise SystemExit(
                f"memory_write did not store diagnostic input: {injected_value:#x}")
        time.sleep(0.5)
        frame_after_hold = mcp.u32(syms["prototype_diag_frame"])
        seen_input = mcp.u32(syms["prototype_diag_seen_input"])
        mcp.write_u32(syms["prototype_diag_inject_input"], 0)
        time.sleep(0.2)
        moved_x = mcp.u32(syms["prototype_diag_player_x"])
        if moved_x == first_x:
            raise SystemExit(
                "diagnostic D-pad injection did not move player "
                f"(frame {first_frame}->{frame_after_hold}, x={first_x:#x}, "
                f"seen={seen_input:#x})")
        smoke_deadline = time.monotonic() + args.seconds
        while time.monotonic() < smoke_deadline:
            if process.poll() is not None:
                raise SystemExit("pinned emulator exited during smoke")
            time.sleep(min(1.0, max(0.05, smoke_deadline - time.monotonic())))
        last_frame = mcp.u32(syms["prototype_diag_frame"])
        last_heartbeat = mcp.u32(syms["prototype_diag_render_heartbeat"])
        if last_frame <= first_frame or last_heartbeat <= first_heartbeat:
            raise SystemExit("prototype frame/render heartbeat stalled")
        report = {
            "classification": "ONE_EMULATOR PROTOTYPE_ONLY",
            "seconds": args.seconds,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "first_heartbeat": first_heartbeat,
            "last_heartbeat": last_heartbeat,
            "player_x_before": first_x,
            "player_x_after_input": moved_x,
            "result": "PASS",
        }
        output = ROOT / "build/prototype_v1/emulator_check.json"
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
