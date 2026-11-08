#!/usr/bin/env python
"""Drive the Saturn image under Yaba with real pad input: key messages posted to Yaba's OWN window handle, never global input.
Path: PostMessage(WM_KEYDOWN) -> Yaba's Qt key handler -> emulated Saturn pad -> SMPC INTBACK -> pad.c -> the game's latch (0x804000/0x804020).
Tier: EMULATOR.
usage: play_yaba.py WORK SCRIPT.py [seconds]
SCRIPT.py defines step(vblank, s) called about every 50 ms; s has press(name), release(name), set(names), latch(), ram8(off), ram16(off), shot(name), log(...), stop().
Pad names: up right down left start a b c x y z l r. The build must not use -DSAT_INPUT_SCRIPT."""
import ctypes
import ctypes.wintypes as wt
import importlib.util
import os
import pathlib
import re
import socket
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from capture_frontend_cram import Mcp

JO = pathlib.Path("E:/AvP/worktrees/saturn-hw/.deps")
EXE = pathlib.Path(os.environ.get("YABA_EXE", JO / "emulators/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-d7767591/yabasanshiro.exe"))
NM = JO / "joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
# A second instance: YABA_EXE in its own folder with a yabause.ini beside it (Qt then uses that file), YABA_INI that file, YABA_PORT its Debug\McpServerPort.
INI = pathlib.Path(os.environ["YABA_INI"]) if os.environ.get("YABA_INI") else pathlib.Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
PORT = int(os.environ.get("YABA_PORT", "9640"))
# Windows virtual keys for the bindings in yabause.ini (Port 1 pad).
VK = dict(up=0x57, right=0x44, down=0x53, left=0x41, r=0x36, l=0x35, start=0x0d, a=0x47, b=0x48, c=0x4a, x=0x54, y=0x59, z=0x55)
QT = dict(start=16777220)   # Qt key code where it differs from the virtual key
VK.update(p2_up=0x49, p2_right=0x4c, p2_down=0x4b, p2_left=0x4a, p2_start=0x4f, p2_a=0x5a, p2_b=0x58, p2_c=0x43, p2_x=0x56)   # second pad, YABA_P2=1: keys only pad_set uses
P2_INI = dict(enumerate((0x49, 0x4c, 0x4b, 0x4a, 0x3a, 0x3b, 0x4f, 0x5a, 0x58, 0x43, 0x56, 0x3c, 0x3d)))   # Yaba's pad key order, as port 1 in yabause.ini
WM_KEYDOWN, WM_KEYUP = 0x100, 0x101
u32 = ctypes.WinDLL("user32", use_last_error=True)
u32.MapVirtualKeyW.restype = wt.UINT
u32.PostMessageW.argtypes = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def windows_of(pid):
    found = []
    def cb(h, _):
        p = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u32.IsWindowVisible(h):
            n = ctypes.create_unicode_buffer(200)
            u32.GetWindowTextW(h, n, 200)
            r = wt.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            found.append((h, n.value, r.right - r.left, r.bottom - r.top))
        return True
    u32.EnumWindows(ENUM(cb), 0)
    return found


class RetryMcp(Mcp):
    """memory_read can answer empty while the core is starting or inside a long CD read."""
    def read(self, a, n):
        for tries in range(600):
            try:
                return Mcp.read(self, a, n)
            except RuntimeError:
                time.sleep(0.1)
        return Mcp.read(self, a, n)


def port_busy():
    s = socket.socket()
    s.settimeout(0.3)
    busy = s.connect_ex(("127.0.0.1", PORT)) == 0
    s.close()
    return busy


def port_owner():
    """The pid listening on the MCP port. Two lanes can both see the port free and both start Yaba: only one binds it, and the other's bot would then drive the wrong machine."""
    for l in subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout.splitlines():
        p = l.split()
        if len(p) >= 5 and p[1].endswith(f":{PORT}") and p[3] == "LISTENING":
            return int(p[4])
    return None


class Session:
    def __init__(self, m, syms, hwnd, work):
        self.m, self.syms, self.hwnd, self.work = m, syms, hwnd, work
        self.down = set()
        self.done = False
        (work / "shots").mkdir(exist_ok=True)

    def _key(self, name, down):
        if os.environ.get("YABA_PAD") == "mcp":   # patched exe (saturn/rt/yaba_pad_set.patch): tool calls PerKeyDown/PerKeyUp, as the key handler does
            self.held = getattr(self, "held", set())
            (self.held.add if down else self.held.discard)(QT.get(name, VK[name]))
            self.m.call("pad_set", keys=sorted(self.held))
            return
        vk = VK[name]
        scan = u32.MapVirtualKeyW(vk, 0)
        lp = 1 | (scan << 16) | (0 if down else (3 << 30))
        if not u32.PostMessageW(self.hwnd, WM_KEYDOWN if down else WM_KEYUP, vk, lp):
            raise OSError(ctypes.get_last_error())

    def press(self, n):
        if n not in self.down:
            self.down.add(n); self._key(n, True)

    def release(self, n):
        if n in self.down:
            self.down.discard(n); self._key(n, False)

    def set(self, names):
        names = set(names)
        for n in list(self.down - names):
            self.release(n)
        for n in names - self.down:
            self.press(n)

    def pulse(self, n, secs=0.05):
        """Down and up without going through MCP, whose reads each wait for a frame."""
        self._key(n, True); time.sleep(secs); self._key(n, False)

    def word(self, sym, off=0, n=4):
        return int.from_bytes(self.m.read(self.syms[sym] + off, n), "big")

    def ram8(self, off):
        return self.m.read(self.syms["RAMB"] + off, 1)[0]

    def ram16(self, off):
        return int.from_bytes(self.m.read(self.syms["RAMB"] + off, 2), "big")

    def ram(self, off, n):
        return self.m.read(self.syms["RAMB"] + off, n)

    def latch(self):
        return dict(raw=self.word("sat_pad_raw"), in0=self.word("in0", 0, 2), in2=self.word("in2", 0, 2))

    def shot(self, name):
        self.m.call("framebuffer_screenshot", path=str(self.work / "shots" / f"{name}.png"))

    def log(self, *a):
        print(f"[{time.time() - self.t0:6.1f}s v{self.v}]", *a, flush=True)

    def stop(self):
        self.done = True


def main():
    work = pathlib.Path(sys.argv[1])
    spec = importlib.util.spec_from_file_location("play_script", sys.argv[2])
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 55
    while port_busy():
        print("Yaba lock held, waiting", flush=True); time.sleep(10)
    syms = {}
    for l in subprocess.run([str(NM), os.environ.get("YABA_ELF", str(work / "sat.elf"))], capture_output=True, text=True).stdout.splitlines():
        p = l.split()
        if len(p) == 3:
            syms[p[2].lstrip("_")] = int(p[0], 16)
    orig = INI.read_bytes()
    set_ = {r"Video\VideoCore": os.environ.get("YABA_VIDEO", "4"), r"Sound\SoundCore": os.environ.get("YABA_SOUND", "0"), r"General\CdRomISO": os.environ.get("YABA_CUE", str(work / "sat.cue")).replace("\\", "/"), "autostart": "true", r"Cartridge\Type": "7", r"General\EnableEmulatedBios": "true"}
    out = [f"{l.split('=')[0]}={set_[l.split('=')[0]]}" if l.split("=")[0] in set_ else l for l in orig.decode("latin-1").splitlines()]
    if os.environ.get("YABA_P2"):
        out = [l for l in out if not l.startswith("Input\\Port\\2\\")]
        at = next(i for i, l in enumerate(out) if l.startswith("Input\\Port\\1\\"))
        out[at:at] = ["Input\\Port\\2\\Id\\1\\Type=2", "Input\\Port\\2\\Id\\1\\Device=keyboard", "Input\\Port\\2\\Id\\1\\DeviceName=Keyboard"] + [f"Input\\Port\\2\\Id\\1\\Controller\\2\\Key\\{k}={v}" for k, v in P2_INI.items()]
    INI.write_bytes(("\n".join(out) + "\n").encode("latin-1"))
    proc = subprocess.Popen([str(EXE)], cwd=str(EXE.parent))
    s = None
    global foreign
    foreign = False
    last_own = time.time()
    try:
        m = RetryMcp(f"http://127.0.0.1:{PORT}/mcp")
        t0 = time.time()
        while True:
            try:
                m.initialize(); break
            except Exception:
                if time.time() - t0 > 120: raise
                time.sleep(0.3)
        if port_owner() != proc.pid:
            print(f"port {PORT} belongs to another Yaba, this leg did not run", flush=True)
            foreign = True
            return
        print("tools", [x["name"] for x in m._post("tools/list", {})["result"]["tools"]], flush=True)
        wins = []
        while not wins and time.time() - t0 < 130:
            time.sleep(0.2)
            wins = windows_of(proc.pid)
        print("windows", wins, flush=True)
        hwnd = max(wins, key=lambda w: w[2] * w[3])[0]
        if os.environ.get("YABA_LOAD"):   # one fresh process per leg, as docs/EMULATOR_MCP_CAPTURE.md says
            time.sleep(3)
            m.call("pause")
            print(m.call("load_state", slot=int(os.environ["YABA_LOAD"]))[:160], flush=True)
            m.call("resume")
        s = Session(m, syms, hwnd, work)
        s.t0 = t0
        s.v = 0
        while time.time() - t0 < secs and not s.done:
            try:
                d = m.read(syms["sat_dbg"], 40)
            except RuntimeError:   # the core is not up yet
                time.sleep(0.5); continue
            s.v = int.from_bytes(d[8:12], "big")
            if time.time() - last_own > 15:
                last_own = time.time()
                if port_owner() != proc.pid:
                    print(f"port {PORT} lost to another Yaba, leg void", flush=True)
                    foreign = True
                    return
            fatal = int.from_bytes(d[28:32], "big")
            if fatal:
                det = int.from_bytes(d[32:36], "big")
                s.log(f"FATAL {fatal:#x} detail {det:#x}")
                getattr(script, "fatal", lambda *a: None)(s, fatal, det)
                break
            script.step(s.v, s)
            time.sleep(float(os.environ.get("POLL", "0.03")))
        getattr(script, "end", lambda s: None)(s)
    finally:
        if s:
            s.set([])
        proc.kill(); proc.wait(10)
        text = orig.decode("latin-1")
        for key, value in ((r"Video\VideoCore", "4"), (r"Sound\SoundCore", "1")):
            text = re.sub(rf"(?m)^{re.escape(key)}=.*$", (key + "=" + value).replace(chr(92), chr(92) * 2), text)
        INI.write_bytes(text.encode("latin-1"))


if __name__ == "__main__":
    main()
    if foreign:
        sys.exit(3)   # no save was taken from this leg; the caller repeats it
