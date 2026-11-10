"""Lane wv-native3 11-09: unassisted soak of native Wolverine under Yaba (own copy, own port; keys by PostMessage to that window only). Same navigation as native_states_proof.py (front end to the first standing
frame in stage 02), then a free-running play policy for PROOF_SECS seconds with a trace of everything lifecycle-relevant:
  - every change of the player's state word (+4..6) with the frame record, timer, health, stage word, lives, the Berserker byte and the vblank counter,
  - anomalies: a frame record outside his native window (a donor record he should not show), the same state held for more than PROOF_STUCK vblanks, a fatal,
  - the set of states and (state, record range) pairs reached, with counts.
Policy: walk toward the nearest enemy (tag 0c), tap attack when near, attack + jump together every few seconds (Berserker, his special), jump now and then; a KO is followed by start pulses (continue). Health is topped up only with PROOF_ASSIST=1.
Output: PROOF_OUT/soak.jsonl (events) and PROOF_OUT/soak_summary.json. Env: PROOF_OUT, PROOF_SECS (default 300), PROOF_SEED, PROOF_P2=1 (also drive nothing for player 2; only logs it), PROOF_TITLE.
usage: YABA_CUE=<work>/sat.cue YABA_ELF=<work>/sat.elf YABA_EXE=<own yaba>/yabasanshiro.exe YABA_INI=<own yaba>/yabause.ini YABA_PORT=9718 YABA_VIDEO=1 YABA_SOUND=0 PROOF_OUT=<dir> python saturn/rt/play_yaba.py <work> tools/wolverine/native_soak.py 1500"""
import collections, ctypes, json, os, random, re, time

OUT = os.environ["PROOF_OUT"]
SECS = float(os.environ.get("PROOF_SECS", "300"))
STUCK = int(os.environ.get("PROOF_STUCK", "400"))
TITLE = os.environ.get("PROOF_TITLE", "AvP NATIVE: soak [port 9718]")
ASSIST = bool(os.environ.get("PROOF_ASSIST"))
rnd = random.Random(int(os.environ.get("PROOF_SEED", "7")))
st = dict(lastp=0.0, started=False, n=0, titled=False)
NAT_LO, NAT_HI = 0x300000, 0x310000


def rec_class(rec):
    if NAT_LO <= rec < NAT_HI: return "native"
    if rec == 0: return "none"
    return "other:%x" % (rec >> 12)


def enemies(s):
    buf = s.ram(0x9580, 20 * 0xc0); out = []   # the enemy pool: 20 blocks of 0xc0 from ff9580
    for o in range(0, 20 * 0xc0, 0xc0):
        b = buf[o:o + 0xc0]
        if b[0] and b[1] != 0 and int.from_bytes(b[0x40:0x42], "big") < 0x8000:
            out.append((int.from_bytes(b[0x10:0x12], "big"), int.from_bytes(b[0x18:0x1a], "big")))
    return out


nav_t = [0.0]


def nav(s, ev):
    """front end / continue: the same navigation step() uses, driven while the player block is inactive"""
    now = time.time()
    a = s.ram(0x8000, 0x400)
    sc = s.word("sat_home_screen")
    if now - nav_t[0] < 0.6: return
    sel = a[1] == 2 and not a[0x380] and not a[0x1e8] and not a[0x1e9] and a[0x1b0] == 0
    if sc in (1, 3): nav_t[0] = now; s.pulse("start", .1); return
    if sel:
        nav_t[0] = now
        if a[0x1cc] != 2: s.pulse("right", .08)
        else: s.pulse("start", .1)
        ev.write(json.dumps(dict(nav="select", cursor=a[0x1cc], mode=a[1])) + chr(10))
        return
    if a[1] == 4 or a[1] == 0 or a[0x1b0]:   # game over / attract: coin then start
        nav_t[0] = now; s.pulse("x" if a[0x18c] == 0 else "start", .08)
        ev.write(json.dumps(dict(nav="continue", mode=a[1], attract=a[0x1b0], credits=a[0x18c])) + chr(10))
        return
    nav_t[0] = now; s.pulse("start", .1)


def soak(s):
    m = s.m
    os.makedirs(OUT, exist_ok=True)
    ev = open(OUT + "/soak.jsonl", "w")
    bz = s.syms.get("sat_wv_bz")
    states, pairs = collections.Counter(), collections.Counter()
    anomalies = []
    last_state, last_v, since_v = None, 0, 0
    t_end = time.time() + SECS
    seq, seq_i, seq_t = None, 0, 0
    t_qcf = time.time() + 6
    jumped = 0
    polls = 0
    ko_seen = 0
    v0 = int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big")
    s.shot("soak_start")
    n_shots = [0]
    while time.time() < t_end:
        polls += 1
        blk = s.ram(0x8380, 0x200)
        p1, p2 = blk[:0x100], blk[0x100:]
        v = int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big")
        stw = p1[4:7].hex()
        rec = int.from_bytes(p1[0x1c:0x20], "big")
        hp = int.from_bytes(p1[0x40:0x42], "big")
        rc = rec_class(rec)
        states[stw] += 1
        pairs[(stw, rc)] += 1
        if p1[0] and rc != "native" and p1[0xd2] == 1:
            if len(anomalies) < 40: anomalies.append(dict(v=v, kind="record outside the native window", state=stw, rec=hex(rec)))
        if stw != last_state:
            row = dict(v=v, state=stw, rec=hex(rec), cls=rc, timer=int.from_bytes(p1[0x0a:0x0c], "big"), hp=hp, sub=p1[7], face=p1[0x0f], x=int.from_bytes(p1[0x10:0x12], "big"),
                       stage=s.ram16(0x81e8), p2=p2[4:7].hex(), bz=(m.read(bz, 1)[0] if bz else -1), alive=p1[0], tag=p1[8], swing=p1[0x67], hit=p1[0x6e])
            ev.write(json.dumps(row) + "\n"); ev.flush()
            if stw in ('020008', '020006') and n_shots[0] < int(os.environ.get('SOAK_SHOTS', '0')) and polls % 2 == 0: n_shots[0] += 1; s.shot('soak_%s_v%d' % (stw, v))   # looks: his special and attack chain in free-running play
            last_state, since_v = stw, v
        elif v - since_v > STUCK and stw not in ("020000", "020002", "080000"):
            if len(anomalies) < 40: anomalies.append(dict(v=v, kind="state held", state=stw, vblanks=v - since_v, rec=hex(rec)))
            since_v = v
        if p1[0] == 0 or hp == 0xffff or stw.startswith("04"):
            ko_seen += 1
        if p1[0] == 0:   # between lives: the game's own continue (coin, start) and the select screen: pick Wolverine's slot again, then start
            nav(s, ev)
            time.sleep(0.05)
            continue
        # --- input policy
        keys = []
        if ASSIST and hp != 0xffff and hp < 40:
            s.m.call("memory_write", address=hex(s.syms["RAMB"] + 0x83c0), size="word", value=hex(0x65))
        if seq is not None:
            if seq_i < len(seq):
                if time.time() - seq_t > seq[seq_i][1]:
                    seq_i += 1; seq_t = time.time()
                if seq_i < len(seq): keys = [k if k not in ("fwd",) else ("right" if p1[0x0f] else "left") for k in seq[seq_i][0]]
            if seq_i >= len(seq): seq = None
        else:
            en = enemies(s)
            px, pz = int.from_bytes(p1[0x10:0x12], "big"), int.from_bytes(p1[0x18:0x1a], "big")
            near = min(en, key=lambda e: abs(e[0] - px) + abs(e[1] - pz)) if en else None
            if near:
                dx, dz = near[0] - px, near[1] - pz
                if abs(dx) > 70: keys.append("right" if dx > 0 else "left")
                elif abs(dx) < 40: keys.append("left" if dx > 0 else "right")
                if dz < -3: keys.append("up")
                elif dz > 3: keys.append("down")
                if abs(dx) < 90 and abs(dz) < 8 and polls % 3 == 0: keys.append("a")
                if time.time() > t_qcf and abs(dx) < 120:
                    seq = [(["a", "b"], .09), (["a", "b"], .09), ([], .05)]; seq_i, seq_t = 0, time.time()
                    t_qcf = time.time() + rnd.uniform(4, 9)
                if time.time() > jumped and rnd.random() < 0.02:
                    keys.append("b"); jumped = time.time() + 4
            else:
                keys.append("right")
        s.set(keys)
        if polls % 40 == 0:
            s.log("soak", stw, "hp", hp, "v", v - v0, "states", len(states), "anoms", len(anomalies))
    s.set([])
    s.shot("soak_end")
    summary = dict(polls=polls, vblanks=v - v0, states=dict(states), pairs={"%s/%s" % k: c for k, c in pairs.items()}, anomalies=anomalies, ko_polls=ko_seen)
    json.dump(summary, open(OUT + "/soak_summary.json", "w"), indent=1)
    s.log("soak done", len(states), "states", len(anomalies), "anomalies")
    s.stop()


def step(v, s):
    now = time.time()
    if not st["titled"]:
        st["titled"] = True
        try:
            ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), TITLE)
        except Exception as e:
            s.log("retitle failed", e)
    if st["started"]:
        return
    a = s.ram(0x8000, 0x400)
    sc = s.word("sat_home_screen")
    st["n"] += 1
    sel0 = a[1] == 2 and not a[0x380] and not a[0x1e8] and not a[0x1e9] and a[0x1b0] == 0
    if os.environ.get("PROOF_WARP") and sel0 and sc == 0 and "sat_home_warp" in s.syms and a[0x18c] is not None and s.word("sat_home_warp") == 0:   # start the game at another stage: home.c replaces stage word 2 by sat_home_warp (the menus clear it, so it is set on the select screen)
        s.m.call("memory_write", address=hex(s.syms["sat_home_warp"] + 2), size="word", value=hex(int(os.environ["PROOF_WARP"], 16)))
        s.log("warp set", os.environ["PROOF_WARP"], "screen", sc, "mode", a[1])
    if sc == 3:
        if now - st["lastp"] > 1.0:
            st["lastp"] = now; s.pulse("start", .1)
        return
    if sc == 1:
        if now - st["lastp"] > .7:
            st["lastp"] = now; s.pulse("start", .1)
        return
    sel = a[1] == 2 and not a[0x380] and not a[0x1e8] and not a[0x1e9] and a[0x1b0] == 0
    if sel:
        if a[0x1cc] != 2 and now - st["lastp"] > .5:
            st["lastp"] = now; s.pulse("right", .08); return
        if a[0x1cc] == 2 and now - st["lastp"] > .7:
            st["lastp"] = now; s.pulse("start", .1)
        return
    if not (a[1] == 2 and a[0x380] and a[0x1e9] and a[0x1b0] == 0 and a[0x384] == 2):
        if a[0x1b0] == 0 and not a[0x380] and now - st["lastp"] > .7:
            st["lastp"] = now; s.pulse("start", .1)
        return
    if a[0x384:0x387].hex() != "020000":
        return
    st["started"] = True
    soak(s)
