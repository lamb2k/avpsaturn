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
sys.path.insert(0, 'E:/AvP/learning/lane-wv-speed/ymir_wv')
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
    if os.environ.get('NOAUTO'): return
    if time.time() - last[0] > 10:
        last[0] = time.time(); n[0] += 1; y.shot(f'{out}/auto_{n[0]:04d}.png')
        if not getattr(y, '_lab', 0) and y.win(): y._lab = 1; y.label('WV-SPEED lane Ymir - ' + name)
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
        elif k == 'm':   # m:OFFSET:HEX  poke bytes into the game RAM at ff0000+OFFSET (my own Ymir process): the boss-down and clear flags of a boss, as home.c's ending hook does
            off, _, hx = a.partition(':'); r = ram()
            if r: r[0].write(r[1] + int(off, 16), bytes.fromhex(hx)); log('poke', off, hx)
            else: log('no ram base')
        elif k == 'bw':   # Wolverine bot (lane wv-speed): as b, plus his special (attack + jump held together) for 8 vblanks every 300, and a pause of walking during it
            r = ram(); vb0 = y.vb(); nv = int(a); last_x = 0; stuck = 0; dirn = 0; v_last = vb0
            while y.vb() - vb0 < nv and y.pr.poll() is None:
                vb = y.vb(); f = vb - vb0
                if r:
                    r[0].write(r[1] + 0x83c0, b'\x00e')
                    xb = r[0].read(r[1] + 0x8390, 2); x = (xb[0] << 8 | xb[1]) if xb else 0
                    if vb != v_last:
                        if x == last_x: stuck += vb - v_last
                        else: stuck = 0; last_x = x
                        v_last = vb
                    if stuck > 240: dirn = (dirn + 1) % 4; stuck = 0
                w = f % 900; keys = []
                keys.append('left' if dirn == 2 else 'right')
                if dirn == 1 or 300 < w < 340: keys.append('up')
                if dirn == 3 or 700 < w < 740: keys.append('down')
                if f % 300 < 8: keys += ['a', 'b']
                else:
                    if f % 24 < 5: keys.append('a')
                    if f % 700 < 5: keys.append('b')
                pad(*keys); auto(); time.sleep(0.03)
            pad(); log('bot done')
        elif k == 'b':   # bot: walk, shoot and attack with the player's health held, for N vblanks (as hw_run.py)
            r = ram(); vb0 = y.vb(); nv = int(a); last_x = 0; stuck = 0; dirn = 0; v_last = vb0
            while y.vb() - vb0 < nv and y.pr.poll() is None:
                vb = y.vb(); f = vb - vb0
                if r:
                    r[0].write(r[1] + 0x83c0, b'\x00e')
                    xb = r[0].read(r[1] + 0x8390, 2); x = (xb[0] << 8 | xb[1]) if xb else 0
                    if vb != v_last:
                        if x == last_x: stuck += vb - v_last
                        else: stuck = 0; last_x = x
                        v_last = vb
                    if stuck > 240: dirn = (dirn + 1) % 4; stuck = 0
                w = f % 900; keys = []
                keys.append('left' if dirn == 2 else 'right')
                if dirn == 1 or 300 < w < 340: keys.append('up')
                if dirn == 3 or 700 < w < 740: keys.append('down')
                if f % 16 < 6: keys.append('c')
                if f % 24 < 5: keys.append('a')
                if f % 700 < 5: keys.append('b')
                pad(*keys); auto(); time.sleep(0.03)
            pad(); log('bot done')
        elif k == 'q':   # log the slave's sat_gfx_stats counters (frames, missing tiles, refused ...) read from my own Ymir's memory
            import struct
            OFF2 = int(os.environ.get('GS_OFF2', '0'), 0); OFF = int(os.environ.get('GS_OFF', '0'), 0)
            pp = memscan.Proc(y.pr.pid); got = None
            for h in pp.find(b'SATR'):
                c = h - 0xDEA64 - OFF
                d = pp.read(c + (0x060FEF84 + OFF2 - 0x06000000), 0x60)
                if d and len(d) >= 0x2c:
                    v = struct.unpack('>I', d[0:4])[0]; l = y.last()
                    if l and abs(v - int(l['pics'])) < 400: got = d; break
            if got:
                fr, = struct.unpack('>I', got[0:4]); mi, rc, rs = struct.unpack('>III', got[0x20:0x2c])
                log('stats', a, 'frames', fr, 'missing', mi, 'refused_commands', rc, 'refused_next', rs)
            else: log('stats: not found')
        elif k == 'x':
            open(ygs.HERE + '/hw_cmd.txt', 'w').write(a.replace('_', ' ') + (' ' + name if a == 'dump' else '')); log('cmd', a)
        elif k == 'n':   # n:select[:secs] wait until the screen looks like the reference (refs/NAME.png)
            from PIL import Image, ImageChops, ImageStat
            nm, _, mx = a.partition(':'); ref = Image.open('E:/AvP/learning/lane-perf-pic/refs/' + nm + '.png').convert('RGB').crop((0, 80, 985, 640)).resize((123, 70))
            t1 = time.time() + float(mx or 90); ok = False
            while time.time() < t1 and y.pr.poll() is None:
                tmp = out + '/_n.png'; y.shot(tmp)
                try:
                    im = Image.open(tmp).convert('RGB').crop((0, 80, 985, 640)).resize((123, 70))
                    if sum(ImageStat.Stat(ImageChops.difference(im, ref)).mean) / 3 < 20: ok = True; break
                except Exception: pass
                auto(); time.sleep(1.0)
            log('state', nm, ok)
        elif k == 'p':
            y.shot(f'{out}/{a}.png'); log('shot', a, y.last())
        log('step', st)
    log('done'); y.shot(out + '/last.png')
finally:
    y.kill(); time.sleep(1)
    try: shutil.copy(ygs.HERE + '/gs.log', out + '/gs.log')
    except Exception as e: print(e)
