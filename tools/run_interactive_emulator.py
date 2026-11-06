#!/usr/bin/env python3
"""Saturn-emulator tier: boot a staged image, sample diagnostics, take frames.

usage: run_interactive_emulator.py STAGE_DIR SECONDS [SHOT_EVERY_SECONDS]
STAGE_DIR holds game.cue/game.iso/stage1_audio.wav/game.map. Output goes there.
Touches only the process it starts; restores the emulator ini afterwards.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402

EXE = next((ROOT / ".deps/emulators").glob(
    "yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34/**/yabasanshiro.exe"))
INI = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
SYMS = ["avsp_diag_runtime_ready", "avsp_diag_live_frame_stage",
        "avsp_diag_live_frame", "avsp_diag_round1_tick_total",
        "avsp_diag_round1_tick_last", "avsp_diag_round1_failure_count",
        "avsp_round1_containment"]


def symbols(path):
    out = {}
    for line in path.read_text(errors="replace").splitlines():
        m = re.match(r"\s+0x([0-9a-f]{8,16})\s+_?(\w+)$", line)
        if m and m.group(2) in SYMS:
            out[m.group(2)] = int(m.group(1), 16)
    return out


def main():
    stage, seconds = Path(sys.argv[1]), float(sys.argv[2])
    every = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    syms = symbols(stage / "game.map")
    # One debug port and one ini are shared across lanes: never run alongside.
    while subprocess.run(["tasklist", "/FI", "IMAGENAME eq yabasanshiro.exe"],
                         capture_output=True, text=True
                         ).stdout.lower().count("yabasanshiro.exe"):
        print("emulator busy, waiting", flush=True)
        time.sleep(10)
    original = INI.read_bytes()
    text = original.decode("latin-1")
    for key, value in (("Video\\VideoCore", "1"), ("Sound\\SoundCore", "0"),
                       ("autostart", "true")):
        text = re.sub(rf"(?m)^{re.escape(key)}=.*$",
                      (key + "=" + value).replace("\\", "\\\\"), text)
    INI.write_bytes(text.encode("latin-1"))
    proc = subprocess.Popen([str(EXE), "-nb", "-a", "-i", str(stage / "game.cue")],
                            cwd=str(stage))
    rows = []
    try:
        mcp = Mcp("http://127.0.0.1:9640/mcp")
        deadline = time.time() + 40
        while True:
            try:
                mcp.initialize()
                break
            except Exception:
                if time.time() > deadline:
                    raise
                time.sleep(0.5)
        start = time.time()
        next_shot = 0.0
        while time.time() - start < seconds and proc.poll() is None:
            row = {"t": round(time.time() - start, 1)}
            try:
                for name, addr in syms.items():
                    if name != "avsp_round1_containment":
                        row[name.replace("avsp_diag_", "")] = int.from_bytes(
                            mcp.read(addr, 4), "big", signed=True)
                row["contained"] = mcp.u32(syms["avsp_round1_containment"] + 4)
            except RuntimeError as error:  # memory not readable during boot
                row["read_error"] = str(error)
            if row["t"] >= next_shot:
                shot = stage / f"t{int(row['t']):04}.png"
                row["shot"] = mcp.call("framebuffer_screenshot", path=str(shot))[:120]
                next_shot += every
            rows.append(row)
            print(row, flush=True)
            time.sleep(2)
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(15)
        INI.write_bytes(original)
        (stage / "readback.json").write_text(json.dumps(rows, indent=0))


if __name__ == "__main__":
    main()
