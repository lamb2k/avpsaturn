# Lane avp-megaman: guests on stage 02, 1P or 2P. env P1 / P2: select grid moves ("" Warrior, "r" Schaefer = Wolverine, "d" Linn,
# "rd" Hunter = Mega Man); P2 unset = 1 player. Short scripted play (walk, attack, gun, jump) and stills tagged with both states.
# Run through saturn/rt/play_yaba.py WORK this_file SECONDS (YABA_P2=1 YABA_PAD=mcp for two pads), the lane's own Yaba port.
import os, time
P1, P2 = os.environ.get("P1", "rd"), os.environ.get("P2")
TAG = os.environ.get("TAG", "g")
lastp = 0; sel_at = None; play_at = None; shots = 0; nextshot = 0; done = set()
PLAN = [(0, 1.5, ["right"]), (1.5, 2.5, ["up"]), (2.5, 3.5, ["down"])] + [(4 + 0.6 * i, 4.15 + 0.6 * i, [("a", "c", "b")[i % 3]]) for i in range(9)] + \
       [(10, 11.5, ["left"]), (11.5, 30, [])]


def step(v, s):
    global lastp, sel_at, play_at, shots, nextshot
    if v < 300: return
    now = time.time(); a = s.ram(0x8000, 0x500); sc = s.word("sat_home_screen")
    if sc == 1:
        if now - lastp > .7: lastp = now; s.pulse("start", .1)
        return
    playing = a[1] == 2 and a[0x380] and a[0x1e9] and a[0x1b0] == 0
    if not playing:
        if a[0x1b0] == 0 and a[9] == 2 and not a[0x1e9] and sc == 0:
            if sel_at is None: sel_at = v; s.log("select")
            t = v - sel_at
            acts = [("right", 190, P1), ("down", 225, P1)]
            if P2 is not None:
                acts = [("p2start", 60, "x")] + acts + [("p2right", 190, P2), ("p2down", 225, P2)]
            for k, at, want in acts:
                if t >= at and k not in done:
                    done.add(k)
                    if k == "p2start" or k.replace("p2", "")[0] in want: s.pulse(k, .1)
            if t >= 245 and "shot" not in done: done.add("shot"); s.shot(f"{TAG}_sel")
            if t > 270 and now - lastp > .6:
                lastp = now; s.pulse("a", .08)
                if P2 is not None: s.pulse("p2a", .08)
        elif a[0x1b0] == 0 and now - lastp > .7: lastp = now; s.pulse("start", .1)
        return
    if play_at is None:
        if a[0x384] != 2: return
        play_at = now; s.log("play kinds", a[0x380 + 0xd2], a[0x480 + 0xd2], "p2 on", a[0x480], "file", s.word("sat_rounds", 0))
    t = now - play_at
    keys = []
    for t0, t1, k in PLAN:
        if t0 <= t < t1: keys = k
    s.set(keys + (["p2" + k for k in keys] if P2 is not None else []))
    if now > nextshot:
        nextshot = now + 0.4; shots += 1
        s.shot(f"{TAG}{shots:02d}_{a[0x384:0x387].hex()}_{a[0x484:0x487].hex()}")
    if t > 14: s.stop()
