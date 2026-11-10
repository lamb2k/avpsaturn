"""Lane wv-features 11-09: Yaba proof of the healing factor and the Berserker flash (build switches SAT_WV_HEAL, SAT_WV_FLASH). Reuses native_states_proof.py's navigation
(front end, stage 02, first standing frame) and its keep-alive/approach helpers; runs under saturn/rt/play_yaba.py (own Yaba copy, own port, keys by PostMessage to that window only):
  YABA_CUE=<work>/sat.cue YABA_ELF=<work>/sat.elf YABA_EXE=<own yaba>/yabasanshiro.exe YABA_INI=<own yaba>/yabause.ini YABA_PORT=9724 YABA_VIDEO=1 YABA_SOUND=0 \
  PROOF_OUT=<dir> PROOF_MODE=heal|flash [PROOF_SECS=25] PYTHONPATH=tools/wolverine python saturn/rt/play_yaba.py <work> tools/wolverine/wvf_proof.py 900
heal : at the first standing frame his health is set to PROOF_HP (default 40), the core runs free for PROOF_SECS seconds with no input and the trace has (emulated vblank, health,
       state, enemies' distance) about every 50 ms, so the health-over-time curve of the build can be compared with the same run of the build without the switch.
flash: approach an enemy, save, then a paused leg steps one frame at a time through the Berserker motion (down, down+right, right, attack) and keeps every picture, with a trace of
       the player's state, the enemies' hitstop byte (+0x2c) and positions, and the VDP2 colour offset registers, so the flash and the freeze can be read off frame by frame."""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_states_proof as nsp

OUT = nsp.OUT
MODE = os.environ.get("PROOF_MODE", "heal")


def wrow(row):
    with open(OUT + "/trace.jsonl", "a") as fh:
        fh.write(json.dumps(row) + chr(10))


def enemies_full(s):   # the game's enemy pool (tag 0c): 20 slots of 0xc0 bytes from ff9580
    buf = s.ram(0x9580, 20 * 0xc0); out = []
    for k in range(20):
        b = buf[k * 0xc0:(k + 1) * 0xc0]
        if b[0] and b[8] == 0x0c:
            out.append(dict(slot=k, x=int.from_bytes(b[0x10:0x12], "big"), z=int.from_bytes(b[0x18:0x1a], "big"), hs=b[0x2c], hp=int.from_bytes(b[0x40:0x42], "big"), st=b[4:7].hex()))
    return out


def heal_leg(s):
    m = s.m
    hp0 = int(os.environ.get("PROOF_HP", "40"))
    secs = float(os.environ.get("PROOF_SECS", "25"))
    os.makedirs(OUT, exist_ok=True)
    m.call("pause"); s.set([])
    s.log("poke hp", hp0)
    m.call("memory_write", address=hex(s.syms["RAMB"] + 0x83c0), size="word", value=hex(hp0))
    m.call("memory_write", address=hex(s.syms["RAMB"] + 0x83c2), size="word", value=hex(hp0))
    s.shot("heal_start")
    if os.environ.get("PROOF_BLOCKS"):   # which blocks of the object pools are active: offset, class, tag, kind, health
        buf = m.read(s.syms["RAMB"] + 0x9000, 0x3800)
        wrow(dict(mode="blocks", act=[(hex(0x9000 + o), buf[o], buf[o + 2], buf[o + 8], int.from_bytes(buf[o + 0x40:o + 0x42], "big")) for o in range(0, 0x3800 - 0x40, 0x40) if buf[o] and buf[o + 8] in (0x0c, 0x10, 0x14, 0x04, 0x08, 0x20)]))
    m.call("resume")
    v0 = int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big"); t_end = time.time() + secs; last = None; shot_hp = hp0
    while time.time() < t_end:
        v = int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big") - v0
        blk = s.ram(0x8380, 0x100)
        hp = int.from_bytes(blk[0x40:0x42], "big")
        en = enemies_full(s)
        if os.environ.get("PROOF_CLEAR"):   # harness assist, every leg alike: the stage's enemies (pools tag 0c and 08) are taken out of play (active byte 0) so the curve shows only the healing factor
            for base, cnt in ((0x9580, 20), (0x9280, 4)):
                buf = s.ram(base, cnt * 0xc0)
                for k in range(cnt):
                    if buf[k * 0xc0]:
                        m.call("memory_write", address=hex(s.syms["RAMB"] + base + k * 0xc0), size="byte", value=hex(0))
        near = min((abs(e["x"] - int.from_bytes(blk[0x10:0x12], "big")) for e in en), default=9999)
        row = dict(mode="heal", v=v, hp=hp, hp_seen=int.from_bytes(blk[0x42:0x44], "big"), st=blk[4:7].hex(), enemies=len(en), nearest=near)
        for n in ("hl_t", "hl_hp"):
            if n in s.syms:
                row[n] = list(m.read(s.syms[n], 2))
        if row != last:
            wrow(row); last = row
        if os.environ.get("PROOF_SHOTS") and hp >= shot_hp + 10 and hp < 200:   # a picture each time the health is 10 higher: the HUD bar rises
            shot_hp = hp
            s.shot("heal_hp%03d" % hp)
        time.sleep(0.04)
    m.call("pause")
    s.shot("heal_end")
    s.log("heal leg done")
    s.stop()


def keys_for(face):   # since native 035d44c Berserker is Schaefer's special: attack + jump together (state 020008), no motion
    return [(0, []), (8, ["a", "b"]), (13, []), (200, [])]


def flash_leg(s):
    m = s.m
    os.makedirs(OUT, exist_ok=True)
    m.call("pause"); s.set([])
    for attempt in range(6):   # a state saved in a hit reaction would ignore the motion: try again until the loaded state stands
        nsp.approach(s)
        s.log("save", m.call("save_state", slot=nsp.SLOT)[:60])
        m.call("load_state", slot=nsp.SLOT); time.sleep(0.5)
        st = s.ram(0x8384, 3).hex()
        s.log("loaded state", st, "attempt", attempt)
        if st in ("020000", "020002"):
            break
        m.call("resume"); time.sleep(1.5); m.call("pause")
    frames = int(os.environ.get("PROOF_FRAMES", "90"))
    for tag in ("run1",):
        m.call("pause"); m.call("load_state", slot=nsp.SLOT); time.sleep(0.5)
        os.makedirs(OUT + "/" + tag, exist_ok=True)
        keys = []; k = 0
        KEYS = keys_for(s.ram(0x838f, 1)[0] & 1)
        s.log("keys", KEYS)
        for f in range(frames):
            while k < len(KEYS) and KEYS[k][0] <= f:
                keys = KEYS[k][1]; k += 1
            s.set(keys)
            nsp.keep_alive(s)
            blk = s.ram(0x8380, 0x100)
            en = enemies_full(s)
            row = dict(mode="flash", f=f, keys=list(keys), st=blk[4:7].hex(), x=int.from_bytes(blk[0x10:0x12], "big"), face=blk[0x0f], enemies=en[:6],
                       vdp2=m.read(0x25F80110, 16).hex() if os.environ.get("PROOF_VDP2") else "")
            for n in ("fl_left", "fl_done"):
                if n in s.syms:
                    row[n] = m.read(s.syms[n], 1)[0]
            wrow(row)
            m.call("framebuffer_burst", directory=OUT + "/" + tag, frames=1, prefix="f%04d_" % f)
        s.set([])
    m.call("pause")
    s.log("flash leg done")
    s.stop()


def retitle(s):
    """Yaba puts its own title back on pause/resume and state loads; OBS finds the window by title, so ours is set again (and read back)."""
    import ctypes
    ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), nsp.TITLE)
    b = ctypes.create_unicode_buffer(200)
    ctypes.windll.user32.GetWindowTextW(ctypes.c_void_p(s.hwnd), b, 200)
    return b.value


def clip_leg(s):
    """Free-running footage for OBS (PROOF_MODE=clip): walk to the nearest enemy, Berserker (QCF + attack) when within reach, rest, repeat; health is put back to 60 under 30 (harness assist)."""
    import subprocess
    m = s.m
    secs = float(os.environ.get("PROOF_SECS", "45"))
    os.makedirs(OUT, exist_ok=True)
    m.call("pause"); s.set([])
    nsp.approach(s)
    obs = None
    s.log("title", retitle(s))
    if os.environ.get("PROOF_OBS"):
        obsdir = "C:/Program Files/obs-studio/bin/64bit"
        obs = subprocess.Popen([obsdir + "/obs64.exe", "--profile", "avp-features", "--collection", "avp-features", "--startrecording", "--minimize-to-tray", "--disable-updater", "--disable-shutdown-check"], cwd=obsdir)
        s.log("obs started", obs.pid)
    m.call("resume")
    s.log("title", retitle(s))
    time.sleep(8 if obs else 0.5)
    s.log("title", retitle(s))
    vb = lambda: int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big")
    t_end = time.time() + secs; n = 0
    while time.time() < t_end:
        blk = s.ram(0x8380, 0x100)
        hp = int.from_bytes(blk[0x40:0x42], "big"); face = blk[0x0f] & 1
        if hp < 30 or hp > 60000:
            m.call("memory_write", address=hex(s.syms["RAMB"] + 0x83c0), size="word", value=hex(60))
        px, pz = int.from_bytes(blk[0x10:0x12], "big"), int.from_bytes(blk[0x18:0x1a], "big")
        en = enemies_full(s)
        near = min(en, key=lambda e: abs(e["x"] - px) + abs(e["z"] - pz)) if en else None
        keys = []
        if near and blk[4:7].hex() in ("020000", "020002", "020202", "020200") and abs(near["x"] - px) < 140 and abs(near["z"] - pz) < 14:
            fw = "right" if near["x"] > px else "left"
            v0 = vb(); n += 1
            for off, ks in ((0, ["down"]), (6, ["down", fw]), (12, [fw]), (16, [fw, "a"]), (20, [])):
                while vb() - v0 < off: time.sleep(0.005)
                s.set(ks)
            s.log("berserker", n, "near", near["x"] - px)
            v1 = vb()
            while vb() - v1 < 140 and time.time() < t_end: time.sleep(0.05)
            continue
        if near:
            dx = near["x"] - px
            keys = ["right" if dx > 0 else "left"] if abs(dx) > 100 else []
            if near["z"] < pz - 3: keys.append("up")
            elif near["z"] > pz + 3: keys.append("down")
        s.set(keys)
        time.sleep(0.04)
        if n % 1 == 0 and int(time.time()) % 2 == 0:
            retitle(s)
    s.set([])
    if obs:
        time.sleep(1.5)
        subprocess.run(["taskkill", "/PID", str(obs.pid)], capture_output=True)   # WM_CLOSE: OBS finishes the recording file
        try:
            obs.wait(20)
        except Exception:
            obs.terminate()
        s.log("obs stopped")
    m.call("pause")
    s.log("clip done", n, "berserkers")
    s.stop()


def proof(s):
    {"heal": heal_leg, "flash": flash_leg, "clip": clip_leg}[MODE](s)


nsp.enemies = lambda s: [(e['x'], e['z']) for e in enemies_full(s)]   # native_states_proof walks ff9a00 in steps of 0x100: not the enemy pool's grid
nsp.proof = proof
nsp.TITLE = os.environ.get("PROOF_TITLE", "AvP FEATURES: " + MODE + " [port 9724]")
step = nsp.step
