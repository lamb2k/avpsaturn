"""Yaba driver for the Wolverine sound checks (lane wv-sounds). Own Yaba copy only: it edits the yabause.ini next to its own exe and posts keys to its own window.
EMULATOR tier. The SCSP output is dumped by AVP_SCSP_RAW (saturn/audio/yaba_wav_dump.patch: raw 44.1 kHz s16le stereo of what the SCSP generated, whatever the sound driver does).
env: WVY_DIR (the folder with yaba/ and saves/; default D:/AvP-lanes/lane-wv-sounds), WVY_PORT (MCP port, default 9722), WVY_TITLE."""
import ctypes
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "saturn/rt"))
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import play_yaba as p            # key posting, window lookup (its module-level ini/port defaults are not used here)
from capture_frontend_cram import Mcp

D = pathlib.Path(os.environ.get("WVY_DIR", "D:/AvP-lanes/lane-wv-sounds"))
PORT = int(os.environ.get("WVY_PORT", "9722"))
NM = "E:/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"


def setup(cue, video="1", extra=None):
    ini = D / "yaba" / "yabause.ini"
    kv = {r"General\CdRomISO": cue, r"Debug\McpServerPort": str(PORT), r"Video\VideoCore": video, r"General\SaveStates": str(D / "saves").replace("\\", "/"),
          r"Memory\Path": str(D / "saves/bkram.bin").replace("\\", "/"), r"General\EnableEmulatedBios": "true", r"Cartridge\Type": "7", "autostart": "true", r"Sound\SoundCore": "1", r"Sound\Volume": "100",   # owner rule 11-10: audio on the real output, never muted (the SCSP dump is independent of it)
          r"General\UseSh2Cache": "false"}   # owner rule 11-10: every Yaba copy runs with UseSh2Cache=false; a running Yaba can rewrite its ini, so this is set before each launch
    kv.update(extra or {})
    out, seen = [], set()
    for l in ini.read_text(encoding="latin-1").splitlines():
        k = l.split("=")[0]
        if k in kv:
            out.append(f"{k}={kv[k]}"); seen.add(k)
        else:
            out.append(l)
    out += [f"{k}={v}" for k, v in kv.items() if k not in seen]
    ini.write_text("\r\n".join(out) + "\r\n", encoding="ascii")
    (D / "saves").mkdir(exist_ok=True)
    (D / "appdata").mkdir(exist_ok=True)


def start(raw):
    env = dict(os.environ, QT_OPENGL="desktop", APPDATA=str(D / "appdata"), AVP_SCSP_RAW=str(raw))
    return subprocess.Popen([str(D / "yaba" / "yabasanshiro.exe")], cwd=str(D / "yaba"), env=env)


def syms_of(elf):
    out = {}
    for l in subprocess.run([NM, elf], capture_output=True, text=True).stdout.splitlines():
        q = l.split()
        if len(q) == 3:
            out[q[2].lstrip("_")] = int(q[0], 16)
    return out


class Y:
    def __init__(self, proc, elf, title):
        self.proc, self.pid, self.syms = proc, proc.pid, syms_of(elf)
        self.m = Mcp(f"http://127.0.0.1:{PORT}/mcp")
        for _ in range(240):
            try:
                self.m.initialize(); break
            except Exception:
                time.sleep(0.5)
        self.h = None
        for _ in range(120):
            w = p.windows_of(self.pid)
            if w:
                self.h = max(w, key=lambda w: w[2] * w[3])[0]; break
            time.sleep(0.3)
        if self.h:
            ctypes.WinDLL("user32").SetWindowTextW(self.h, title)   # my own window handle only

    def read(self, a, n):
        for _ in range(200):
            try:
                return self.m.read(a, n)
            except RuntimeError:
                time.sleep(0.1)
        return self.m.read(a, n)

    def sym(self, s, off=0, n=4):
        return int.from_bytes(self.read(self.syms[s] + off, n), "big")

    def ram(self, off, n=1):
        return self.read(self.syms["RAMB"] + off, n)

    def ram16(self, off):
        return int.from_bytes(self.ram(off, 2), "big")

    def v(self):
        try:
            return int.from_bytes(self.read(self.syms["sat_dbg"] + 8, 4), "big")
        except Exception:
            return -1

    def write(self, addr, data):
        self.m.call("memory_write", address=hex(addr), bytes=data.hex() if isinstance(data, (bytes, bytearray)) else data)

    def wsym(self, s, data, off=0):
        self.write(self.syms[s] + off, bytes(data))

    def key(self, n, d):
        vk = p.VK[n]
        sc = p.u32.MapVirtualKeyW(vk, 0)
        p.u32.PostMessageW(self.h, p.WM_KEYDOWN if d else p.WM_KEYUP, vk, 1 | (sc << 16) | (0 if d else 3 << 30))

    def pulse(self, n, s=0.08):
        self.key(n, 1); time.sleep(s); self.key(n, 0); time.sleep(0.25)

    def wait(self, pred, timeout=120, step=0.5):
        t = time.time()
        while time.time() - t < timeout:
            if pred():
                return True
            time.sleep(step)
        return False

    def shot(self, path):
        self.m.call("framebuffer_screenshot", path=str(path))

    def stop(self):
        try:
            self.proc.terminate()
        except Exception:
            pass
