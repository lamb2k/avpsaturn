"""route.py NAME CUE "STEPS"   (EMULATED): drive the loading-lane Ymir by the pad file only; every wait is in emulated frames (trace.log VB lines), so a route repeats.
STEPS, space separated:
  f:N      wait until emulated frame N (from power-on)       r:N   wait N frames from now
  t:keys:hold:gap   tap keys (plus separated) for hold frames, then wait gap frames          h:keys:N  hold keys N frames
  q:S      wait until the CD has been idle S seconds after at least one more sector read (a load finished)
  p:label  screenshot runs/NAME/label.png (and the frame number)
  m:label  note a marker (label, frame) in trace marks.txt
Screenshots every 20 s go to runs/NAME/auto_NNN.png; the window title is relabelled every few seconds (Ymir resets it)."""
import sys, time, os, shutil, re
sys.path.insert(0, 'E:/AvP/learning/lane-loading/ymir')
import ygs, memscan
name, cue, route = sys.argv[1], sys.argv[2], sys.argv[3].split()
HERE = ygs.HERE
out = f'{HERE}/runs/{name}'; os.makedirs(out, exist_ok=True)
try: os.remove(f'{HERE}/trace.log')
except OSError: pass
y = ygs.Y(cue, label='LOADING lane Ymir (EMULATED) - ' + name)
class Tail:
    def __init__(self, p): self.p = p; self.pos = 0; self.vb = 0; self.sect = 0; self.lastsect_vb = 0; self.f = None; self.nsect = 0
    def poll(self):
        if self.f is None:
            if not os.path.exists(self.p): return
            self.f = open(self.p, 'rb')
        self.f.seek(self.pos); data = self.f.read()
        if not data: return
        cut = data.rfind(b'\n') + 1
        if not cut: return
        self.pos += cut
        for l in data[:cut].split(b'\n'):
            if l.rstrip().endswith(b' VB'): self.vb += 1
            elif b' SECT ' in l: self.nsect += 1; self.lastsect_vb = self.vb
T = Tail(f'{HERE}/trace.log')
lf = open(out + '/run.log', 'w')
_base = [None]
def ram():
    """host address of the game's 64 KB RAM (RAMB): 'SATR' (sat_dbg.magic) found in the Ymir process, shifted by RAMB - sat_dbg from the build's map (env GS_DBG, GS_RAMB, hex)"""
    if _base[0]: return _base[0]
    dbg, rb = int(os.environ['GS_DBG'], 16), int(os.environ['GS_RAMB'], 16)
    p = memscan.Proc(y.pr.pid)
    hits = p.find(b'SATR')
    import struct
    def vbl(h):
        d = p.read(h + 8, 4); return struct.unpack('>I', d)[0] if d else None
    a0 = [vbl(h) for h in hits]; time.sleep(0.5); tick()
    for h, v0 in zip(hits, a0):   # the real sat_dbg: its vblank counter moves
        v1 = vbl(h)
        if v0 is not None and v1 is not None and v1 != v0 and v1 - v0 < 1000:
            _base[0] = (p, h + (rb - dbg)); log('ram base', hex(h), 'of', len(hits), 'hits'); return _base[0]
    return None
def log(*a):
    s = f'{time.time()-y.t0:7.1f}s f={T.vb} ' + ' '.join(str(x) for x in a); lf.write(s + '\n'); lf.flush(); print(s, flush=True)
AUTO = int(os.environ.get('AUTO', '300')); last = [0]; n = [0]
def tick():
    T.poll()
    if T.vb >= last[0] + AUTO and T.vb > 0:
        last[0] = T.vb; n[0] += 1; y.shot(f'{out}/auto_{n[0]:03d}_f{T.vb:06d}.png')
    y.win()
def wait_frames(target):
    while T.vb < target and y.pr.poll() is None: tick(); time.sleep(0.05)
try:
    for st in route:
        k, _, a = st.partition(':')
        if k == 'f': wait_frames(int(a))
        elif k == 'r': wait_frames(T.vb + int(a))
        elif k in ('t', 'h'):
            keys, _, rest = a.partition(':'); ks = [x for x in keys.split('+') if x]
            if k == 't':
                hold, _, gap = rest.partition(':'); hold = int(hold or 8); gap = int(gap or 30)
            else: hold, gap = int(rest), 0
            T.poll(); ygs.pad(*ks); wait_frames(T.vb + hold); ygs.pad(); wait_frames(T.vb + gap)
        elif k == 'q':
            s = float(a or 2); n0 = T.nsect; qend = T.vb + int(os.environ.get('QMAX', '4000'))
            while y.pr.poll() is None:
                tick(); time.sleep(0.05)
                if T.nsect > n0 and (T.vb - T.lastsect_vb) >= int(s * 60): break
                if T.vb > qend: log('q timeout'); break
        elif k == 'x':   # x:ADDR:VAL  poke game RAM bytes, ADDR hex offset in ff0000 space (e.g. 822a), VAL hex bytes; x:ADDR? just reads and logs
            ad, _, vl = a.partition(':'); r = ram()
            if r and vl: r[0].write(r[1] + int(ad, 16), bytes.fromhex(vl)); log('poke', ad, vl)
            elif r: log('peek', ad, r[0].read(r[1] + int(ad, 16), 2).hex())
            else: log('no ram base')
        elif k == 'z':   # z:  log the loader's test words at 0x06013fb8 (load count, rotating sum of the last file's bytes; SAT_LOAD_SUM builds)
            r = ram()
            if r:
                dbg = int(os.environ['GS_DBG'], 16); host = r[1] - (int(os.environ['GS_RAMB'], 16) - dbg) + (0x06013fb8 - dbg)
                d = r[0].read(host, 8)
                import struct; log('LOADSUM', 'n=%d sum=%08x' % struct.unpack('>II', d) if d else 'unreadable')
            else: log('no ram base')
        elif k == 'k':   # k: health 0 (a KO)
            r = ram()
            if r: r[0].write(r[1] + 0x83c0, b'\x00\x00'); log('KO poke')
            else: log('no ram base')
        elif k == 'v':   # v:  health held at 0x65 for 5 s emulated (written every poll)
            r = ram(); e = T.vb + 300
            while r and T.vb < e and y.pr.poll() is None: r[0].write(r[1] + 0x83c0, b'\x00e'); tick(); time.sleep(0.05)
        elif k == 'p':
            T.poll(); y.shot(f'{out}/{a}.png'); log('shot', a)
        elif k == 'm':
            T.poll(); open(f'{out}/marks.txt', 'a').write(f'{T.vb} {a}\n'); log('mark', a)
        log('step', st)
    log('done'); y.shot(out + '/last.png')
finally:
    y.kill(); time.sleep(1)
    for f in ('trace.log', 'ymir_run.log'):
        try: shutil.copy(f'{HERE}/{f}', f'{out}/{f}')
        except Exception as e: print(e)
