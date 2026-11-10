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
    v0 = int.from_bytes(m.read(s.syms["sat_dbg"] + 8, 4), "big"); t_end = time.time() + secs; last = None
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
        time.sleep(0.04)
    m.call("pause")
    s.shot("heal_end")
    s.log("heal leg done")
    s.stop()


def keys_for(face):   # Berserker Barrage: QCF + attack, forward = right when his facing byte (+0f) is set
    fw = "right" if face else "left"
    return [(0, []), (6, ["down"]), (12, ["down", fw]), (18, [fw]), (22, [fw, "a"]), (26, []), (200, [])]


def flash_leg(s):
    m = s.m
    os.makedirs(OUT, exist_ok=True)
    m.call("pause"); s.set([])
    nsp.approach(s)
    s.log("save", m.call("save_state", slot=nsp.SLOT)[:60])
    frames = int(os.environ.get("PROOF_FRAMES", "90"))
    for tag in ("run1",):
        m.call("pause"); m.call("load_state", slot=nsp.SLOT); time.sleep(0.5)
        os.makedirs(OUT + "/" + tag, exist_ok=True)
        keys = []; k = 0
        KEYS = keys_for(s.ram(0x838f, 1)[0] & 1)
        s.log("facing", KEYS[2][1])
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


def proof(s):
    (heal_leg if MODE == "heal" else flash_leg)(s)


nsp.enemies = lambda s: [(e['x'], e['z']) for e in enemies_full(s)]   # native_states_proof walks ff9a00 in steps of 0x100: not the enemy pool's grid
nsp.proof = proof
nsp.TITLE = os.environ.get("PROOF_TITLE", "AvP FEATURES: " + MODE + " [port 9724]")
step = nsp.step
