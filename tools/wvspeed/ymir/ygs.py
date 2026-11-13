"""Own Ymir (E:/AvP/learning/lane-wv-speed/ymir_wv): launch no-activate, scripted pad via ymir_pad.txt, window grabs. Never touches other lanes' Ymir or ini."""
import subprocess, sys, time, os, ctypes, re
HERE = 'E:/AvP/learning/lane-wv-speed/ymir_wv'
sys.path.insert(0, HERE)
import wincap
u = wincap.u
B = {'right': 0x8000, 'left': 0x4000, 'down': 0x2000, 'up': 0x1000, 'start': 0x0800, 'a': 0x0400, 'c': 0x0200, 'b': 0x0100, 'r': 0x80, 'x': 0x40, 'y': 0x20, 'z': 0x10, 'l': 0x08}
def pad(*names):
    m = 0
    for n in names: m |= B[n]
    open(HERE + '/ymir_pad.txt', 'w').write('%x' % m)
def tap(*names, hold=0.2, gap=0.6):
    pad(*names); time.sleep(hold); pad(); time.sleep(gap)
class Y:
    def __init__(self, cue, secs_max=3600):
        for f in ('gs.log',):
            try: os.remove(f'{HERE}/{f}')
            except OSError: pass
        pad()
        si = subprocess.STARTUPINFO(); si.dwFlags |= 1; si.wShowWindow = 4   # SW_SHOWNOACTIVATE
        self.pr = subprocess.Popen([os.environ.get('GS_EXE', f'{HERE}/run/ymir-sdl3.exe'), '-p', os.environ.get('GS_PROF', f'{HERE}/prof'), '-d', cue], cwd=f'{HERE}/run', startupinfo=si,
                                   stdout=open(f'{HERE}/ymir_run.log', 'w'), stderr=subprocess.STDOUT)
        self.t0 = time.time()
        self.h = None
    def label(self, text):
        if self.win():
            u.SetWindowTextW(self.h, text)
    def win(self):
        ws = [w for w in wincap.windows_of(self.pr.pid) if w[1] > 200]
        self.h = max(ws, key=lambda x: x[1] * x[2])[0] if ws else None
        return self.h
    def shot(self, path):
        if self.win():
            try: wincap.shot(self.h, path)
            except Exception as e: print('shot err', e)
    def last(self):
        """last V line of gs.log as dict"""
        try:
            with open(f'{HERE}/gs.log', 'rb') as f:
                f.seek(0, 2); n = f.tell(); f.seek(max(0, n - 60000)); lines = f.read().decode(errors='ignore').splitlines()
        except OSError: return None
        for l in reversed(lines):
            if l.startswith('V '):
                d = dict(re.findall(r'(\w+)=(\S+)', l)); d['vb'] = int(l.split()[1]); return d
        return None
    def vb(self):
        d = self.last(); return d['vb'] if d else 0
    def stage(self):
        d = self.last(); return int(d['st'], 16) if d else 0
    def kill(self):
        pad()
        try: self.pr.terminate()
        except Exception: pass
