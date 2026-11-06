#!/usr/bin/env python3
"""Boot game.cue on the pinned debug-rig Yaba Sanshiro and read frame cost (ONE_EMULATOR).

Owns only the process it starts. Saves and restores the shared yabause.ini. Yaba does not
model SH-2 bus wait states or VDP1 draw time, so ticks are not hardware timing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402

EXE = ROOT / ".deps/emulators/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34"
SHARED_INI = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
INI = SHARED_INI
BIN = ROOT / ".deps/joengine/Compiler/WINDOWS/bin"
COST = ["fields", "callbacks", "late_callbacks", "peak_fields", "work_ticks", "work_peak",
        "work_sum_low", "tcr", "vdp1_busy_at_entry"]
EXTRA = ["avsp_diag_live_frame", "avsp_diag_round1_presentation_commands_peak",
         "jo_current_palette_id", "avsp_diag_round1_native_composite_exhaustions"]


def symbols() -> dict[str, int]:
    table = {}
    for line in (ROOT / "game.map").read_text(errors="ignore").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].startswith("0x"):
            table[parts[1].lstrip("_")] = int(parts[0], 16)
    return table


def set_ini(values: dict[str, str]) -> None:
    lines = INI.read_text().splitlines()
    for key, value in values.items():
        hit = [i for i, line in enumerate(lines) if line.startswith(key + "=")]
        if hit:
            lines[hit[0]] = key + "=" + value
        else:
            lines.append(key + "=" + value)
    INI.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=240)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shot", type=Path)
    args = parser.parse_args()
    exe = next(EXE.rglob("yabasanshiro.exe"))
    # The rig reads one shared ini (Qt ignores APPDATA) and one fixed MCP port.
    if subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower().count("yabasanshiro"):
        raise SystemExit("another lane owns the emulator")
    backup = args.output.with_suffix(".ini.bak")
    shutil.copy2(INI, backup)
    cue = args.output.with_suffix(".cue")
    cue.write_text('FILE "%s" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n'
                   'FILE "%s" WAVE\n  TRACK 02 AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n'
                   % (ROOT / "game.iso", ROOT / "stage1_audio.wav"))
    set_ini({"General\\CdRom": "1", "General\\CdRomISO": str(cue).replace("\\", "/"),
             "Cartridge\\Type": "7", "autostart": "true", "Video\\VideoCore": "1",
             "Sound\\SoundCore": "0", "Advanced\\SH2Interpreter": "3"})
    table = symbols()
    process = subprocess.Popen([str(exe), "-nb", "-a", "-i", str(cue)], cwd=str(ROOT),
                               env=dict(os.environ))
    samples, result = [], {"tier": "ONE_EMULATOR", "exe": exe.name, "boot": False}
    try:
        mcp = Mcp("http://127.0.0.1:9640/mcp")
        deadline = time.time() + 45
        while True:
            try:
                mcp.initialize()
                break
            except Exception:
                if time.time() > deadline or process.poll() is not None:
                    raise
                time.sleep(0.5)
        try:
            mcp.call("resume")
        except Exception:
            pass
        end = time.time() + args.seconds
        while time.time() < end and process.poll() is None:
            row = {"t": round(time.time(), 1)}
            try:
                for name in COST:
                    row[name] = mcp.u32(table["avsp_diag_frame_cost_" + name])
                for name in EXTRA:
                    if name in table:
                        row[name] = mcp.u32(table[name])
                samples.append(row)
            except RuntimeError as error:
                result["last_read_error"] = str(error)
                result["raw"] = mcp.call("memory_read", address=hex(table["avsp_diag_frame_cost_tcr"]), length=4)[:200]
            time.sleep(5)
        result["boot"] = bool(samples) and samples[-1]["callbacks"] > 0
        if args.shot:
            result["shot"] = mcp.call("framebuffer_screenshot", path=str(args.shot))[:200]
    finally:
        shutil.copy2(backup, INI)
        result["samples"] = samples
        args.output.write_text(json.dumps(result, indent=1))
        if process.poll() is None:
            process.kill()
            try:
                process.wait(60)
            except subprocess.TimeoutExpired:
                result["kill_timeout"] = True
    result["alive_at_end"] = True
    result["samples"] = samples
    args.output.write_text(json.dumps(result, indent=1))
    print(json.dumps(result["samples"][-1] if samples else result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
