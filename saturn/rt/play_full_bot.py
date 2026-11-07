# Whole-game closed loop for play_yaba.py: the choices of tools/mame_route_bot.lua (nearest live enemy, line up, fire, wander when stalled), on the real pad. RAM is only read.
# Writes rounds_proof.txt in WORK: one line per stage, with vblank, wall time, KOs and the loader's counters.
import json, os, random, time
loaded = False
stage = sec = None; n = 0; ko = 0; presses = 0; inko = False; lastshot = 0; lastsave = 0; seen = False; ended = False
stall = (0, 0); stall_t = 0; wander_to = 0; wander = []; last_press = 0; last_load = 0; endv = None; t0 = time.time(); lastend = 0; late = False; prog = None; prog_v = 0; stuck = 0; lastw = None
_w = os.environ.get("BOT_WATCH", "").split(","); WATCH = int(_w[0], 16) if _w[0] else 0; WATCHST = int(_w[1], 16) if WATCH else 0
WANT = int(os.environ.get("BOT_CHAR", "0"))   # select grid as tools/mame_route_bot.lua: 0 Warrior, 1 right Schaefer, 2 down Linn, 3 right and down Hunter
BIT = (1, 2, 8, 4)
P2 = os.environ.get("BOT_P2") == "1"; P2K = []; wrapped = False; p2_last = 0; p2_ph = 0; pick_t = 0
POOLS = ((0x8680, 24, 0x80), (0x9280, 4, 0xc0), (0x9580, 20, 0xc0))
lastv = 0
LEG = ("ko", "presses", "late", "seen", "ended", "endv", "lastv")   # kept across process legs joined by a save state
def load_leg(s):
    global loaded
    loaded = True
    f = s.work / "leg.json"
    if os.environ.get("YABA_LOAD") and f.exists():
        globals().update(json.loads(f.read_text()))
def note(s, *a):
    _r = os.environ.get("AVP_SCSP_RAW")
    if _r and os.path.exists(_r):   # where this line falls in the sound capture
        a += ("raw", os.path.basename(_r), os.path.getsize(_r))
    s.log(*a)
    with open(s.work / "rounds_proof.txt", "a") as f:
        f.write(" ".join(str(x) for x in a) + "\n")
def rounds(s):
    return [int.from_bytes(s.m.read(s.syms["sat_rounds"] + i * 4, 4), "big") for i in range(4)]
def p2_keys(a, v, now):
    """The second player on the second pad: coin, start, then nearest enemy, as bot2 in tools/mame_route_bot.lua."""
    global p2_last, p2_ph
    u = lambda o: int.from_bytes(a[o:o + 2], "big")
    sg = lambda o: u(o) - 0x10000 if u(o) >= 0x8000 else u(o)
    B = 0x480
    if a[0x1b0]:
        return []
    if a[1] != 2 or a[B] == 0 or a[B + 4] == 4:
        if now - p2_last > 0.4:
            p2_last = now; p2_ph += 1
            return ["p2_x"] if a[0x18c] == 0 else (["p2_start"] if p2_ph % 2 else ["p2_c"])
        return []
    px, py, cam = u(B + 0x10), u(B + 0x14), u(0x278)
    best = None; bd = 1 << 30
    for base, cnt, size in POOLS:
        for i in range(cnt):
            o = base - 0x8000 + i * size
            if a[o] and sg(o + 0x40) >= 0:
                x, y = u(o + 0x10), u(o + 0x14)
                if cam - 32 < x < cam + 416:
                    d = abs(x - px) + 2 * abs(y - py)
                    if d < bd:
                        best, bd = (x, y), d
    k = ["p2_c"] if n % 4 == 1 else []
    if n % 30 == 7: k.append("p2_a")
    if not best:
        return k + ["p2_right"]
    dx, dy = best[0] - px, best[1] - py
    if dy < -6: k.append("p2_up")
    elif dy > 6: k.append("p2_down")
    if dx > 48: k.append("p2_right")
    elif dx < -48: k.append("p2_left")
    elif n % 12 == 3: k.append("p2_right" if dx >= 0 else "p2_left")
    return k
def step(v, s):
    global lastv, P2K, wrapped, pick_t, stage, sec, n, ko, presses, inko, lastshot, lastsave, seen, ended, stall, stall_t, wander_to, wander, last_press, last_load, endv, lastend, late, prog, prog_v, stuck, lastw
    if not loaded:
        load_leg(s)
    n += 1
    if v + 1000 < lastv:   # the machine restarted under the bot: not an ending, and the leg must not save over it
        s.shot(f"reset_{v}"); note(s, "RESET vblank", v, "after", lastv, "stage was", hex(stage or 0)); s.done = True; return
    lastv = v
    a = s.ram(0x8000, 0x2000) + s.ram(0xa000, 0x500)
    u16 = lambda o: int.from_bytes(a[o:o + 2], "big")
    s16 = lambda o: u16(o) - 0x10000 if u16(o) >= 0x8000 else u16(o)
    st, att, mode, cred, p0, top = u16(0x1e8), a[0x1b0], a[1], a[0x18c], a[0x380], a[0x384]
    if P2:
        if not wrapped:
            wrapped = True; _set = s.set; s.set = lambda names: _set(list(names) + P2K)
        P2K = p2_keys(a, v, time.time())
    if WANT and st == 0 and not att and mode == 2 and cred >= 1 and a[9] == 2:   # on the select screen: walk the cursor to the character (ff81cc follows it), then the normal presses confirm
        cur = a[0x1cc] & 15
        if cur & BIT[WANT] == 0:
            s.set([])
            if time.time() - pick_t > 0.7:
                pick_t = time.time()
                c = {1: 0, 2: 1, 8: 0, 4: 1}.get(cur & -cur, 0); r = {1: 0, 2: 0, 8: 1, 4: 1}.get(cur & -cur, 0)
                k = ("right" if WANT & 1 else "left") if c != (WANT & 1) else (("down" if WANT & 2 else "up") if r != (WANT >> 1) else None)
                note(s, "SELECT cur", cur, "want", BIT[WANT], "press", k, "vblank", v)
                if k: s.pulse(k, 0.15)
            return
    se = s.ram(0xd182, 1)[0]
    if WATCH:   # BOT_WATCH=ffa240,0a: log one object's motion fields on every change in that stage, and save slot 4 on entering it
        if st == WATCHST and stage != st:
            s.log("watch save", str(s.m.call("save_state", slot=4))[:40])
        if st == WATCHST:
            r = s.ram(WATCH - 0xff0000, 0x70)
            k = (r[2:8], r[0x30:0x40], r[0x5c])
            if k != lastw:
                lastw = k
                with open(s.work / "watch.txt", "a") as f:
                    f.write(f"{v} {r[:8].hex()} x{r[0x10:0x14].hex()} y{r[0x14:0x18].hex()} v{r[0x30:0x34].hex()} {r[0x34:0x38].hex()} a{r[0x38:0x3c].hex()} {r[0x3c:0x40].hex()} h{r[0x40:0x42].hex()} 5c{r[0x5c]:02x} 6c{r[0x6c]:02x}" + chr(10))
    if st != stage or se != sec:
        r = rounds(s)
        if st != stage:
            s.shot(f"stage{st:02x}_{v}")
        note(s, "STAGE", hex(st), "section", se, "attract", att, "mode", mode, "vblank", v, "wall", round(time.time() - t0), "ko", ko, "presses", presses, "rounds", r)
        stage, sec = st, se
    r = rounds(s) if n % 20 == 0 else None
    if r and r[1] != last_load:
        last_load = r[1]; s.shot(f"load{r[1]:03d}_st{st:02x}_{v}"); note(s, "LOAD", r, "stage", hex(st), "vblank", v, "wall", round(time.time() - t0))
    if v - lastshot >= 1800:
        lastshot = v; s.shot(f"g_{v:07d}")
        s.log("st", hex(st), "sec", se, "hp", u16(0x3c0), "cred", cred, "ko", ko, "rate", round(v / (time.time() - t0), 1))
    if v - lastsave >= 6000:
        lastsave = v; s.log("save", str(s.m.call("save_state", slot=3))[:50])
    if top == 4 and not inko:
        ko += 1
    inko = top == 4
    now = time.time()
    if st >= 0x26 and v - lastend >= 240:   # the ending and credits: dense stills, they only count if seen
        lastend = v; s.shot(f"end_{v:07d}")
    late = late or st >= 0x10
    if late and att and seen:
        if not ended:
            ended = True; endv = v; note(s, "BACK TO ATTRACT vblank", v, "stage", hex(st), "ko", ko, "wall", round(now - t0)); s.shot(f"attract_{v}")
        s.set([])
        if v - endv > 1200:
            s.stop()
        return
    if att or mode in (0, 4) or p0 == 0 or top == 4:
        s.set([])
        if now - last_press > 0.5:
            last_press = now; presses += 1
            s.pulse("x" if cred == 0 else ("start" if presses % 2 else "c"), 0.1)
        return
    seen = True
    px, py, cam = u16(0x390), u16(0x394), u16(0x278)
    # Stuck section: stage, section and camera all unchanged. Log what is alive, and leave the fight for a while on a rotating heading.
    mark = (st, se, cam)
    if mark != prog:
        prog, prog_v = mark, v
    elif v - prog_v >= 3000:
        prog_v = v; stuck += 1
        live = [(hex(b + i * z), hex(a[b - 0x8000 + i * z]), s16(b - 0x8000 + i * z + 0x40)) for b, c, z in POOLS for i in range(c) if a[b - 0x8000 + i * z]]
        s.shot(f"stuck{stuck:03d}_st{st:02x}_{v}")
        note(s, "STUCK", stuck, "stage", hex(st), "section", se, "vblank", v, "cam", hex(cam), "x", hex(px), "y", hex(py), "ko", ko, "live", live[:12])
        wander = [("right",), ("left",), ("right", "up"), ("right", "down"), ("left", "up"), ("left", "down")][stuck % 6]
        wander = list(wander); wander_to = now + 6
    fire = ["c"] if n % 4 == 0 else []
    if now < wander_to:
        s.set(wander + fire); return
    if (px, py) != stall:
        stall, stall_t = (px, py), now
    if now - stall_t > 4:
        wander = random.choice((["right"], ["left"], ["up"], ["down"], ["right", "up"], ["right", "down"], ["left", "up"], ["left", "down"], ["right", "b"]))
        wander_to = now + 1 + random.random() * 1.5; stall_t = now
        s.set(wander); return
    best = None; bd = 1 << 30
    for base, cnt, size in POOLS:
        for i in range(cnt):
            o = base - 0x8000 + i * size
            if a[o] and s16(o + 0x40) >= 0:
                x, y = u16(o + 0x10), u16(o + 0x14)
                if cam - 32 < x < cam + 416:
                    d = abs(x - px) + 2 * abs(y - py)
                    if d < bd:
                        best, bd = (x, y), d
    keys = list(fire)
    if n % 30 == 0: keys.append("a")
    if not best:
        s.set(keys + ["right"] + (["b"] if n % 40 == 0 else [])); return
    dx, dy = best[0] - px, best[1] - py
    if dy < -6: keys.append("up")
    elif dy > 6: keys.append("down")
    if dx > 48: keys.append("right")
    elif dx < -48: keys.append("left")
    elif n % 12 == 0: keys.append("right" if dx >= 0 else "left")
    s.set(keys)
def fatal(s, c, d):
    s.done = True   # never let end() save a faulted state over the leg's slot
    try:   # the 68000 registers and which ROM pages differ, for the fault's cause
        c = s.m.read(s.syms[os.environ.get("BOT_CPU", "sat_cpu")], 64)
        regs = [int.from_bytes(c[i:i + 4], "big") for i in range(0, 64, 4)]
        note(s, "REGS d", [hex(x) for x in regs[:8]], "a", [hex(x) for x in regs[8:]])
        for r in regs[8:]:
            if 0 < r < 0x200000:
                note(s, "at", hex(r), s.m.read(0x02400000 + (r & ~1), 32).hex())
        for r in regs[8:15]:   # the record chain a sprite script read walks: a+0x1c, then its +4
            if 0xff0000 <= r & 0xffffff < 0x1000000:
                x = int.from_bytes(s.ram((r & 0xffff) + 0x1c, 4), "big")
                note(s, "rec", hex(r), s.ram(r & 0xffff, 0xc0).hex(), "1c", hex(x), "1c.h", s.m.read(0x02400000 + (x & 0x1ffffc), 16).hex() if x < 0x200000 else s.ram(x & 0xffff, 16).hex())
        (s.work / "fatal_ram.bin").write_bytes(s.ram(0, 0x10000))   # ROM-derived evidence, under E:/AvP/learning
        s.log("fatal save", str(s.m.call("save_state", slot=5))[:50])
    except Exception as e:
        note(s, "no regs", e)
    s.shot("fatal"); note(s, "FATAL", hex(c), hex(d), "stage", hex(stage or 0), "rounds", rounds(s), "vblank", s.v)
def end(s):
    if not s.done:   # time limit: save for the next leg
        s.set([])
        s.log("leg save", str(s.m.call("save_state", slot=3))[:50])
        (s.work / "leg.json").write_text(json.dumps({k: globals()[k] for k in LEG}))
    else:
        (s.work / "DONE").write_text("stopped by bot")
    note(s, "END vblank", s.v, "stage", hex(stage or 0), "ko", ko, "presses", presses, "rounds", rounds(s), "wall", round(time.time() - t0))
