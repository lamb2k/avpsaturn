# Closed loop for the whole game: reads game RAM over MCP, chooses pad keys, sends them to Yaba's own window (play_yaba.py). Real pad path; RAM is only read.
# Markers: ff81e8 stage word, ff81b0 attract, ff8001 mode (2 in play), ffd182 section, ff8380/ff8384 player state. Writes rounds_proof.txt in WORK, one line per stage.
import os, time
t0 = time.time(); started = False
stage = None; n = 0; ko = 0; cont = 0; inko = False; lastshot = 0; lastpress = 0; lastx = 0; stuck = 0; dir_ = 0; lastsave = 0; ended = False; seen_play = False
BOTLOG = None
def note(s, *a):
    s.log(*a)
    with open(s.work / "rounds_proof.txt", "a") as f:
        f.write(" ".join(str(x) for x in a) + "\n")
def rounds(s):
    return [int.from_bytes(s.m.read(s.syms["sat_rounds"] + i * 4, 4), "big") for i in range(4)]
def step(v, s):
    global stage, n, ko, cont, inko, lastshot, lastpress, lastx, stuck, dir_, lastsave, ended, seen_play
    n += 1
    a = s.ram(0x8000, 0x400); c = s.ram(0xd180, 6)
    mode, att, cred, p0, top, sec = a[1], a[0x1b0], a[0x18c], a[0x380], a[0x384], c[2]
    st = int.from_bytes(a[0x1e8:0x1ea], "big")
    x = int.from_bytes(a[0x390:0x392], "big")
    hp = int.from_bytes(a[0x3c0:0x3c2], "big")
    if st != stage:
        stage = st
        note(s, "STAGE", hex(st), "section", sec, "attract", att, "mode", mode, "vblank", v, "wall", round(time.time() - t0), "ko", ko, "continues", cont, "rounds", rounds(s))
        s.shot(f"stage{st:02x}_{v}")
    if v - lastshot >= 1200:
        lastshot = v; s.shot(f"g_{v:06d}")
        s.log("st", hex(st), "sec", sec, "hp", hp, "x", x, "cred", cred, "ko", ko, "cont", cont, "rate", round(v / (time.time() - t0), 1), "rounds", rounds(s))
        if v - lastsave >= 6000:
            lastsave = v; s.log("save", s.m.call("save_state", slot=2)[:60])
    if top == 4 and not inko:
        inko = True; ko += 1
    if top != 4:
        inko = False
    now = time.time()
    if att or mode != 2 or p0 == 0 or top == 4:
        s.set([])
        if seen_play and att and not ended:
            ended = True; note(s, "BACK TO ATTRACT vblank", v, "stage", hex(st), "ko", ko, "continues", cont); s.shot(f"attract_{v}")
        if now - lastpress > 0.7:
            lastpress = now
            if cred == 0: s.pulse("x", 0.08)
            elif n % 2: s.pulse("start", 0.08); cont += 1
            else: s.pulse("c", 0.08)
        return
    seen_play = True
    if x == lastx:
        stuck += 1
    else:
        stuck = 0; lastx = x
    if stuck > 60:
        dir_ = (dir_ + 1) % 4; stuck = 0
    keys = ["left"] if dir_ == 2 else ["right"]
    if dir_ == 1: keys.append("up")
    if dir_ == 3: keys.append("down")
    if n % 90 < 8: keys.append("up")
    if 45 <= n % 90 < 53: keys.append("down")
    s.set(keys)
    for k in range(6):
        s.pulse("c" if k < 4 else ("a" if k < 5 else "b"), 0.04); time.sleep(0.04)
def fatal(s, c, d):
    s.shot("fatal"); note(s, "FATAL", hex(c), hex(d), "stage", hex(stage or 0), "rounds", rounds(s))
def end(s):
    note(s, "END vblank", s.v, "stage", hex(stage or 0), "ko", ko, "continues", cont, "rounds", rounds(s), "wall", round(time.time() - t0))
