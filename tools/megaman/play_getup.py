# Lane avp-megaman (getup and shot check): home Start, pick the Predator Hunter (BONUS CHARACTERS = MEGA MAN in the build), stage 02: walk, depth, attack, gun, stills.
# Run through saturn/rt/play_yaba.py WORK this_file SECONDS with the lane's own Yaba (YABA_EXE, YABA_INI, YABA_PORT).
import time
n = 0; lastp = 0; sel_at = None; play_at = None; shots = 0; nextshot = 0
PLAN = [(0, 1.0, ["right"])] + [(1.5 + 0.6 * i, 1.65 + 0.6 * i, ["c"]) for i in range(10)] + [(8, 60, [])]


def step(v, s):
    global n, lastp, sel_at, play_at, shots, nextshot
    if v < 300: return
    n += 1; now = time.time(); a = s.ram(0x8000, 0x500); sc = s.word("sat_home_screen")
    if n % 40 == 0:
        s.log("v", v, "scr", sc, "mode", a[1], "att", a[0x1b0], "p0", a[0x380], "stage", a[0x1e9], "kind", a[0x380 + 0xd2], "st", a[0x384:0x387].hex(),
              "loads", s.word("sat_rounds", 4), "file", s.word("sat_rounds", 0))
    if sc == 1:
        if now - lastp > .7: lastp = now; s.pulse("start", .1)
        return
    playing = a[1] == 2 and a[0x380] and a[0x1e9] and a[0x1b0] == 0
    if not playing:
        if a[0x1b0] == 0 and a[9] == 2 and not a[0x1e9] and sc == 0:   # the game's select screen (ff8009 = 2, as tools/alien_measure walks it)
            if sel_at is None: sel_at = v; s.log("select"); s.shot("sel0"); step.done = set()
            t = v - sel_at   # vblanks, as tools/alien_measure walks the select (right at 190, down at 225)
            for k, at in (("right", 190), ("down", 225)):
                if t >= at and k not in step.done: step.done.add(k); s.pulse(k, .1)
            if t >= 245 and "shot" not in step.done: step.done.add("shot"); s.shot("sel1")
            if t > 270 and now - lastp > .6: lastp = now; s.pulse("a", .08)
        elif a[0x1b0] == 0 and now - lastp > .7: lastp = now; s.pulse("start", .1)
        if n % 30 == 0: s.shot(f"pre{n:04d}")
        return
    if play_at is None:
        if a[0x384] != 2: return   # the round proper: the player block leaves its entry state (08xxxx)
        play_at = now - 4; s.log("play kind", a[0x380 + 0xd2], "file", s.word("sat_rounds", 0))
    t = now - play_at
    keys = []
    for t0, t1, k in PLAN:
        if t0 <= t - 4 < t1: keys = k
    s.set(keys)
    st = a[0x384:0x387].hex()
    if now > nextshot and t > 3 and (st[:4] in ("0402", "0208", "0404") or st in ("02000c", "02001a") or 1.5 < t - 4 < 8 or n % 40 == 0):
        nextshot = now + 0.12; shots += 1
        s.shot(f"mm{shots:02d}_{a[0x384:0x387].hex()}")
    if t > 60: s.stop()
