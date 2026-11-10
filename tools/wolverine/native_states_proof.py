"""Lane wv-native-gfx 11-09 (step 2): Yaba proof of every native state group (chain LP LP HP, jump and air attack, Berserker, hits/knockdown/getup). Same harness as native_attack_proof.py with the
schedule below (paused legs: native and Schaefer, one frame at a time, the trace has the player block, record and state each frame). Original header follows.

Yaba proof of Wolverine's native idle, walk and first claw attack (build flag -DSAT_WV_NATIVE_GFX; plan V2 section 5), run under saturn/rt/play_yaba.py
(own Yaba copy, own port, keys by PostMessage to that window only):
  YABA_CUE=<work>/sat.cue YABA_ELF=<work>/sat.elf YABA_EXE=<own yaba>/yabasanshiro.exe YABA_INI=<own yaba>/yabause.ini YABA_PORT=9718 YABA_VIDEO=1 YABA_SOUND=0 \
  PROOF_OUT=<dir> PROOF_FREERUN=<seconds> python saturn/rt/play_yaba.py <work> tools/wolverine/native_attack_proof.py 900
Navigation is the front end's. At the first standing frame in stage 02 the core is paused and the state saved (slot 3). Each leg loads that state, so every leg starts from the same
machine state, and sets the mode by poking the debug port:
  native   wv_nat_dbg = 1                         his native data on (idle, walk and first claw attack are the game's own records)
  skin     wv_nat_dbg = 0                         the replacement pass and the move clock (the integration build's behaviour; the data of the flag is off)
  schaefer wv_nat_dbg = 0, sat_guest_sel = 0      the arcade character (setting off)
Paused legs step one frame at a time (framebuffer_burst) through idle, walk and a claw attack; the trace has the player's block, frame record, timer, flags, hold, and the first enemy's
health every frame, and the first frames of the attack are kept as pictures. Free-running legs run the same input schedule (keys set when the emulated vblank counter passes a threshold)
and report emulated vblanks per wall second, pictures started, shown and skipped, plot waits, the guest pass's emulated ticks (sat_gprof) and the pose progression of the player.
Input is paced by the poll of the emulated vblank counter (a read waits for a frame), not by a scripted pad inside the machine, so a press can be a frame or two late; the same loop
runs every leg."""
import ctypes, json, os, time

OUT = os.environ["PROOF_OUT"]
FREE = float(os.environ.get("PROOF_FREERUN", "0"))
SLOT = int(os.environ.get("PROOF_SLOT", "3"))
TITLE = os.environ.get("PROOF_TITLE", "AvP NATIVE: states [port 9718]")
st = dict(lastp=0.0, started=False, n=0, titled=False)
MODES = (("native", 1, None), ("schaefer", 0, 0))
# (frames after the leg starts, keys held from there): attack taps every 14 frames for 160 frames (an enemy walking in is met in every leg), then walk away and back
SCHEDULE = [(0, []), (6, ["a"]), (9, []), (22, ["a"]), (25, []), (38, ["a"]), (41, []), (100, ["b"]), (104, []), (190, ["b"]), (194, []), (200, ["a"]), (203, []),
            (260, ["down"]), (266, ["down", "right"]), (272, ["right"]), (276, ["right", "a"]), (280, []), (360, ["left"]), (420, []), (480, ["a"]), (483, []), (500, ["a"]), (503, []), (700, [])]


def poke(s, name, val):
    s.m.call("memory_write", address=hex(s.syms[name]), size="byte", value=hex(val))


def mode_set(s, tag, dbg, sel):
    poke(s, "wv_nat_dbg", dbg)
    if sel is not None:
        poke(s, "sat_guest_sel", sel)


def rec_bytes(s, rec):
    if rec >= 0x300000:
        return s.m.read(s.syms["wv_blk"] + rec - 0x300000, 16)
    return s.m.read(0x02400000 + rec, 16)


def snap(s, tag, f, keys):
    blk = s.ram(0x8380, 0x100)
    rec = int.from_bytes(blk[0x1c:0x20], "big")
    rb = rec_bytes(s, rec) if 0x160000 <= rec < 0x170000 or 0x300000 <= rec < 0x310000 else bytes(16)
    en = s.ram(0x9a00, 0x2d00)
    hp = sum(int.from_bytes(en[o + 0x40:o + 0x42], "big") for o in range(0, len(en) - 0x100, 0x100) if en[o] and en[o + 8] == 0x0c)
    d = s.m.read(s.syms["sat_dbg"], 12)
    row = dict(tag=tag, f=f, v=int.from_bytes(d[8:12], "big"), keys=keys, st=blk[4:7].hex(), x=int.from_bytes(blk[0x10:0x12], "big"), z=int.from_bytes(blk[0x18:0x1a], "big"),
               face=blk[0x0f], rec=hex(rec), timer=int.from_bytes(blk[0x0a:0x0c], "big"), flags=blk[0x24:0x26].hex(), hold=int.from_bytes(blk[0x90:0x92], "big"), hp=int.from_bytes(blk[0x40:0x42], "big"),
               rec_bytes=rb.hex(), enemy_hp=hp, native=int(0x300000 <= rec < 0x310000))
    with open(OUT + "/trace.jsonl", "a") as fh:
        fh.write(json.dumps(row) + chr(10))
    return row


def paused_leg(s, tag, dbg, sel, shots):
    m = s.m
    m.call("pause"); m.call("load_state", slot=SLOT); time.sleep(0.5)
    mode_set(s, tag, dbg, sel)
    os.makedirs(OUT + "/" + tag, exist_ok=True)
    keys = []; k = 0; end = SCHEDULE[-1][0]
    for f in range(end):
        while k < len(SCHEDULE) and SCHEDULE[k][0] <= f:
            keys = SCHEDULE[k][1]; k += 1
        s.set(keys)
        if f % 10 == 0: keep_alive(s)
        snap(s, tag, f, list(keys))
        m.call("framebuffer_burst", directory=OUT + "/" + tag, frames=1, prefix="f%04d_" % f)
    s.set([])
    s.log("paused leg", tag, "done")


def counters(s):
    d = s.m.read(s.syms["sat_dbg"], 0x68)
    out = dict(wall=time.time(), vblank=int.from_bytes(d[8:12], "big"), skips=int.from_bytes(d[0x64:0x68], "big"))
    for n in ("plot_started", "plot_shown", "sat_gfx_plot_waits"):
        if n in s.syms:
            out[n] = int.from_bytes(s.m.read(s.syms[n], 4), "big")
    if "sat_gprof" in s.syms:
        g = s.m.read(s.syms["sat_gprof"], 32)
        out["gprof"] = [int.from_bytes(g[i:i + 4], "big") for i in range(0, 32, 4)]
    return out


def free_leg(s, tag, dbg, sel, secs):
    m = s.m
    m.call("pause"); m.call("load_state", slot=SLOT); time.sleep(0.5)
    mode_set(s, tag, dbg, sel)
    m.call("resume"); time.sleep(0.3)
    a = counters(s); v0 = a["vblank"]; k = 0; keys = []; poses = []; last = None
    t_end = time.time() + secs
    while time.time() < t_end:
        v = counters(s)["vblank"] - v0 if False else int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big") - v0
        while k < len(SCHEDULE) and SCHEDULE[k][0] <= v % (SCHEDULE[-1][0] + 60):
            keys = SCHEDULE[k][1]; k += 1
        if v % (SCHEDULE[-1][0] + 60) < 5 and k >= len(SCHEDULE): k = 0
        s.set(keys)
        keep_alive(s)
        rec = int.from_bytes(s.ram(0x839c, 4), "big")
        if rec != last:
            poses.append(rec); last = rec
    s.set([])
    b = counters(s)
    row = dict(tag=tag, secs=round(b["wall"] - a["wall"], 2), vblanks=b["vblank"] - a["vblank"], vblank_per_s=round((b["vblank"] - a["vblank"]) / (b["wall"] - a["wall"]), 2),
               d_skips=b["skips"] - a["skips"], d_started=b.get("plot_started", 0) - a.get("plot_started", 0), d_shown=b.get("plot_shown", 0) - a.get("plot_shown", 0),
               d_waits=b.get("sat_gfx_plot_waits", 0) - a.get("sat_gfx_plot_waits", 0), record_changes_seen=len(poses), native_records_seen=sum(1 for p in poses if 0x300000 <= p < 0x310000),
               gprof_delta=[y - x for x, y in zip(a.get("gprof", [0] * 8), b.get("gprof", [0] * 8))])
    with open(OUT + "/trace.jsonl", "a") as fh:
        fh.write(json.dumps(row) + chr(10))
    s.log("free leg", row)
    m.call("pause")
    return row


def keep_alive(s):
    """harness assist, every leg alike: the player's health word is put back to its full value so an unattended run is not cut short by his death (the stage-02 enemies keep coming)"""
    s.m.call("memory_write", address=hex(s.syms["RAMB"] + 0x83c0), size="word", value=hex(0x65))


def enemies(s):
    buf = s.ram(0x9a00, 0x2d00); out = []
    for o in range(0, len(buf) - 0x80, 0x100):
        b = buf[o:o + 0x100]
        if b[0] and b[8] == 0x0c and b[1] != 0:
            out.append((int.from_bytes(b[0x10:0x12], "big"), int.from_bytes(b[0x18:0x1a], "big")))
    return out


def approach(s):
    """free-run toward the nearest enemy (as tools v4rec.py did), pause with him in front, so the attack legs have a target"""
    m = s.m
    m.call("resume")
    t0 = time.time(); near = None
    while time.time() - t0 < 60:
        a = s.ram(0x8380, 0x20)
        px, pz = int.from_bytes(a[0x10:0x12], "big"), int.from_bytes(a[0x18:0x1a], "big")
        en = enemies(s)
        near = min(en, key=lambda e: abs(e[0] - px) + abs(e[1] - pz)) if en else None
        if near and 55 < abs(near[0] - px) < 85 and abs(near[1] - pz) < 5 and a[4:7].hex() in ("020000", "020002"):
            break
        keys = []
        if near:
            dx = near[0] - px
            if dx < -85: keys.append("left")
            elif dx > 85: keys.append("right")
            elif abs(dx) < 55: keys.append("right" if dx < 0 else "left")   # too close: step back
            if near[1] < pz - 3: keys.append("up")
            elif near[1] > pz + 3: keys.append("down")
        s.set(keys)
        keep_alive(s)
        time.sleep(0.02)
    s.set([])
    keep_alive(s)
    m.call("pause")
    s.log("approach done", near, px, pz)


def proof(s):
    m = s.m
    m.call("pause"); s.set([])
    os.makedirs(OUT, exist_ok=True)
    if not os.environ.get("PROOF_NOAPPROACH"):
        approach(s)
    s.log("save", m.call("save_state", slot=SLOT)[:80])
    for tag, dbg, sel in MODES:
        paused_leg(s, tag, dbg, sel, True)
    if FREE:
        for rep in range(2):
            for tag, dbg, sel in MODES:
                free_leg(s, "free_%s_%d" % (tag, rep), dbg, sel, FREE)
    m.call("pause")
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
    if st["n"] % 100 == 0:
        s.log("nav", sc, a[1], a[0x380], a[0x1e9], a[0x1b0], a[0x384], a[0x385:0x387].hex())
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
    proof(s)
