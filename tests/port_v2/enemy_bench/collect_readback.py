#!/usr/bin/env python3
"""Pinned-Yaba enemy position, ROM assembly, failure, and stability readback."""

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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(required: list[str]) -> dict[str, int]:
    nm = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
    output = subprocess.run([str(nm), "--target=coff-sh", str(ROOT / "game.elf")],
                            check=True, capture_output=True, text=True).stdout
    result = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("_"):
            result.setdefault(parts[2][1:], int(parts[0], 16))
    missing = [name for name in required if name not in result]
    if missing:
        raise RuntimeError(f"missing enemy symbols: {', '.join(missing)}")
    return result


def process_record(pid: int) -> dict[str, object]:
    command = ("$p=Get-CimInstance Win32_Process -Filter \"ProcessId=%d\"; "
               "$p | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress") % pid
    raw = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                         check=True, capture_output=True, text=True).stdout
    value = json.loads(raw)
    return {"pid": int(value["ProcessId"]), "executable": value["ExecutablePath"],
            "command_line": value["CommandLine"]}


def window_bounds(pid: int, timeout: float) -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    deadline = time.time() + timeout
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
    raise TimeoutError("pinned emulator window unavailable")


def signed32(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


def snapshot(mcp: Mcp, syms: dict[str, int]) -> dict[str, int]:
    fields = {
        "runtime_ready":"avsp_diag_runtime_ready", "interface_version":"avsp_diag_enemy_interface_version",
        "relative_frame":"avsp_diag_enemy_frame", "phase":"avsp_diag_enemy_phase",
        "class_id":"avsp_diag_enemy_class_id", "x":"avsp_diag_enemy_x",
        "lane":"avsp_diag_enemy_lane", "facing":"avsp_diag_enemy_facing",
        "anim_record":"avsp_diag_enemy_anim_record", "assembly":"avsp_diag_enemy_assembly",
        "object_count":"avsp_diag_enemy_object_count", "render_count":"avsp_diag_enemy_render_count",
        "command_code":"avsp_diag_enemy_command_code", "palette_bank":"avsp_diag_enemy_palette_bank",
        "asset_failures":"avsp_diag_enemy_asset_failures", "negative_rejections":"avsp_diag_enemy_negative_rejections",
        "canary_ok":"avsp_diag_enemy_canary_ok", "disc_late_reads":"avsp_diag_enemy_disc_late_reads",
        "tile_bank_misses":"avsp_diag_enemy_tile_bank_misses", "tile_rank_misses":"avsp_diag_enemy_tile_rank_misses",
    }
    state = {name: signed32(mcp.u32(syms[symbol])) for name, symbol in fields.items()}
    status = mcp.call("debug_status")
    match = re.search(r"^frame:\s+(\d+)$", status, re.MULTILINE)
    state["emulator_frame"] = int(match.group(1)) if match else -1
    return state


def wait_frame(mcp: Mcp, syms: dict[str, int], target: int, timeout: float) -> dict[str, int]:
    address = hex(syms["avsp_diag_enemy_frame"])
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory", address=address,
             write=True, value=hex(target))
    try:
        mcp.call("resume")
        stopped = mcp.call("wait_for_stop", timeout_ms=int(timeout * 1000))
        if "stopped: true" not in stopped:
            raise TimeoutError(f"enemy frame {target} was not reached")
        state = snapshot(mcp, syms)
        if state["relative_frame"] != target:
            raise RuntimeError(f"enemy frame mismatch: {state}")
        return state
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory", address=address)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "enemy_contract.json").read_text())
    build = json.loads((ROOT / f"build/port_v2/enemy_bench/run-{args.run}/build.json").read_text())
    syms = symbols(inventory["required_readback_symbols"])
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
    mcp.call("set_debug_option", cpu_core="interpreter")
    bounds = window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and mcp.u32(syms["avsp_diag_enemy_interface_version"]) == contract["interface_version"]:
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("enemy bench did not become ready")
    samples = {}
    for label in ("stationary", "translated", "repeat_stationary"):
        expected = contract["samples"][label]
        samples[label] = wait_frame(mcp, syms, expected["frame"], args.timeout)
        if label == "translated":
            screenshot = ROOT / f"build/port_v2/enemy_bench/run-{args.run}/emulator.png"
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    mcp.call("resume")
    actor = contract["source_actor"]
    for label, state in samples.items():
        expected = contract["samples"][label]
        required = (state["runtime_ready"] == 1 and state["interface_version"] == 1 and
                    state["class_id"] == actor["class_id"] and state["palette_bank"] == actor["palette_bank"] and
                    state["lane"] == actor["lane"] and state["facing"] == actor["facing"] and
                    state["phase"] == expected["phase"] and state["x"] == expected["x"] and
                    state["anim_record"] > 0 and state["assembly"] > 0 and state["object_count"] > 0 and
                    state["render_count"] >= state["object_count"] and state["command_code"] >= 0 and
                    state["asset_failures"] == 0 and state["negative_rejections"] == 2 and
                    state["canary_ok"] == 1 and state["disc_late_reads"] == 0 and
                    state["tile_bank_misses"] == 0 and state["tile_rank_misses"] == 0)
        if not required:
            raise RuntimeError(f"enemy invariant failed at {label}: {state}")
    process = process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {"schema":1, "task_id":inventory["task_id"], "card_profile":inventory["card_profile"],
              "source_commit":build["source_commit"], "iso_sha256":build["artifacts"]["game_iso"]["sha256"],
              "samples":samples, "bounded_stability_frames":samples["repeat_stationary"]["emulator_frame"]-samples["stationary"]["emulator_frame"],
              "final_scanout":{"width":352,"height":224,"screenshot":{"path":screenshot.relative_to(ROOT).as_posix(),"sha256":sha256(screenshot),"bytes":screenshot.stat().st_size}},
              "emulator":{"identity":"Yaba Sanshiro 1.20.37-2986eb","evidence_tier":"ONE_EMULATOR","process_id":process["pid"],"executable_sha256":sha256(executable),"settings_sha256":sha256(settings),"command_line":process["command_line"]},
              "disabled_systems":contract["disabled_systems"],"physical_saturn":"UNRUN","result":"PASS"}
    output = ROOT / f"build/port_v2/enemy_bench/run-{args.run}/readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
