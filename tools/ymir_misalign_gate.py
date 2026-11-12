#!/usr/bin/env python3
"""Strict-Ymir data misalignment gate. The patched Ymir (lane copy ymir_strict / ymir_vram2, sh2.cpp AvpLogMisalign) appends one line per distinct (PC, width, kind, CPU) to
E:/AvP/learning/lane-hwboot/ymir_misalign.log when an SH-2 makes a 16/32 bit access at an address that is not a multiple of the width:
    READ SH2-M PC=060A128E addr=060A128E 32-bit
The emulator still performs the access (a real SH-2 raises an address error), so the log is the only trace. Lines with addr == PC are the emulator's own instruction
fetches at a 2 mod 4 PC, not data accesses, and are filtered. Anything else is a data access and fails the gate.
Usage:
  ymir_misalign_gate.py --check LOG                       parse an existing log
  ymir_misalign_gate.py --run CUE [--secs N] [--keys SCHEDULE] [--exe EXE] [--profile DIR] [--log LOG]
      launch strict Ymir (SW_SHOWNOACTIVATE, keys posted to its own window only), run N seconds, then check the log. Default route: boot, menu, ARCADE start, stage 1, KO, continue
      with a different character (the keys of the fix7n2 runs); SCHEDULE is 'G@15,J@62,...' (key@second; G start, J A, D right, A left).
Exit 1 on any data access."""
import argparse, os, re, subprocess, sys, time, ctypes, ctypes.wintypes as w

LOG = "E:/AvP/learning/lane-hwboot/ymir_misalign.log"
DEFAULT_KEYS = ",".join([f"G@{t}" for t in (15, 25, 35, 45, 55)] + [f"J@{t}" for t in (62, 66, 70, 74, 78, 82, 86, 90)] + ["G@130", "D@133", "D@135", "J@137"])

def check(path):
    data, fetch = [], 0
    for l in open(path, errors="replace"):
        m = re.match(r"(READ|WRITE)\s+(\S+)\s+PC=([0-9A-Fa-f]+)\s+addr=([0-9A-Fa-f]+)\s+(\d+)-bit", l)
        if not m:
            continue
        kind, who, pc, addr, bits = m.groups()
        if int(pc, 16) == int(addr, 16):
            fetch += 1
            continue
        data.append(l.strip())
    print(f"ymir misalign log {path}: {fetch} instruction fetch artefacts (filtered), {len(data)} data accesses")
    for d in data[:40]:
        print("  DATA", d)
    return len(data)

def run(cue, secs, keys, exe, profile, log):
    u = ctypes.WinDLL("user32")
    if os.path.exists(log):
        os.remove(log)
    si = subprocess.STARTUPINFO(); si.dwFlags |= 1; si.wShowWindow = 4   # SW_SHOWNOACTIVATE
    args = [exe] + (["-p", profile] if profile else []) + ["-d", cue]
    pr = subprocess.Popen(args, cwd=os.path.dirname(exe), startupinfo=si, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    sched = sorted((float(k.split("@")[1]), k.split("@")[0]) for k in keys.split(",") if k)
    t0 = time.time()

    def windows(pid):
        res = []
        @ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        def cb(h, _):
            p = w.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value == pid and u.IsWindowVisible(h):
                r = w.RECT(); u.GetWindowRect(h, ctypes.byref(r)); res.append((h, r.right - r.left))
            return True
        u.EnumWindows(cb, 0)
        return [x for x in res if x[1] > 200]
    try:
        while time.time() - t0 < secs and pr.poll() is None:
            time.sleep(0.5); t = time.time() - t0
            ws = windows(pr.pid)
            h = max(ws, key=lambda x: x[1])[0] if ws else None
            while sched and sched[0][0] <= t and h:
                u.PostMessageW(h, 0x7, 0, 0)   # WM_SETFOCUS for SDL's own focus state, own window only
                _, k = sched.pop(0); vk = ord(k[0].upper()); sc = u.MapVirtualKeyW(vk, 0)
                u.PostMessageW(h, 0x100, vk, 1 | (sc << 16)); time.sleep(0.12); u.PostMessageW(h, 0x101, vk, 1 | (sc << 16) | (3 << 30))
    finally:
        pr.terminate()
        time.sleep(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check"); ap.add_argument("--run"); ap.add_argument("--secs", type=float, default=200)
    ap.add_argument("--keys", default=DEFAULT_KEYS)
    ap.add_argument("--exe", default="E:/AvP/learning/lane-hwboot/ymir_strict/ymir-sdl3.exe")
    ap.add_argument("--profile", default="E:/AvP/learning/lane-hwboot/ymir_prof")
    ap.add_argument("--log", default=LOG)
    a = ap.parse_args()
    if a.run:
        run(a.run, a.secs, a.keys, a.exe, a.profile, a.log)
        if not os.path.exists(a.log):
            print("no misalign log written: the patched Ymir wrote nothing (the game did not boot, or this exe lacks the patch)"); return 1
        return 1 if check(a.log) else 0
    if a.check:
        return 1 if check(a.check) else 0
    ap.print_help(); return 2

if __name__ == "__main__":
    sys.exit(main())
