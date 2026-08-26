#!/usr/bin/env python3
"""Collect the native Round 1 boot/HUD/audio ownership chronology in Yaba."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = ROOT / "tests/port_v2/enemy_bench/collect_readback.py"
SPEC = importlib.util.spec_from_file_location("avsp_yaba_tools", HELPER_PATH)
TOOLS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOLS)

SYMBOLS = [
    "avsp_diag_runtime_ready",
    "avsp_diag_round1_startup_trace",
    "avsp_diag_round1_startup_trace_count",
    "avsp_diag_round1_startup_retained_initializations",
    "avsp_diag_round1_startup_retained_steps",
    "avsp_diag_round1_startup_retained_before_handoff",
    "avsp_diag_round1_startup_p2_visible_frames",
    "avsp_diag_round1_startup_hidden_contacts",
    "avsp_diag_round1_startup_hidden_damage",
    "avsp_diag_round1_startup_orphan_pcm",
    "avsp_diag_round1_startup_cdda_starts",
    "avsp_diag_round1_startup_duplicate_cdda",
    "avsp_diag_round1_startup_first_pcm_frame",
    "avsp_diag_round1_startup_first_pcm_trigger",
    "avsp_diag_round1_startup_first_pcm_cue",
    "avsp_diag_round1_startup_source_frame",
    "avsp_diag_round1_route_state",
    "avsp_diag_round1_control_enabled",
    "avsp_diag_round1_failure_count",
    "avsp_diag_round1_fallback_count",
    "avsp_diag_round1_canaries_ok",
    "avsp_diag_round1_player_health",
    "avsp_diag_round1_player_resource",
    "avsp_diag_live_frame_stage",
    "avsp_diag_live_internal_failures",
    "failed_asset",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(value: int) -> int:
    return TOOLS.signed32(value)


def decode_trace(word: int) -> dict[str, int | bool]:
    return {
        "native_frame": (word >> 22) & 0xFF,
        "source_frame": 2040 + ((word >> 22) & 0xFF),
        "route_state": word & 0x0F,
        "player_initialized": bool(word & (1 << 4)),
        "player_visible": bool(word & (1 << 5)),
        "p1_hud_visible": bool(word & (1 << 6)),
        "p2_hud_visible": bool(word & (1 << 7)),
        "control_enabled": bool(word & (1 << 8)),
        "retained_encounter_stepped": bool(word & (1 << 9)),
        "contact": bool(word & (1 << 10)),
        "damage": bool(word & (1 << 11)),
        "pcm_event": bool(word & (1 << 12)),
        "pcm_cue": (word >> 13) & 0x0F,
        "cdda_command": (word >> 17) & 0x03,
        "rendered_actor_count": (word >> 19) & 0x03,
        "gameplay_authority": bool(word & (1 << 21)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    syms = TOOLS.symbols(SYMBOLS)
    mcp = TOOLS.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.25)
    mcp.call("set_debug_option", cpu_core="interpreter")
    bounds = TOOLS.window_bounds(args.emulator_pid, args.timeout)
    source_frame_address = hex(syms["avsp_diag_round1_startup_source_frame"])
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory",
             address=source_frame_address, write=True, value=hex(2521))
    try:
        mcp.call("resume")
        stopped = "stopped: false"
        while time.time() < deadline and "stopped: true" not in stopped:
            stopped = mcp.call("wait_for_stop", timeout_ms=20000)
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=source_frame_address)
    if ("stopped: true" not in stopped or
            mcp.u32(syms["avsp_diag_round1_startup_source_frame"]) != 2521):
        failed_pointer = mcp.u32(syms["failed_asset"])
        failed = ""
        if failed_pointer:
            failed = mcp.read(failed_pointer, 64).split(b"\0", 1)[0].decode(
                "ascii", errors="replace")
        raise TimeoutError(f"startup chronology did not stop at source 2521: {failed}")
    trace_count = signed(mcp.u32(syms["avsp_diag_round1_startup_trace_count"]))
    raw = mcp.read(syms["avsp_diag_round1_startup_trace"], trace_count * 4)
    trace = [decode_trace(int.from_bytes(raw[i:i + 4], "big"))
             for i in range(0, len(raw), 4)]
    scalar_names = SYMBOLS[2:-1]
    state = {name.removeprefix("avsp_diag_round1_startup_"):
             signed(mcp.u32(syms[name])) for name in scalar_names}
    state.update({
        "route_state": signed(mcp.u32(syms["avsp_diag_round1_route_state"])),
        "control_enabled": signed(mcp.u32(syms["avsp_diag_round1_control_enabled"])),
        "failure_count": signed(mcp.u32(syms["avsp_diag_round1_failure_count"])),
        "fallback_count": signed(mcp.u32(syms["avsp_diag_round1_fallback_count"])),
        "canaries_ok": signed(mcp.u32(syms["avsp_diag_round1_canaries_ok"])),
        "player_health": signed(mcp.u32(syms["avsp_diag_round1_player_health"])),
        "player_resource": signed(mcp.u32(syms["avsp_diag_round1_player_resource"])),
        "frame_stage": signed(mcp.u32(syms["avsp_diag_live_frame_stage"])),
        "internal_failures": signed(mcp.u32(syms["avsp_diag_live_internal_failures"])),
    })
    if not trace or not trace[-1]["control_enabled"]:
        raise RuntimeError(f"startup trace did not reach first control: {trace}")
    expected_frames = [0, 32, 35]
    for frame in expected_frames:
        if not any(row["native_frame"] == frame for row in trace):
            raise RuntimeError(f"startup transition frame {frame} missing: {trace}")
    first, hud, visible, control = trace[0], trace[1], trace[2], trace[-1]
    if (first["player_initialized"] or first["player_visible"] or
            first["p1_hud_visible"] or first["p2_hud_visible"]):
        raise RuntimeError(f"startup presentation appeared before source boundary: {first}")
    if not (hud["player_initialized"] and hud["p1_hud_visible"] and
            not hud["player_visible"] and not hud["p2_hud_visible"]):
        raise RuntimeError(f"HUD/player initialization chronology drifted: {hud}")
    if not (visible["player_visible"] and visible["rendered_actor_count"] == 1):
        raise RuntimeError(f"player visibility chronology drifted: {visible}")
    if not (control["route_state"] == 4 and control["control_enabled"] and
            control["gameplay_authority"]):
        raise RuntimeError(f"native handoff chronology drifted: {control}")
    if any(row["retained_encounter_stepped"] or row["contact"] or row["damage"] or
           row["pcm_event"] or row["p2_hud_visible"] for row in trace):
        raise RuntimeError(f"pre-handoff retained authority leaked: {trace}")
    required_zero = ("retained_before_handoff", "p2_visible_frames",
                     "hidden_contacts", "hidden_damage", "orphan_pcm",
                     "duplicate_cdda")
    if any(state[name] != 0 for name in required_zero):
        raise RuntimeError(f"startup zero-gap counters failed: {state}")
    if not (state["retained_initializations"] == 1 and
            state["cdda_starts"] == 1 and state["first_pcm_frame"] == -1 and
            state["route_state"] == 4 and state["control_enabled"] == 1 and
            state["failure_count"] == 0 and state["fallback_count"] == 0 and
            state["canaries_ok"] == 1 and state["internal_failures"] == 0):
        raise RuntimeError(f"startup ownership state failed: {state}")
    run_root = ROOT / f"build/port_v2/round1_startup/run-{args.run}"
    run_root.mkdir(parents=True, exist_ok=True)
    screenshot = run_root / "emulator.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    process = TOOLS.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1,
        "task_id": "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1",
        "checkpoint": "startup-authority",
        "source_commit": subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
            capture_output=True, text=True).stdout.strip(),
        "main_sha256": sha(ROOT / "main.c"),
        "iso_sha256": sha(ROOT / "game.iso"),
        "trace": trace,
        "state": state,
        "final_scanout": {
            "path": screenshot.relative_to(ROOT).as_posix(),
            "sha256": sha(screenshot),
            "bytes": screenshot.stat().st_size,
        },
        "emulator": {
            "identity": "Yaba Sanshiro 1.20.37-2986eb",
            "process_id": process["pid"],
            "executable_sha256": sha(executable),
            "settings_sha256": sha(settings),
            "command_line": process["command_line"],
        },
        "physical_saturn": "UNRUN",
        "result": "PASS",
    }
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
