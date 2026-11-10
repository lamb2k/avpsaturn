"""AvP PERF timeline: usage run.py CUE ELF TAG STAGE(hex) CHAR CACHE(true|false) [A_STEPS FREE_SECONDS]
Per single stepped frame (framebuffer_burst frames=1): vblanks, slave draws finished (gfx_done), plots started / shown (VDP1 frame-buffer swaps) / held,
snapshot skips, game overruns, object-bank flips, gfx_ticks, game_ticks, snap_ticks, the slave's stage timers, composite pixel hash.
Segments: A idle after the stage load; W hold right (walk, the screen scrolls); A2 settle; F fixed attack pattern; C free running (not stepped) with random input,
counters read at pause points only. No game-state pokes in the measured windows (the warp word and stage byte are set up before)."""
import sys, time, random, os, json, shutil, glob, hashlib
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
cue, elf, tag, stage, ch, cache = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4], 16), sys.argv[5], sys.argv[6]
A_STEPS, FREE = (int(sys.argv[7]), int(sys.argv[8])) if len(sys.argv) > 8 else (150, 25)
KEEP_PNG = os.environ.get('PF_PNG') == '1'; FB = os.environ.get('PF_FB') == '1'
out = f"{pf.D}/runs/{tag}"; shutil.rmtree(out, ignore_errors=True); os.makedirs(out, exist_ok=True); tmp = f"{out}/_f"; os.makedirs(tmp, exist_ok=True)
y = pf.boot(cue, tag, cache); Y = pf.Y(y.pid, elf); Y.ready()
POS = {1: (0, 0), 2: (1, 0), 8: (0, 1), 4: (1, 1)}; BIT = {"w": 1, "s": 2, "l": 8, "h": 4}
def enter_stage(stage, ch, log=print):
    Y.m.call("memory_write", address=hex(Y.s['sat_home_warp']), size="long", value=hex(stage))
    want = BIT[ch]; t0 = time.time()
    for k in ("start", "none", "start", "none"):
        if k != "none": Y.pulse(k)
        time.sleep(1.2)
    while time.time() - t0 < 300:
        st = Y.arc(0xff81e8); mode = Y.arc(0xff8001, 1); g09 = Y.arc(0xff8009, 1); cc = Y.arc(0xff81cc, 1) & 15
        if st == stage and mode == 2 and Y.arc(0xff8380, 1): break
        if st == 2 and mode == 2 and Y.arc(0xff8380, 1): Y.w(0xff81e9, "byte", stage & 255)
        elif st == 0 and g09 == 2 and cc:
            if cc == want: Y.pulse("a", gap=1.0)
            elif cc in POS:
                (x, yy), (wx, wy) = POS[cc], POS[want]
                Y.pulse("right" if wx > x else "left" if wx < x else ("down" if wy > yy else "up"), gap=0.8)
        else: Y.pulse("a", gap=0.9)
        time.sleep(0.1)
    log("entered stage", hex(Y.arc(0xff81e8)), "chars", Y.arc(0xff81cc, 1) & 15, "want", want, flush=True)
enter_stage(stage, ch)
v = Y.vb(); t2 = time.time()
while time.time() - t2 < 240:
    time.sleep(1)
    if Y.vb() - v > 300: break
Y.m.call("pause"); time.sleep(1.0)
u = lambda b, o: int.from_bytes(b[o:o + 4], "big")
S = Y.s
PS = "sat_gfx_pf" in S
def counters():
    d = Y.m.read(S["sat_dbg"], 104)
    dn = Y.m.read(S["gfx_done"], 8)          # gfx_done, gfx_handed
    pl = Y.m.read(S["plot_held"], 12)        # plot_held, plot_shown, plot_started
    pw = Y.m.read(S["sat_gfx_plot_waits"], 4)
    gs = Y.m.read(S["sat_gfx_stats"], 24)
    sg = Y.m.read(S["sat_gfx_stage"], 64 if PS else 24)
    pf_ = Y.m.read(S["sat_gfx_pf"], 20) if PS else b""
    return dict(stg=[u(sg, i * 4) for i in range(13 if PS else 6)], pfc=[u(pf_, i * 4) for i in range(5)] if PS else [],
                vb=u(d, 8), gfx=u(d, 60), game=u(d, 68), snap=u(d, 92), over=u(d, 84), flips=u(d, 88), skips=u(d, 100), done=u(dn, 0), handed=u(dn, 4),
                held=u(pl, 0), shown=u(pl, 4), started=u(pl, 8), waits=u(pw, 0), objects=int.from_bytes(gs[4:6], "big"), pieces=int.from_bytes(gs[6:8], "big"),
                upl=int.from_bytes(gs[10:12], "big"), lupl=int.from_bytes(gs[18:20], "big"), lwr=int.from_bytes(gs[20:22], "big"), sfr=u(gs, 0))
log = []; free = []
def step(seg, keys=None):
    if keys is not None: Y.set(sorted(keys)); time.sleep(0.12)
    Y.m.call("framebuffer_burst", directory=tmp, frames=1, prefix="f")
    h = ""; names = []
    for f in sorted(glob.glob(tmp + "/*")):
        names.append(os.path.basename(f))
        if f.endswith(".png"):
            data = open(f, "rb").read()
            try:
                from PIL import Image
                im = Image.open(f); h = hashlib.sha1(im.convert("RGB").tobytes()).hexdigest()[:12]
            except Exception: h = hashlib.sha1(data).hexdigest()[:12]
            if KEEP_PNG: shutil.copy(f, f"{out}/png_{len(log):04d}_{seg}.png")
        os.remove(f)
    if not os.path.exists(f"{out}/first_names.txt"): open(f"{out}/first_names.txt", "w").write(repr(names))
    r = counters(); r["seg"] = seg; r["h"] = h
    if FB:
        t0 = time.time(); fb = Y.m.read(0x25C80000, 0x10000) + Y.m.read(0x25C90000, 0xc000)   # first 112 rows of the VDP1 frame buffer the CPU sees (reads are capped at 64 KB)
        r["fb"] = hashlib.sha1(fb).hexdigest()[:12]; r["fbnz"] = sum(1 for x in fb[::16] if x); r["fbt"] = round(time.time() - t0, 2)
    return r
def dump(): json.dump(dict(log=log, free=free, elf=elf, cue=cue, cache=cache, stage=hex(stage), char=ch), open(f"{out}/log.json", "w"))
for i in range(A_STEPS): log.append(step("A"))
print("A done vb", Y.vb(), flush=True); dump()
# M: multi-frame bursts (the emulator's own presented frames; the first 3 frames after a pause carry no sprites in Yaba, so they are dropped): frame hashes from the
# burst manifest against the kernel's swap counter over the same window
bursts = []
def burst(seg, names, n=64, reps=3):
    for rep in range(reps):
        Y.set(names); time.sleep(0.12)
        for f in glob.glob(tmp + "/*"): os.remove(f)
        c0 = counters()
        Y.m.call("framebuffer_burst", directory=tmp, frames=n, prefix="b")
        c1 = counters()
        shas = []
        mf = os.path.join(tmp, "manifest.tsv")
        if os.path.exists(mf):
            for l in open(mf).read().splitlines()[1:]:
                p = l.split("\t")
                if len(p) >= 3: shas.append(p[2])
        for f in glob.glob(tmp + "/*"):
            if KEEP_PNG and f.endswith(".png") and rep == 0: shutil.copy(f, f"{out}/b_{seg}_{os.path.basename(f)}")
            os.remove(f)
        bursts.append(dict(seg=seg, c0=c0, c1=c1, shas=shas))
burst("MA", [], 64, 3); burst("MW", ["right"], 64, 3); Y.set([]); time.sleep(0.2)
json.dump(bursts, open(f"{out}/bursts.json", "w"))
print("M done", len(bursts), flush=True)
def hold(seg, names, n):
    Y.set(names); time.sleep(0.12)
    for _ in range(n): log.append(step(seg))
hold("W", ["right"], 150); print("W done vb", Y.vb(), flush=True); dump()          # walk right: the screen scrolls
hold("A2", [], 40)                                                                  # settle
for c in range(15):                                                                 # F: a fixed attack pattern (b for 2 steps, rest 8) on the spot
    Y.set(["b"]); time.sleep(0.12); log.append(step("F")); log.append(step("F"))
    Y.set([]); time.sleep(0.12)
    for _ in range(8): log.append(step("F"))
print("F done vb", Y.vb(), "hp", Y.arc(0xff83c0), flush=True); dump()
def keys(rnd):
    r = rnd.random(); fz = {"right"} if rnd.random() < .5 else ({"left"} if rnd.random() < .4 else set())
    if rnd.random() < .25: fz |= {"up"}
    if r < .22: fz |= {"c"}
    elif r < .4: fz |= {"c", "b"}
    elif r < .7: fz |= {"b"}
    elif r < .8: fz |= {"a"}
    return fz
# C: free running with scripted input; counters at the pause points only
Y.m.call("resume"); time.sleep(1.0); Y.m.call("pause"); time.sleep(0.5)
c0 = counters(); c0["wall"] = time.time(); free.append(c0)
Y.m.call("resume"); r3 = random.Random(31); t0 = time.time()
while time.time() - t0 < FREE:
    Y.set(sorted(keys(r3))); time.sleep(0.25)
Y.set([]); Y.m.call("pause"); time.sleep(0.5)
c1 = counters(); c1["wall"] = time.time(); free.append(c1)
dump(); print("C done", c0["vb"], c1["vb"], flush=True)
y.terminate()
