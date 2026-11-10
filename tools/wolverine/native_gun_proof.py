"""Lane wv-native3 11-10 (gun proof, copy of native_coop.py): the partner of the Wolverine player fires its gun on a vblank schedule at a pinned enemy; every poll logs the shot pool, the pinned enemy and both players. Original header follows.
Lane wv-native3 11-09: native Wolverine in co-op under Yaba (two pads: YABA_P2=1 YABA_PAD=mcp, a Yaba exe with the pad_set tool; own copy and port). Adapted from tools/megaman/play_guest.py.
env: P1 / P2 = select grid moves ("" Warrior, "r" Schaefer slot = Wolverine, "d" Linn, "rd" Hunter); P2 unset = one player. WV = 1 or 2: which player is Wolverine (drives the Berserker motion; default 1).
PROOF_OUT = directory for trace.jsonl, summary.json and stills; PROOF_SECS = play seconds (default 40); PROOF_TITLE.
Script (seconds after both are in play): walk right, up, down; attack taps by both; the partner fires its gun (button c) and jumps (b); Wolverine plays the Berserker motion (down, down+forward, forward, attack)
twice, at about 12 s and 22 s. The trace has, per poll, both players' state words, frame records (class: native window or not), health, the Berserker byte, and the shot actors (tag 4) with their owner,
so "his Berserker allocates no shot, the partner's gun keeps working" is a count: shots_owned_by_wolverine must be 0, shots_owned_by_partner > 0 for a Warrior or Hunter partner."""
import collections, ctypes, glob, json, os, time

P1, P2 = os.environ.get("P1", "r"), os.environ.get("P2")
WV = int(os.environ.get("WV", "1"))
OUT = os.environ["PROOF_OUT"]
SECS = float(os.environ.get("PROOF_SECS", "40"))
TITLE = os.environ.get("PROOF_TITLE", "AvP NATIVE: coop [port 9718]")
shot_t = set(); lastp = 0; sel_at = None; play_at = None; done = set(); titled = False
NAT_LO, NAT_HI = 0x300000, 0x310000
rows = []; states = [collections.Counter(), collections.Counter()]; pairs = collections.Counter(); anomalies = []
shot_owner = collections.Counter(); last_st = [None, None]
bz_t = []


def pre(i):
    return "" if i == 0 else "p2"


def step(v, s):
    global lastp, sel_at, play_at, titled
    if not titled:
        titled = True
        try: ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), TITLE)
        except Exception as e: s.log("retitle failed", e)
    if v < 300: return
    if os.environ.get('WARP') and play_at is None:   # the home menu's stage select word (sat_home_warp replaces the start path's stage 02)
        try: s.m.call('memory_write', address=hex(s.syms['sat_home_warp']), size='word', value=os.environ['WARP'])
        except Exception: pass
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
                acts.append((k, int(os.environ.get('SEL_AT', '580')) + int(os.environ.get('SEL_STEP', '50')) * n))
            if os.environ.get('SEL_SHOT') and t // 60 not in shot_t: shot_t.add(t // 60); s.shot('sel_%04d' % t)
            hold = int(os.environ.get("SEL_HOLD", "30")); held = []
            for n, (k, at) in enumerate(acts):   # held through the pad_set path for SEL_HOLD vblanks (a pulse by window message was lost on the fast, SH-2 cache off emulator: every select landed on the default pair)
                if at <= t < at + hold: held.append(k)
                if t >= at and n not in done: done.add(n); s.log("select move", k, "at", t)
            conf = int(os.environ.get('SEL_AT', '580')) + int(os.environ.get('SEL_STEP', '50')) * len(acts) + 40
            if t >= conf and (t - conf) % 90 < 30: held += ["a"] + (["p2a"] if P2 is not None else [])
            s.set(held)
        elif a[0x1b0] == 0 and now - lastp > .7: lastp = now; s.pulse("start", .1)
        return
    if play_at is None:
        if a[0x384] != 2: return
        play_at = now; s.log("play kinds", a[0x380 + 0xd2], a[0x480 + 0xd2], "p2 on", a[0x480], "stage", a[0x1e8], a[0x1e9])
    if play_v[0] is None:
        play_v[0] = s.v; s.log("play at vblank", s.v)
    if os.environ.get("CAP"): cap(s)
    else: live(s)


def cap(s):
    """background check (owner 11-10): paused-free screenshots at fixed vblank offsets after the play start, the stage word and both players' character indexes in cap.json"""
    f = s.v - play_v[0]
    targets = [int(x) for x in os.environ["CAP"].split(",")]
    for tgt in targets:
        if f >= tgt and ("cap", tgt) not in done:
            done.add(("cap", tgt)); a = s.ram(0x81e8, 2); b = s.ram(0x8380, 0x200)
            name = "cap_%s_f%d" % (os.environ.get("CAPNAME", "x"), tgt); s.shot(name)
            caps.append(dict(name=name, f=f, v=s.v, stage=a.hex(), kinds=(b[0xd2], b[0x100 + 0xd2]), players_active=(b[0], b[0x100])))
            s.log("capture", name, "stage", a.hex(), "kinds", (b[0xd2], b[0x100 + 0xd2]))
    if f > max(targets) + 20:
        os.makedirs(OUT, exist_ok=True); json.dump(caps, open(OUT + "/cap.json", "w"), indent=1); s.stop()



def live(s):
    """free running, paced by the emulated vblank counter: one memory read a poll (players, shot pool and enemy pool are one block), key presses at fixed vblank offsets from the play start"""
    m = s.m
    k0 = s.ram(0x8380, 0x200); kinds = (k0[0xd2], k0[0x100 + 0xd2])   # the game's character index of each player: 0 Warrior, 1 Schaefer slot (Wolverine when selected), 2 Hunter, 3 Linn
    if want_kinds[0] is None:
        want_kinds[0] = kinds; s.log("character kinds P1,P2", kinds)
        if os.environ.get("WANT") and tuple(int(x) for x in os.environ["WANT"].split(",")) != kinds:
            s.log("MISMATCH: wanted", os.environ["WANT"], "got", kinds); os.makedirs(OUT, exist_ok=True); open(OUT + "/MISMATCH.txt", "w").write("wanted %s got %s" % (os.environ["WANT"], kinds)); s.stop(); return
    wvi = 0 if kinds[0] == 1 else 1 if kinds[1] == 1 else WV - 1; gp = 1 - wvi   # gp: index of the partner that fires; wvi: the player on the Schaefer slot
    G0, GN, GP, GH = int(os.environ.get("GUN_START", "240")), int(os.environ.get("GUN_N", "14")), int(os.environ.get("GUN_PERIOD", "50")), int(os.environ.get("GUN_HOLD", "8"))
    f = s.v - play_v[0]
    if f > G0 + GN * GP + 150:
        finish(s, gp, wvi); return
    if os.environ.get("GUEST_OFF") == "1" and f % 20 == 0:   # baseline: Wolverine not selected (the slot shows stock Schaefer)
        m.call("memory_write", address=hex(s.syms["sat_guest_sel"]), size="byte", value="0x0")
    pressing = any(G0 + k * GP <= f < G0 + k * GP + GH for k in range(GN))
    for k in range(GN):
        if f >= G0 + k * GP and ("press", k) not in done:
            done.add(("press", k)); presses.append(dict(k=k, vblank=s.v, offset=f))
    keys = [pre(gp) + "c"] if pressing else []
    if os.environ.get("WV_ACT"):   # long run: the Wolverine player also taps attack (every 100 vblanks) and plays his special (attack + jump) every 700
        wp = pre(wvi)
        if f % 100 < 12: keys.append(wp + "a")
        if 300 <= f % 700 < 312: keys += [wp + "a", wp + "b"]
    s.set(keys)
    if f - last_assist[0] >= 40:   # harness assist, both players alike: health topped up
        last_assist[0] = f
        for off in (0x83c0, 0x84c0): m.call("memory_write", address=hex(s.syms["RAMB"] + off), size="word", value=hex(0x65))
    blk = s.ram(0x8380, 0x2100)   # 8380 players, 8680 shot pool (15 x 0x100), 9580 enemy pool (20 x 0xc0)
    a = blk[:0x200]; gb = a[0x100 * gp:0x100 * gp + 0x100]
    gx, gz, gf = int.from_bytes(gb[0x10:0x12], "big"), int.from_bytes(gb[0x18:0x1a], "big"), gb[0x0f] & 1
    buf = blk[0x1200:0x1200 + 20 * 0xc0]; best = None
    for o in range(0, 20 * 0xc0, 0xc0):
        b = buf[o:o + 0xc0]
        if b[0] and b[1] != 0 and int.from_bytes(b[0x40:0x42], "big") < 0x8000:
            d = abs(int.from_bytes(b[0x10:0x12], "big") - gx)
            if best is None or d < best[0]: best = (d, o)
    if os.environ.get("PIN", "1") == "1" and f >= G0 - 80 and best is not None and f - last_pin[0] >= 4:   # the nearest live enemy in front of the firing player; health set once when first chosen
        last_pin[0] = f; o = best[1]; base = s.syms["RAMB"] + 0x9580 + o
        if pinned[0] != o:
            pinned[0] = o; m.call("memory_write", address=hex(base + 0x40), size="word", value=hex(0x190))
        dx = int(os.environ.get("PIN_DX", "130")); x = (gx + dx) if gf else (gx - dx)
        for off, val in ((0x10, x & 0xffff), (0x14, int.from_bytes(gb[0x14:0x16], "big")), (0x18, gz)):
            m.call("memory_write", address=hex(base + off), size="word", value=hex(val))
    pool = blk[0x300:0x300 + 0xf00]; ents = []
    for sl in range(15):
        b = pool[sl * 0x100:sl * 0x100 + 0x100]
        if b[0]:
            ents.append(dict(slot=sl, tag=b[8], kind=int.from_bytes(b[2:4], "big"), own26=int.from_bytes(b[0x26:0x28], "big"), own28=int.from_bytes(b[0x28:0x2a], "big"), x=int.from_bytes(b[0x10:0x12], "big"), z=int.from_bytes(b[0x18:0x1a], "big"), h=int.from_bytes(b[0x14:0x16], "big")))
    ehp = int.from_bytes(buf[pinned[0] + 0x40:pinned[0] + 0x42], "big") if pinned[0] is not None else None
    rows.append(dict(f=f, v=s.v, press=pressing, ids=[a[0], a[1], a[0xd2], a[0x100], a[0x101], a[0x100 + 0xd2]], in0=(s.word('in0', 0, 2) if pressing else None), btn=gb[0xee], btn_prev=gb[0xef], gun_player=gp + 1, gun_state=gb[4:7].hex(), other_state=a[0x100 * wvi + 4:0x100 * wvi + 7].hex(), pinned=pinned[0], ehp=ehp, px=gx, ex=(int.from_bytes(buf[pinned[0] + 0x10:pinned[0] + 0x12], "big") if pinned[0] is not None else None), ents=ents))
    if ents and len(shots_kept) < 24 and f - (shots_kept[-1] if shots_kept else -99) >= 3:   # pictures of the frames with pool objects
        shots_kept.append(f); s.shot("gun_%04d" % f)


def finish(s, gp, wvi):
    a = s.ram(0x8380, 0x200); kinds = (a[0xd2], a[0x100 + 0xd2]); names = {0: "Warrior", 1: "Schaefer-slot", 2: "Hunter", 3: "Linn"}
    label = ("Wolverine" if os.environ.get("GUEST_OFF") != "1" else "stock Schaefer") + (" P%d" % (wvi + 1)) + " + " + names.get(kinds[gp], "?") + " P%d" % (gp + 1) + ("; P%d fires" % (gp + 1))
    with open(OUT + "/gun_trace.jsonl", "w") as fh:
        for r in rows: fh.write(json.dumps(r) + chr(10))
    own = collections.Counter(); spawn = {}
    for r in rows:
        for e in r["ents"]:
            key = (e["slot"], e["tag"], e["kind"], e["own26"], e["own28"])
            spawn.setdefault(key, [r["f"], r["f"]])[1] = r["f"]
            own["wolverine" if (0x8380 + 0x100 * wvi) in (e["own26"], e["own28"]) else "partner" if (0x8380 + 0x100 * gp) in (e["own26"], e["own28"]) else "other"] += 1
    ehps = [r["ehp"] for r in rows if r["ehp"] is not None]
    gun_entries = sum(1 for i in range(1, len(rows)) if rows[i]["gun_state"] == "02000c" and rows[i - 1]["gun_state"] != "02000c")
    kinds_seen = collections.Counter((e["tag"], e["kind"]) for r in rows for e in r["ents"])
    json.dump(dict(label=label, env=dict(P1=P1, P2=P2, wolverine_index_p=wvi + 1, GUNP=gp + 1, WANT=os.environ.get("WANT"), GUEST_OFF=os.environ.get("GUEST_OFF"), SEQ=os.environ.get("SEQ")), char_kinds_p1_p2=kinds, presses=len(presses), gun_state_entries=gun_entries,
                   distinct_pool_objects=[dict(slot=k[0], tag=k[1], kind=hex(k[2]), own26=hex(k[3]), own28=hex(k[4]), first_frame=v0, last_frame=v1) for k, (v0, v1) in sorted(spawn.items(), key=lambda kv: kv[1][0])],
                   owner_frame_counts=dict(own), pool_kinds_seen={"tag%d kind%x" % k: c for k, c in kinds_seen.items()}, pinned_enemy_hp_first_last_min=[ehps[0] if ehps else None, ehps[-1] if ehps else None, min(ehps) if ehps else None], frames=len(rows)), open(OUT + "/gun_summary.json", "w"), indent=1)
    s.shot("gun_end"); s.log("gun proof done", label); s.stop()


caps = []; play_v = [None]; pinned = [None]; presses = []; last_assist = [-99]; want_kinds = [None]; last_pin = [-99]; shots_kept = []
