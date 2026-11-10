"""Lane wv-native3 11-10: attract and opening scenes without any input: a screenshot every ATT_STEP vblanks from boot to ATT_END (default 7200), plus the table base word (sat_wv_tb) and the player blocks' in-use bytes at each shot,
to check that Schaefer's own tables stand while no Wolverine player is alive (front end, attract, the opening street scene with Dutch Schaefer). Run under saturn/rt/play_yaba.py (own Yaba copy, minimised, SH-2 cache off); sends no input.
Env: PROOF_OUT (json log), ATT_STEP, ATT_END, ATT_NAME (prefix of the picture names), ATT_START (vblank of the first Start press; unset: no input at all)"""
import json, os
OUT = os.environ["PROOF_OUT"]; STEP = int(os.environ.get("ATT_STEP", "150")); END = int(os.environ.get("ATT_END", "7200")); NAME = os.environ.get("ATT_NAME", "att")
last = [-STEP]; log = []; titled = [False]; sent = set()


def step(v, s):
    if not titled[0]:
        titled[0] = True
        import ctypes
        try: ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), os.environ.get("PROOF_TITLE", "AvP NATIVE: attract [port 9718]"))
        except Exception: pass
    if os.environ.get("ATT_START"):   # Start twice (title, then ARCADE MODE) by window message to this window only, then the opening scenes play unattended until the character select
        t0 = int(os.environ["ATT_START"])
        for k, at in enumerate((t0, t0 + 400)):
            if v >= at and k not in sent:
                sent.add(k); s.pulse("start", 0.15)
    if v - last[0] >= STEP:
        last[0] = v
        tb = s.word("sat_wv_tb") if "sat_wv_tb" in s.syms else None
        a = s.ram(0x8380, 0x200)
        name = "%s_v%05d" % (NAME, v)
        s.shot(name)
        log.append(dict(v=v, shot=name, sat_wv_tb0=hex(tb) if tb is not None else None, p1=(a[0], a[0xd2]), p2=(a[0x100], a[0x100 + 0xd2]), stage=s.ram16(0x81e8)))
    if v >= END:
        os.makedirs(OUT, exist_ok=True); json.dump(log, open(OUT + "/attract.json", "w"), indent=1); s.stop()
