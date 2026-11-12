"""usage: gs_ymir.py NAME GAME_VBLANKS [stage_downs stage_rights]  -> E:/AvP/learning/lane-perf-hw/ymir_hw/runs/NAME (gs.log copy, shots)
Boots the fix7n2 disc in my own Ymir (probe build), title -> STAGE SELECT MODE -> stage list, then plays with a scripted bot (same moves as the MAME bot)
with the player's health held, for GAME_VBLANKS vblanks of the stage. Pad: ymir_pad.txt only. RAM health hold through WriteProcessMemory on my own emulator process."""
import sys, time, os, shutil, re
sys.path.insert(0, 'E:/AvP/learning/lane-perf-hw/ymir_hw')
import ygs, memscan
HERE_ = ygs.HERE
from ygs import tap, pad
name, gv = sys.argv[1], int(sys.argv[2])
downs = int(sys.argv[3]) if len(sys.argv) > 3 else 0; rights = int(sys.argv[4]) if len(sys.argv) > 4 else 0
cue = os.environ.get('GS_CUE', 'E:/AvP/package-integration/fenrir/avp_3h_A_fix7n4/avp_3h_A_fix7n4.cue')
reset_at = int(os.environ.get('HW_RESET_AT', '300')); dump_at = int(os.environ.get('HW_DUMP_AT', '0'))
cmdf = HERE_ + '/hw_cmd.txt'
out = f'{ygs.HERE}/runs/{name}'; os.makedirs(out, exist_ok=True)
y = ygs.Y(cue)
lf = open(out + '/run.log', 'w')
def log(*a):
    s = f'{time.time()-y.t0:7.1f} vb={y.vb()} ' + ' '.join(str(x) for x in a); print(s, flush=True); lf.write(s + '\n'); lf.flush()
try:
    while y.vb() < 3300: time.sleep(0.5)
    log('title'); y.label('PERF-HW lane Ymir - ' + name); tap('start', gap=3.0)
    for _ in range(3): tap('down')
    tap('a', gap=4.0); tap('start', gap=5.0)
    for _ in range(downs): tap('down', gap=0.7)
    for _ in range(rights): tap('right', gap=0.7)
    y.shot(out + '/list.png'); tap('start', gap=3.0)
    t = time.time()
    while y.stage() == 0 and time.time() - t < 90: time.sleep(0.5)
    log('stage word', hex(y.stage()))
    # find the RAM base: candidate whose game ticks/vblank bytes match the log
    p = memscan.Proc(y.pr.pid); base = None
    OFF = int(os.environ.get('GS_OFF', '0'), 0)
    OFFR = int(os.environ.get('GS_OFFR', str(OFF)), 0)
    cands = [h - 0xDEA64 - OFF for h in p.find(b'SATR')]
    for _ in range(40):
        for c in cands:
            d = p.read(c + 0xDEC14 + OFFR + 0x8018, 2); l = y.last()
            if d and l and abs(((d[0] - int(l['v8'])) + 128) % 256 - 128) <= 3 and abs(((d[1] - int(l['t8'])) + 128) % 256 - 128) <= 6: base = c
        if base: break
        time.sleep(0.2)
    log('ram base', hex(base) if base else None, [hex(c) for c in cands])
    RAM = base + 0xDEC14 + OFFR
    def rb(o, n=2): return p.read(RAM + o, n)
    vb0 = y.vb(); last_x = 0; stuck = 0; dirn = 0; lastshot = 0; v_last = vb0
    while y.vb() - vb0 < gv and y.pr.poll() is None:
        vb = y.vb(); f = vb - vb0
        if base:
            p.write(RAM + 0x83c0, b'\x00\x65')
            xb = rb(0x8390); x = (xb[0] << 8 | xb[1]) if xb else 0
            if vb != v_last:
                if x == last_x: stuck += vb - v_last
                else: stuck = 0; last_x = x
                v_last = vb
            if stuck > 240: dirn = (dirn + 1) % 4; stuck = 0
        if reset_at and f >= reset_at and not getattr(y, '_rs', 0):
            y._rs = 1; open(cmdf, 'w').write('reset x'); log('reset cmd')
        if dump_at and f >= dump_at and not getattr(y, '_dm', 0):
            y._dm = 1; open(cmdf, 'w').write('dump ' + name); log('dump cmd')
        w = f % 900
        keys = []
        if dirn == 2: keys.append('left')
        else: keys.append('right')
        if dirn == 1 or 300 < w < 340: keys.append('up')
        if dirn == 3 or 700 < w < 740: keys.append('down')
        if f % 16 < 6: keys.append('c')
        if f % 24 < 5: keys.append('a')
        if f % 700 < 5: keys.append('b')
        pad(*keys)
        if time.time() - lastshot > 12:
            lastshot = time.time(); y.shot(f'{out}/p{int(f):06d}.png'); log('f', f, 'x', x if base else None, y.last())
        time.sleep(0.03)
    log('done'); y.shot(out + '/last.png')
finally:
    y.kill(); time.sleep(1)
    try: shutil.copy(ygs.HERE + '/gs.log', out + '/gs.log')
    except Exception as e: print(e)
