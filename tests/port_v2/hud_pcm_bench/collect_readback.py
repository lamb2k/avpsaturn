#!/usr/bin/env python3
"""Pinned-Yaba HUD state, PCM timing, failure, and stability readback."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402


BMPNA_OFFSET = 0x2C


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def symbols(elf: Path, nm: Path, required: list[str]) -> dict[str, int]:
    output = subprocess.run([str(nm), "--target=coff-sh", str(elf)],
                            check=True, capture_output=True, text=True).stdout
    result = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("_"):
            result.setdefault(parts[2][1:], int(parts[0], 16))
    missing = [name for name in required + ["slBMPalette"] if name not in result]
    if missing:
        raise RuntimeError(f"missing HUD/PCM symbols: {', '.join(missing)}")
    return result


def process_record(pid: int) -> dict[str, str | int]:
    command = ("$p=Get-CimInstance Win32_Process -Filter \"ProcessId=%d\"; "
               "$p | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress") % pid
    raw = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                         check=True, capture_output=True, text=True).stdout
    value = json.loads(raw)
    return {"pid": int(value["ProcessId"]), "executable": value["ExecutablePath"],
            "command_line": value["CommandLine"]}


def window_bounds(pid: int, timeout: float) -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    deadline = time.time() + timeout
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                      ctypes.c_void_p)
    while time.time() < deadline:
        found: list[int] = []

        @callback_type
        def callback(hwnd: int, _: int) -> bool:
            found_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
            if found_pid.value == pid and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
                return False
            return True

        user32.EnumWindows(callback, 0)
        if found:
            rect = wintypes.RECT()
            if user32.GetWindowRect(found[0], ctypes.byref(rect)):
                return rect.left, rect.top, rect.right, rect.bottom
        time.sleep(0.25)
    raise TimeoutError("pinned emulator window did not become visible")


def signed32(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


def snapshot(mcp: Mcp, syms: dict[str, int], promotion: bool,
             pcm_promotion: bool) -> dict[str, int]:
    names = {
        "relative_frame": "avsp_diag_hud_pcm_frame",
        "runtime_ready": "avsp_diag_runtime_ready",
        "interface_version": "avsp_diag_hud_pcm_interface_version",
        "phase": "avsp_diag_hud_pcm_phase",
        "hud_state": "avsp_diag_hud_state",
        "health": "avsp_diag_hud_health",
        "energy": "avsp_diag_hud_energy",
        "health_fill": "avsp_diag_hud_health_fill",
        "energy_fill": "avsp_diag_hud_energy_fill",
        "hud_render_count": "avsp_diag_hud_render_count",
        "p2_hud_state": "avsp_diag_hud_p2_state",
        "p2_health": "avsp_diag_hud_p2_health",
        "p2_energy": "avsp_diag_hud_p2_energy",
        "p2_health_fill": "avsp_diag_hud_p2_health_fill",
        "p2_energy_fill": "avsp_diag_hud_p2_energy_fill",
        "p2_hud_render_count": "avsp_diag_hud_p2_render_count",
        "p2_hud_binding_ok": "avsp_diag_hud_p2_binding_ok",
        "hud_asset_failures": "avsp_diag_hud_asset_failures",
        "pcm_audio_failures": "avsp_diag_pcm_audio_failures",
        "pcm_event_count": "avsp_diag_pcm_event_count",
        "pcm_event_frame": "avsp_diag_pcm_event_frame",
        "pcm_start_frame": "avsp_diag_pcm_start_frame",
        "pcm_end_frame": "avsp_diag_pcm_end_frame",
        "pcm_active": "avsp_diag_pcm_active",
        "pcm_channel_observed": "avsp_diag_pcm_channel_observed",
        "pcm_underruns": "avsp_diag_pcm_underruns",
        "negative_rejections": "avsp_diag_hud_pcm_negative_rejections",
        "canary_ok": "avsp_diag_hud_pcm_canary_ok",
        "disc_late_reads": "avsp_diag_hud_pcm_disc_late_reads",
        "hud_palette_binding_ok": "avsp_diag_hud_palette_binding_ok",
        "hud_palette_yellow": "avsp_diag_hud_palette_yellow",
        "hud_palette_red": "avsp_diag_hud_palette_red",
        "hud_palette_energy": "avsp_diag_hud_palette_energy",
        "hud_palette_empty": "avsp_diag_hud_palette_empty",
    }
    state = {name: signed32(mcp.u32(syms[symbol]))
             for name, symbol in names.items()}
    if promotion:
        for name, symbol in {
            "hud_production_interface_version":
                "avsp_diag_hud_production_interface_version",
            "hud_port_lock_ok": "avsp_diag_hud_port_lock_ok",
            "hud_submit_count": "avsp_diag_hud_submit_count",
        }.items():
            state[name] = signed32(mcp.u32(syms[symbol]))
    if pcm_promotion:
        for name, symbol in {
            "pcm_production_interface_version":
                "avsp_diag_pcm_production_interface_version",
            "pcm_port_lock_ok": "avsp_diag_pcm_port_lock_ok",
            "pcm_allocation_ok": "avsp_diag_pcm_allocation_ok",
            "pcm_submit_count": "avsp_diag_pcm_submit_count",
            "pcm_semantic_active": "avsp_diag_pcm_semantic_active",
        }.items():
            state[name] = signed32(mcp.u32(syms[symbol]))
    status = mcp.call("debug_status")
    match = re.search(r"^frame:\s+(\d+)$", status, re.MULTILINE)
    state["emulator_frame"] = int(match.group(1)) if match else -1
    return state


def wait_for_frame(mcp: Mcp, syms: dict[str, int], target: int,
                   timeout: float, promotion: bool,
                   pcm_promotion: bool) -> dict[str, int]:
    address = hex(syms["avsp_diag_hud_pcm_frame"])
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory", address=address,
             write=True, value=hex(target))
    try:
        mcp.call("resume")
        stopped = mcp.call("wait_for_stop", timeout_ms=int(timeout * 1000))
        if "stopped: true" not in stopped:
            raise TimeoutError(f"HUD/PCM frame {target} was not reached")
        state = snapshot(mcp, syms, promotion, pcm_promotion)
        if state["relative_frame"] != target:
            raise RuntimeError(
                f"HUD/PCM stopped at {state['relative_frame']}, expected {target}")
        return state
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=address)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--suite", choices=("hud_pcm_bench", "hud", "pcm"),
                        default="hud_pcm_bench")
    args = parser.parse_args()
    suite_here = ROOT / "tests/port_v2" / args.suite
    contract_name = ("hud_pcm_contract.json" if
                     args.suite == "hud_pcm_bench" else
                     "approved_contract.json")
    inventory = json.loads((suite_here / "inventory.json").read_text(encoding="utf-8"))
    contract = json.loads((suite_here / contract_name).read_text(
        encoding="utf-8"))
    build = json.loads((ROOT / f"build/port_v2/{args.suite}/run-{args.run}/build.json").read_text(encoding="ascii"))
    syms = symbols(ROOT / "game.elf",
                   ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe",
                   inventory["required_readback_symbols"])
    mcp = Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.25)
    # Memory breakpoints are intentionally serviced only by Yaba's debug
    # interpreter core. Pin it explicitly instead of inheriting GUI state.
    mcp.call("set_debug_option", cpu_core="interpreter")
    bounds = window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if (mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and
                mcp.u32(syms["avsp_diag_hud_pcm_interface_version"]) ==
                contract["interface_version"]):
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("HUD/PCM bench did not become runtime-ready")
    literal = mcp.u32(syms["slBMPalette"] + 0x10)
    if not 0x06000000 <= literal < 0x06100000:
        raise RuntimeError(f"invalid SGL shadow anchor: 0x{literal:08x}")
    shadow = literal - BMPNA_OFFSET

    samples = {}
    for label, target in (
        ("zero", 20), ("mid", 140), ("together", 180),
        ("full", 260), ("pcm_only", 420), ("negative", 460),
        ("repeat_zero", 20),
    ):
        samples[label] = wait_for_frame(
            mcp, syms, target, args.timeout,
            args.suite in ("hud", "pcm"), args.suite == "pcm")
        if label == "together":
            run_root = ROOT / f"build/port_v2/{args.suite}/run-{args.run}"
            run_root.mkdir(parents=True, exist_ok=True)
            screenshot = run_root / "emulator.png"
            ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    mcp.call("resume")

    palette = contract["hud_palette"]
    palette_expected = {
        "hud_palette_binding_ok": palette["binding_ok"],
        **{f"hud_palette_{name}": value["saturn_cram"]
           for name, value in palette["semantic_colors"].items()},
    }
    for state in samples.values():
        if not (state["runtime_ready"] == 1 and
                state["interface_version"] == contract["interface_version"] and
                state["hud_asset_failures"] == 0 and
                state["pcm_audio_failures"] == 0 and
                state["pcm_underruns"] == 0 and
                state["p2_hud_binding_ok"] == 1 and
                state["canary_ok"] == 1 and
                state["disc_late_reads"] == 0 and
                all(state[name] == value
                    for name, value in palette_expected.items())):
            raise RuntimeError(f"HUD/PCM readback invariant failed: {state}")
        if args.suite in ("hud", "pcm") and not (
                state["hud_production_interface_version"] ==
                    contract["production_interface_version"] and
                state["hud_port_lock_ok"] == 1):
            raise RuntimeError(f"HUD promotion port invariant failed: {state}")
        if args.suite == "pcm" and not (
                state["pcm_production_interface_version"] ==
                    contract["production_interface_version"] and
                state["pcm_port_lock_ok"] == 1 and
                state["pcm_allocation_ok"] == 1):
            raise RuntimeError(f"PCM promotion port invariant failed: {state}")
    if samples["together"]["pcm_active"] != 1 or \
            samples["together"]["pcm_channel_observed"] != 1:
        raise RuntimeError("combined HUD/PCM phase did not start its SCSP channel")
    if samples["pcm_only"]["hud_render_count"] != 0 or \
            samples["pcm_only"]["pcm_active"] != 1:
        raise RuntimeError("PCM-only phase did not isolate the cue")
    if samples["negative"]["negative_rejections"] != \
            len(contract["negative_controls"]):
        raise RuntimeError("runtime missing/invalid asset controls did not reject")

    process = process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1,
        "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "compile_profile": build["compile_profile"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "samples": samples,
        "bounded_stability_frames": (
            samples["repeat_zero"]["emulator_frame"] -
            samples["zero"]["emulator_frame"]),
        "final_scanout": {
            "tvmd": f"0x{mcp.u16(shadow):04x}",
            "width": 352,
            "height": 224,
            "screenshot": {
                "path": portable(screenshot),
                "sha256": sha256(screenshot),
                "bytes": screenshot.stat().st_size,
            },
        },
        "emulator": {
            "identity": "Yaba Sanshiro 1.20.37-2986eb",
            "evidence_tier": "ONE_EMULATOR",
            "process_id": process["pid"],
            "executable_sha256": sha256(executable),
            "settings_sha256": sha256(settings),
            "command_line": process["command_line"],
        },
        "disabled_systems": contract["disabled_systems"],
        "approved_stage_player_locks": "REGRESSION_LOCK_ONLY",
        "physical_saturn": "UNRUN",
        "result": "PASS",
    }
    output = ROOT / f"build/port_v2/{args.suite}/run-{args.run}/readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
