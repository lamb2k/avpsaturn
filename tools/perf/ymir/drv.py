"""usage: drv.py NAME "ROUTE"   (env GS_CUE, GS_EXE, GS_PROF, GS_OFF.. from runp.sh)
Drives my own Ymir by the pad file only. ROUTE is a space separated list:
  w:N        wait until the game's vblank counter reaches N (from boot)
  r:N        wait N vblanks from now
  s:N        wait N seconds
  t:keys:g   tap keys (plus separated, e.g. a+right) then wait g seconds
  h:keys:S   hold keys for S seconds
  k:         set the player's health to 0 (RAM poke on my own Ymir process; a KO)
  v:         set the player's health to 0x65 (held)
  x:reset | x:dump   command file for the profiling Ymir (dump goes to hwprof_NAME.txt)
  p:label    screenshot to runs/NAME/label.png
Screenshots every 10 s go to runs/NAME/auto_NNNN.png. gs.log lines and run.log are kept."""
import sys, time, os, shutil
sys.path.insert(0, 'E:/AvP/learning/lane-perf-hw/ymir_hw')
import ygs, memscan
from ygs import tap, pad
name, route = sys.argv[1], sys.argv[2].split()
cue = os.environ['GS_CUE']
out = f'{ygs.HERE}/runs/{name}'; os.makedirs(out, exist_ok=True)
y = ygs.Y(cue)
lf = open(out + '/run.log', 'w')
t0 = time.time(); last = [0.0]; n = [0]
base = [None]
def log(*a):
    s = f'{time.time()-t0:7.1f} vb={y.vb()} ' + ' '.join(str(x) for x in a); lf.write(s + '\n'); lf.flush(); print(s, flush=True)
def auto():
    if time.time() - last[0] > 10:
        last[0] = time.time(); n[0] += 1; y.shot(f'{out}/auto_{n[0]:04d}.png')
        if not getattr(y, '_lab', 0) and y.win(): y._lab = 1; y.label('PERF-HW lane Ymir - ' + name)
def sleep(s):
    e = time.time() + s
    while time.time() < e:
        auto(); time.sleep(0.2)
def ram():
    if base[0]: return base[0]
    OFF = int(os.environ.get('GS_OFF', '0'), 0); OFFR = int(os.environ.get('GS_OFFR', str(OFF)), 0)
    p = memscan.Proc(y.pr.pid)
    for c in [h - 0xDEA64 - OFF for h in p.find(b'SATR')]:
        d = p.read(c + 0xDEC14 + OFFR + 0x8018, 2); l = y.last()
        if d and l and abs(((d[0] - int(l['v8'])) + 128) % 256 - 128) <= 3:
            base[0] = (p, c + 0xDEC14 + OFFR); return base[0]
    return None
try:
    for st in route:
        k, _, a = st.partition(':')
        if k == 'w':
            while y.vb() < int(a) and y.pr.poll() is None: auto(); time.sleep(0.3)
        elif k == 'r':
            v0 = y.vb()
            while y.vb() < v0 + int(a) and y.pr.poll() is None: auto(); time.sleep(0.3)
        elif k == 's': sleep(float(a))
        elif k == 't':
            keys, _, g = a.partition(':'); ks = [x for x in keys.split('+') if x]
            pad(*ks); sleep(0.25); pad(); sleep(float(g or 0.6))
        elif k == 'h':
            keys, _, g = a.partition(':'); pad(*[x for x in keys.split('+') if x]); sleep(float(g)); pad()
        elif k in ('k', 'v'):
            r = ram()
            if r: r[0].write(r[1] + 0x83c0, b'\x00\x00' if k == 'k' else b'\x00\x65'); log('health', k)
            else: log('no ram base')
        elif k == 'x':
            open(ygs.HERE + '/hw_cmd.txt', 'w').write(a.replace('_', ' ') + (' ' + name if a == 'dump' else '')); log('cmd', a)
        elif k == 'p':
            y.shot(f'{out}/{a}.png'); log('shot', a, y.last())
        log('step', st)
    log('done'); y.shot(out + '/last.png')
finally:
    y.kill(); time.sleep(1)
    try: shutil.copy(ygs.HERE + '/gs.log', out + '/gs.log')
    except Exception as e: print(e)
