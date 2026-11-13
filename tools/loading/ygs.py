"""Own Ymir (E:/AvP/learning/lane-loading/ymir): launch no-activate, pad by ymir_pad.txt, window grabs, trace.log parse. Never touches other lanes' Ymir or ini."""
import subprocess, sys, time, os, ctypes, re
HERE = 'E:/AvP/learning/lane-loading/ymir'
sys.path.insert(0, HERE)
import wincap
u = wincap.u
B = {'right': 0x8000, 'left': 0x4000, 'down': 0x2000, 'up': 0x1000, 'start': 0x0800, 'a': 0x0400, 'c': 0x0200, 'b': 0x0100, 'r': 0x80, 'x': 0x40, 'y': 0x20, 'z': 0x10, 'l': 0x08}
def pad(*names):
    m = 0
    for n in names: m |= B[n]
    open(os.environ.get('AVP_PAD', HERE + '/ymir_pad.txt'), 'w').write('%x' % m)
class Y:
    def __init__(self, cue, label=None, prof=None):
        pad()
        si = subprocess.STARTUPINFO(); si.dwFlags |= 1; si.wShowWindow = 4   # SW_SHOWNOACTIVATE
        self.pr = subprocess.Popen([os.environ.get('GS_EXE', f'{HERE}/run/ymir-sdl3.exe'), '-p', prof or f'{HERE}/prof', '-d', cue], cwd=f'{HERE}/run', startupinfo=si,
                                   stdout=open(os.environ.get('AVP_TRACE','').replace('trace.log','ymir_run.log') or f'{HERE}/ymir_run.log', 'w'), stderr=subprocess.STDOUT)
        self.t0 = time.time(); self.h = None; self.labelled = False; self.lab = label
    def win(self):
        ws = [w for w in wincap.windows_of(self.pr.pid) if w[1] > 200]
        self.h = max(ws, key=lambda x: x[1] * x[2])[0] if ws else None
        if self.h and self.lab and not self.labelled:
            try: u.SetWindowTextW(self.h, self.lab); self.labelled = True
            except Exception: pass
        return self.h
    def shot(self, path):
        if self.win():
            try: wincap.shot(self.h, path)
            except Exception as e: print('shot err', e)
    def kill(self):
        pad()
        try: self.pr.terminate()
        except Exception: pass
