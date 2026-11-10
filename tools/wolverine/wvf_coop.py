"""Lane wv-features 11-10 (heal in co-op): native_coop.py with the health assist replaced. Both players start at health 40 (poked once), enemies of the pools tag 0c/08 are taken out of play every poll (harness assist, both alike), nobody is topped up; the trace (hp.jsonl) has both players health, state and the heal timer whenever either health changes. The check: only the Wolverine player's health rises. Original header:
Lane wv-native3 11-09: native Wolverine in co-op under Yaba (two pads: YABA_P2=1 YABA_PAD=mcp, a Yaba exe with the pad_set tool; own copy and port). Adapted from tools/megaman/play_guest.py.
env: P1 / P2 = select grid moves ("" Warrior, "r" Schaefer slot = Wolverine, "d" Linn, "rd" Hunter); P2 unset = one player. WV = 1 or 2: which player is Wolverine (drives the Berserker motion; default 1).
PROOF_OUT = directory for trace.jsonl, summary.json and stills; PROOF_SECS = play seconds (default 40); PROOF_TITLE.
Script (seconds after both are in play): walk right, up, down; attack taps by both; the partner fires its gun (button c) and jumps (b); Wolverine plays the Berserker motion (down, down+forward, forward, attack)
twice, at about 12 s and 22 s. The trace has, per poll, both players' state words, frame records (class: native window or not), health, the Berserker byte, and the shot actors (tag 4) with their owner,
so "his Berserker allocates no shot, the partner's gun keeps working" is a count: shots_owned_by_wolverine must be 0, shots_owned_by_partner > 0 for a Warrior or Hunter partner."""
import collections, ctypes, json, os, time

P1, P2 = os.environ.get("P1", "r"), os.environ.get("P2")
WV = int(os.environ.get("WV", "1"))
OUT = os.environ["PROOF_OUT"]
SECS = float(os.environ.get("PROOF_SECS", "40"))
TITLE = os.environ.get("PROOF_TITLE", "AvP NATIVE: coop [port 9718]")
lastp = 0; sel_at = None; play_at = None; done = set(); titled = False
NAT_LO, NAT_HI = 0x300000, 0x310000
rows = []; states = [collections.Counter(), collections.Counter()]; pairs = collections.Counter(); anomalies = []
shot_owner = collections.Counter(); last_st = [None, None]
bz_t = []; hp_rows = []; hp_last = [None, None]


def pre(i):
    return "" if i == 0 else "p2"


def step(v, s):
    global lastp, sel_at, play_at, titled
    if not titled:
        titled = True
        try: ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), TITLE)
        except Exception as e: s.log("retitle failed", e)
    if v < 300: return
    now = time.time(); a = s.ram(0x8000, 0x600); sc = s.word("sat_home_screen")
    if sc == 1:
        if now - lastp > .7: lastp = now; s.pulse("start", .1)
        return
    playing = a[1] == 2 and a[0x380] and a[0x1e9] and a[0x1b0] == 0
    if not playing:
        if a[0x1b0] == 0 and a[9] == 2 and not a[0x1e9] and sc == 0:
            global sel_at
            if sel_at is None: sel_at = v; s.log("select")
            t = v - sel_at
            acts = [("p2start", 60)] if P2 is not None else []
            for n, k in enumerate(filter(None, os.environ.get("SEQ", "").split(";"))):   # select moves in order, 35 vblanks apart from vblank 190 on (P2 has joined by then): "p2down;right;p2left;p2up"
                acts.append((k, 190 + 35 * n))
            for n, (k, at) in enumerate(acts):
                if t >= at and n not in done:
                    done.add(n); s.pulse(k, .1)
            if t > 190 + 35 * len(acts) + 50 and now - lastp > .6:
                lastp = now; s.pulse("a", .08)
                if P2 is not None: s.pulse("p2a", .08)
        elif a[0x1b0] == 0 and now - lastp > .7: lastp = now; s.pulse("start", .1)
        return
    if play_at is None:
        if a[0x384] != 2: return
        play_at = now; s.log("play kinds", a[0x380 + 0xd2], a[0x480 + 0xd2], "p2 on", a[0x480], "stage", a[0x1e8], a[0x1e9])
    t = now - play_at
    wv = WV - 1
    wp = pre(wv)
    keys = []
    for t0, t1, k in ((0, 1.5, ["right"]), (1.5, 2.5, ["up"]), (2.5, 3.5, ["down"])):
        if t0 <= t < t1: keys = [pre(i) + x for i in range(2 if P2 is not None else 1) for x in k]
    if 4 <= t < 10:   # attack taps by both, the partner also fires and jumps
        ph = int((t - 4) / 0.45) % 6
        base = [("a",), ("a",), ("c",), ("a",), ("b",), ("a",)][ph]
        keys = [pre(i) + x for i in range(2 if P2 is not None else 1) for x in (base if (i != wv or base[0] != "c") else ("a",))]
        if int((t - 4) / 0.45) != int((t - 4) / 0.45 - 0.1): pass
    if os.environ.get("COOPGUN") and float(os.environ.get("GUN_FROM", "5")) <= t < float(os.environ.get("GUN_TO", "10")) and P2 is not None:   # the partner holds its gun button while the Wolverine player's Berserker (poked at 6 s) runs: shots must be the partner's only
        keys = [pre(1 - wv) + "c"]
    for t0 in (12, 22):   # Berserker of the Wolverine player: his special, attack + jump together
        u = t - t0
        if 0 <= u < 0.6:
            seq = (0, [wp + "a", wp + "b"]), (0.4, [])
            for tt, ks in seq:
                if u >= tt: keys = ks
            if u < 0.1: bz_t.append(t)
    if "poked" not in done and t > 0.8:
        done.add("poked")
        for off in (0x83c0, 0x84c0):
            s.m.call("memory_write", address=hex(s.syms["RAMB"] + off), size="word", value=hex(40)); s.m.call("memory_write", address=hex(s.syms["RAMB"] + off + 2), size="word", value=hex(40))
        s.log("hp poked to 40")
    for base, cnt in ((0x9580, 20), (0x9280, 4)):   # harness assist: no enemies, so only the healing factor moves a health
        buf = s.ram(base, cnt * 0xc0)
        for k in range(cnt):
            if buf[k * 0xc0]: s.m.call("memory_write", address=hex(s.syms["RAMB"] + base + k * 0xc0), size="byte", value=hex(0))
    hb = s.ram(0x8380, 0x200)
    hpn = (int.from_bytes(hb[0x40:0x42], "big"), int.from_bytes(hb[0x140:0x142], "big"))
    if hpn != hp_last:
        hp_rows.append(dict(t=round(t, 2), v=v, hp=list(hpn), st=[hb[4:7].hex(), hb[0x104:0x107].hex()], char=[hb[0xd2], hb[0x1d2]], hl_t=(list(s.m.read(s.syms["hl_t"], 2)) if "hl_t" in s.syms else None)))
        hp_last[:] = list(hpn)
    for t0 in ():   # (the poked Berserker request of the old gun-slot entry is gone: the special press above is the entry) (the motion's timing against the partner is not what is under test); the motion itself is played at 12 and 22
        if t >= t0 and ("bzreq", t0) not in done and "bz_req" in s.syms:
            done.add(("bzreq", t0)); s.m.call("memory_write", address=hex(s.syms["bz_req"] + wv), size="byte", value=hex(6))
    s.set(keys)
    # trace
    blk = [a[0x380:0x480], a[0x480:0x580]] if len(a) >= 0x580 else [a[0x380:0x480], bytes(0x100)]
    b2 = s.ram(0x8380, 0x200)
    blk = [b2[:0x100], b2[0x100:]]
    sh = s.ram(0x8680, 0x0f00)
    for o in range(0, len(sh) - 0x80, 0x100):
        b = sh[o:o + 0x100]
        if b[0] and b[8] == 4:
            ow = int.from_bytes(b[0x26:0x28], "big")
            shot_owner["wolverine" if ow == 0x8380 + 0x100 * wv else "partner" if ow in (0x8380, 0x8480) else "other"] += 1
    bzb = s.syms.get("sat_wv_bz")
    for i in range(2 if P2 is not None else 1):
        b = blk[i]
        stw = b[4:7].hex(); rec = int.from_bytes(b[0x1c:0x20], "big")
        states[i][stw] += 1
        cls = "native" if NAT_LO <= rec < NAT_HI else "other"
        pairs[(i, "wolverine" if i == wv else "stock", cls)] += 1
        if i == wv and b[0] and cls != "native" and len(anomalies) < 40: anomalies.append(dict(t=round(t, 2), player=i, state=stw, rec=hex(rec)))
        if stw != last_st[i]:
            rows.append(dict(t=round(t, 2), p=i + 1, state=stw, rec=hex(rec), cls=cls, hp=int.from_bytes(b[0x40:0x42], "big"), char=b[0xd2], bz=(s.m.read(bzb, 1)[0] if bzb else -1)))
            last_st[i] = stw
    if t > SECS:
        os.makedirs(OUT, exist_ok=True)
        with open(OUT + "/trace.jsonl", "w") as fh:
            for r in rows: fh.write(json.dumps(r) + "\n")
        json.dump(dict(p1=P1, p2=P2, wolverine_player=WV, states=[dict(x) for x in states], pairs={str(k): c for k, c in pairs.items()}, anomalies=anomalies, shots=dict(shot_owner), berserker_motions_at=bz_t[:4]),
                  open(OUT + "/summary.json", "w"), indent=1)
        with open(OUT + "/hp.jsonl", "w") as fh:
            for r in hp_rows: fh.write(json.dumps(r) + chr(10))
        s.shot("coop_end"); s.log("coop done", dict(shot_owner), len(anomalies), "anomalies"); s.stop()
