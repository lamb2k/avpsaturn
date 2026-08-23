#!/usr/bin/env python3
"""Pinned-Yaba CDDA ownership, legal-read, high-water, and canary readback."""

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
        raise RuntimeError(f"missing CDDA symbols: {', '.join(missing)}")
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
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                      ctypes.c_void_p)
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
        "runtime_ready": "avsp_diag_runtime_ready",
        "interface_version": "avsp_diag_cdda_interface_version",
        "relative_frame": "avsp_diag_cdda_frame",
        "action": "avsp_diag_cdda_action",
        "ownership": "avsp_diag_cdda_ownership",
        "track": "avsp_diag_cdda_track",
        "source_frame": "avsp_diag_cdda_source_frame",
        "track_events": "avsp_diag_cdda_track_events",
        "ownership_transitions": "avsp_diag_cdda_ownership_transitions",
        "window_open": "avsp_diag_cdda_window_open",
        "legal_windows": "avsp_diag_cdda_legal_windows",
        "legal_reads": "avsp_diag_cdda_legal_reads",
        "late_reads": "avsp_diag_cdda_late_reads",
        "refused_windows": "avsp_diag_cdda_refused_windows",
        "negative_rejections": "avsp_diag_cdda_negative_rejections",
        "failures": "avsp_diag_cdda_failures",
        "asset_failures": "avsp_diag_cdda_asset_failures",
        "canary_ok": "avsp_diag_cdda_canary_ok",
        "work_ram_high_water": "avsp_diag_cdda_work_ram_high_water",
        "cart_high_water": "avsp_diag_cdda_cart_high_water",
        "vdp1_high_water": "avsp_diag_cdda_vdp1_high_water",
        "vdp2_high_water": "avsp_diag_cdda_vdp2_high_water",
        "cram_high_water": "avsp_diag_cdda_cram_high_water",
        "scsp_high_water": "avsp_diag_cdda_scsp_high_water",
        "cdda_production_interface_version":
            "avsp_diag_cdda_production_interface_version",
        "residency_production_interface_version":
            "avsp_diag_residency_production_interface_version",
        "port_lock_ok": "avsp_diag_cdda_port_lock_ok",
        "cdda_submit_count": "avsp_diag_cdda_submit_count",
        "residency_submit_count": "avsp_diag_residency_submit_count",
        "fallback_used": "avsp_diag_cdda_fallback_used",
    }
    state = {name: signed32(mcp.u32(syms[symbol]))
             for name, symbol in fields.items() if symbol in syms}
    status = mcp.call("debug_status")
    match = re.search(r"^frame:\s+(\d+)$", status, re.MULTILINE)
    state["emulator_frame"] = int(match.group(1)) if match else -1
    return state


def wait_frame(mcp: Mcp, syms: dict[str, int], target: int,
               timeout: float) -> dict[str, int]:
    address = hex(syms["avsp_diag_cdda_frame"])
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory", address=address,
             write=True, value=hex(target))
    try:
        mcp.call("resume")
        stopped = mcp.call("wait_for_stop", timeout_ms=int(timeout * 1000))
        if "stopped: true" not in stopped:
            raise TimeoutError(f"CDDA frame {target} was not reached")
        state = snapshot(mcp, syms)
        if state["relative_frame"] != target:
            raise RuntimeError(f"CDDA frame mismatch: {state}")
        return state
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=address)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--metadata-dir",
                        default="tests/port_v2/cdda_residency_bench")
    parser.add_argument("--output-root",
                        default="build/port_v2/cdda_residency_bench")
    args = parser.parse_args()
    metadata = ROOT / args.metadata_dir
    output_root = ROOT / args.output_root
    inventory = json.loads((metadata / "inventory.json").read_text(
        encoding="utf-8"))
    contract = json.loads((metadata / "contract.json").read_text(
        encoding="utf-8"))
    build = json.loads((output_root / f"run-{args.run}/build.json").read_text(
        encoding="ascii"))
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
        if (mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and
                mcp.u32(syms["avsp_diag_cdda_interface_version"]) ==
                contract["interface_version"]):
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("CDDA/residency bench did not become ready")

    samples = {}
    for label, target in contract["checkpoints"].items():
        samples[label] = wait_frame(mcp, syms, target, args.timeout)
        if label == "stable":
            screenshot = output_root / f"run-{args.run}/emulator.png"
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    samples["repeat_idle"] = wait_frame(
        mcp, syms, contract["checkpoints"]["idle"], args.timeout)
    mcp.call("resume")

    for state in samples.values():
        if not (state["runtime_ready"] == 1 and
                state["interface_version"] == contract["interface_version"] and
                state["track"] == contract["track"] and
                state["source_frame"] == contract["source_event"]["frame"] and
                state["failures"] == 0 and state["asset_failures"] == 0 and
                state["canary_ok"] == 1 and
                state["work_ram_high_water"] == 72 and
                all(state[name] == 0 for name in (
                    "cart_high_water", "vdp1_high_water", "vdp2_high_water",
                    "cram_high_water", "scsp_high_water"))):
            raise RuntimeError(f"CDDA invariant failed: {state}")
    final = samples["stable"]
    for name, expected in contract["expected_final"].items():
        if final[name] != expected:
            raise RuntimeError(
                f"CDDA final {name} was {final[name]}, expected {expected}")
    if not (samples["cdda_owned"]["ownership"] == 1 and
            samples["cdda_owned"]["track_events"] == 1 and
            samples["illegal_read_rejected"]["late_reads"] == 1 and
            samples["illegal_window_rejected"]["refused_windows"] == 1 and
            samples["window_open"]["window_open"] == 1 and
            samples["legal_read_complete"]["legal_reads"] == 1 and
            samples["window_closed"]["window_open"] == 0):
        raise RuntimeError(
            "CDDA ownership/window sequence drifted: "
            f"cdda={samples['cdda_owned']}, "
            f"illegal_read={samples['illegal_read_rejected']}, "
            f"illegal_window={samples['illegal_window_rejected']}, "
            f"window_open={samples['window_open']}, "
            f"legal_read={samples['legal_read_complete']}, "
            f"window_closed={samples['window_closed']}")
    repeat = samples["repeat_idle"]
    if not (repeat["relative_frame"] == contract["checkpoints"]["idle"] and
            repeat["ownership"] == 0 and repeat["track_events"] == 0 and
            repeat["late_reads"] == 0 and repeat["refused_windows"] == 0):
        raise RuntimeError("CDDA deterministic cycle did not reset")
    for name, expected in contract.get("promotion_expected", {}).items():
        if final.get(name) != expected:
            raise RuntimeError(
                f"CDDA promotion {name} was {final.get(name)}, expected {expected}")

    process = process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1,
        "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "cue_sha256": build["artifacts"]["game_cue"]["sha256"],
        "track_audio_sha256": build["artifacts"]["stage1_audio"]["sha256"],
        "samples": samples,
        "bounded_stability_frames": (
            samples["repeat_idle"]["emulator_frame"] -
            samples["idle"]["emulator_frame"]),
        "track_command": {
            "track": 2,
            "command_returned": True,
            "post_command_frame_observed": samples["cdda_owned"]["relative_frame"],
            "classification": "EMULATOR_COMMAND_AND_OWNERSHIP_READBACK"
        },
        "final_scanout": {
            "width": 352, "height": 224,
            "screenshot": {"path": screenshot.relative_to(ROOT).as_posix(),
                           "sha256": sha256(screenshot),
                           "bytes": screenshot.stat().st_size},
        },
        "emulator": {
            "identity": "Yaba Sanshiro 1.20.37-2986eb",
            "evidence_tier": "ONE_EMULATOR",
            "process_id": process["pid"],
            "executable_sha256": sha256(executable),
            "settings_sha256": sha256(settings),
            "command_line": process["command_line"],
        },
        "human_review": contract.get("human_review_status", "PENDING"),
        "physical_saturn": "UNRUN",
        "result": "PASS",
    }
    output = output_root / f"run-{args.run}/readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
