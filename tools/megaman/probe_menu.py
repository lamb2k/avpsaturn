# Lane avp-megaman: look at the STAGE SELECT flow (stills only).
import time
t0 = None; done = set()
ACT = [(1, "down"), (2, "down"), (3, "down"), (4, "shot"), (5, "start"), (7, "shot"), (9, "shot"), (11, "shot")]
def step(v, s):
    global t0
    if v < 300: return
    now = time.time()
    if t0 is None: t0 = now
    t = now - t0
    for i, (at, k) in enumerate(ACT):
        if t >= at and i not in done:
            done.add(i)
            if k == "shot": s.shot(f"menu_{at:02d}")
            else: s.pulse(k, .1)
    if t > 12: s.stop()
