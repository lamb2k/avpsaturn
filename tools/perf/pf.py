"""AvP PERF lane harness. Own Yaba copy E:/AvP/learning/lane-perf/yaba, port 9732, window 'AvP PERF: <run> [port 9732]'.
Input only by PostMessage to the window of the pid started here. Launched minimised without activation (SW_SHOWMINNOACTIVE)."""
import os, subprocess, sys, time, ctypes, json
sys.argv_save = sys.argv; sys.argv = ["x"]
sys.path.insert(0, "E:/AvP/worktrees/integration/saturn/rt"); sys.path.insert(0, "E:/AvP/worktrees/integration/tools")
import play_yaba as p
from capture_frontend_cram import Mcp
sys.argv = sys.argv_save
D = "E:/AvP/learning/lane-perf"; PORT = 9732; YDIR = f"{D}/yaba"; YAPP = f"{D}/appdata"; YSAVE = f"{D}/saves"
NM = "E:/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
os.makedirs(YAPP, exist_ok=True); os.makedirs(YSAVE, exist_ok=True)
def syms(elf):
    out = {}
    for l in subprocess.run([NM, elf], capture_output=True, text=True).stdout.splitlines():
        t = l.split()
        if len(t) == 3: out.setdefault(t[2].lstrip("_"), int(t[0], 16))
    return out
def setini(cue, cache):
    path = f"{YDIR}/yabause.ini"; lines = open(path, newline="").read().replace("\r\n", "\n").split("\n")
    kv = {r'General\CdRomISO': cue, r'Debug\McpServerPort': str(PORT), r'Debug\McpServerEnabled': 'true', r'Video\VideoCore': '1', r'Sound\SoundCore': os.environ.get('PF_SOUND','1'),
          r'Sound\Volume': '100', r'General\UseSh2Cache': cache, r'General\SaveStates': YSAVE, r'Memory\Path': f'{YSAVE}/bkram.bin'}
    out = []; seen = set()
    for l in lines:
        k = l.split('=', 1)[0]
        if k in kv: out.append(f"{k}={kv[k]}"); seen.add(k)
        else: out.append(l)
    for k, v in kv.items():
        if k not in seen: out.append(f"{k}={v}")
    open(path, "w", newline="").write("\r\n".join(out) + "\r\n")
def title(pid, text):
    h = max(p.windows_of(pid), key=lambda w: w[2] * w[3])[0]
    ctypes.windll.user32.SetWindowTextW(h, text)
def kill_mine():
    """Close any earlier Yaba of this lane (exe path under lane-perf) so exactly one instance answers on the port."""
    ps = "Get-CimInstance Win32_Process -Filter \"Name='yabasanshiro.exe'\" | Where-Object { $_.ExecutablePath -like '*lane-perf*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
    time.sleep(2)
def boot(cue, what, cache="true"):
    kill_mine()
    setini(cue, cache)
    env = dict(os.environ, QT_OPENGL="desktop", APPDATA=YAPP)
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 7
    y = subprocess.Popen([f"{YDIR}/yabasanshiro.exe"], cwd=YDIR, env=env, startupinfo=si, creationflags=0x4000)   # BELOW_NORMAL priority (coordinator 11-10: owner is play-testing)
    for _ in range(120):
        time.sleep(2)
        if p.windows_of(y.pid): break
    time.sleep(3)
    try: title(y.pid, f"AvP PERF: {what} cache={cache} [port {PORT}]")
    except Exception as e: print('title failed', e)
    # A minimised Yaba stalls its frame pump. Restore without activation and send to the bottom of the z-order (no focus, no cover).
    try:
        h = max(p.windows_of(y.pid), key=lambda w: w[2] * w[3])[0]
        ctypes.windll.user32.ShowWindow(h, 4); ctypes.windll.user32.SetWindowPos(h, 1, 0, 0, 0, 0, 0x13)
    except Exception as e: print('restore failed', e)
    return y
class Y:
    def __init__(self, pid, elf):
        self.pid = pid; self.s = syms(elf)
        self.m = Mcp(f"http://127.0.0.1:{PORT}/mcp"); self.m.initialize()
        for _ in range(60):
            if p.windows_of(pid): break
            time.sleep(2)
        self.h = max(p.windows_of(pid), key=lambda w: w[2] * w[3])[0]
        self.down = set()
    def key(self, n, d):
        vk = p.VK[n]; sc = p.u32.MapVirtualKeyW(vk, 0)
        p.u32.PostMessageW(self.h, p.WM_KEYDOWN if d else p.WM_KEYUP, vk, 1 | (sc << 16) | (0 if d else 3 << 30))
    def set(self, names):
        names = set(names)
        for n in list(self.down - names): self.key(n, 0); self.down.discard(n)
        for n in names - self.down: self.key(n, 1); self.down.add(n)
    def pulse(self, n, s=0.08, gap=0.25): self.key(n, 1); time.sleep(s); self.key(n, 0); time.sleep(gap)
    def ready(self, vb=600):
        while True:
            try:
                if self.m.read(self.s["sat_dbg"], 4) == b"SATR" and int.from_bytes(self.m.read(self.s["sat_dbg"] + 8, 4), "big") > vb: return
            except Exception: pass
            time.sleep(1)
    def u32(self, name, off=0): return int.from_bytes(self.m.read(self.s[name] + off, 4), "big")
    def arc(self, a, n=2): return int.from_bytes(self.m.read(self.s["RAMB"] + (a - 0xff0000), n), "big")
    def w(self, a, size, v): self.m.call("memory_write", address=hex(self.s["RAMB"] + (a - 0xff0000)), size=size, value=hex(v))
    def vb(self): return int.from_bytes(self.m.read(self.s["sat_dbg"] + 8, 4), "big")
