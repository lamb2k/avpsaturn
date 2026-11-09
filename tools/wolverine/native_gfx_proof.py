"""Lane wv-native-gfx 11-09: paused A/B capture of Wolverine's stand drawn by the game's own emitter (build flag -DSAT_WV_NATIVE_GFX).
Runs under saturn/rt/play_yaba.py (own Yaba copy, own port, keys by PostMessage to that window only):
  YABA_CUE=<work>/sat.cue YABA_ELF=<work>/sat.elf YABA_EXE=<own yaba>/yabasanshiro.exe YABA_INI=<own yaba>/yabause.ini YABA_PORT=9718 YABA_VIDEO=1 YABA_SOUND=0 \
  PROOF_OUT=<dir> PROOF_TITLE="AvP NATIVE-GFX: stand [port 9718]" python saturn/rt/play_yaba.py <work> tools/wolverine/native_gfx_proof.py 400
Navigation is the front end's (start, move the select cursor to Schaefer's slot, start); at the first standing frame in stage 02 the core is paused and:
  N  native on  (wv_nat_dbg = 1): the player's frame record 0x163158 holds the assembly pointer 0x300000, the game's emitter draws the stand
  S  skin       (wv_nat_dbg = 2): the pointer is put back, Schaefer's sprites are removed and the skin draws idle step 0 (the same pose)
  N2 native on again, to show the switch is reversible
Each leg steps FRAMES paused frames (framebuffer_burst) and keeps the last picture; a trace line holds the record pointer and the ROM word read over the debug port.
No ROM data is written to disk except the emulator's own screenshots (they stay on this PC)."""
import ctypes, json, os, time

OUT = os.environ["PROOF_OUT"]
TITLE = os.environ.get("PROOF_TITLE", "AvP NATIVE-GFX: stand [port 9718]")
FRAMES = int(os.environ.get("PROOF_FRAMES", "6"))
st = dict(lastp=0.0, started=False, n=0, titled=False)
RECORD = 0x163158


def rd(s, name, n):
    return s.m.read(s.syms[name], n)


def hexw(b):
    return b.hex()


def leg(s, tag, dbg):
    m = s.m
    m.call("memory_write", address=hex(s.syms["wv_nat_dbg"]), size="byte", value=hex(dbg))
    os.makedirs(OUT, exist_ok=True)
    m.call("framebuffer_burst", directory=OUT + "/" + tag, frames=FRAMES, prefix="f")
    blk = s.ram(0x8380, 0x100)
    rom = s.m.read(0x02400000 + RECORD, 20)   # the cart's ROM image, A-bus
    d = s.m.read(s.syms["sat_dbg"], 12)
    row = dict(tag=tag, dbg=dbg, vblank=int.from_bytes(d[8:12], "big"), state=blk[4:7].hex(), x=int.from_bytes(blk[0x10:0x12], "big"),
               z=int.from_bytes(blk[0x18:0x1a], "big"), face=blk[0x0f], frame_record=blk[0x1c:0x20].hex(), timer=int.from_bytes(blk[0x0a:0x0c], "big"),
               flags=blk[0x24:0x26].hex(), rom_record=rom.hex(), orig=rd(s, "wv_nat_orig", 4).hex(), dbg_now=rd(s, "wv_nat_dbg", 1).hex())
    with open(OUT + "/trace.jsonl", "a") as fh:
        fh.write(json.dumps(row) + "\n")
    m.call("framebuffer_screenshot", path=f"{OUT}/{tag}.png")
    s.log(tag, row)
    return row


def counters(s):
    d = s.m.read(s.syms["sat_dbg"], 0x68)
    out = dict(wall=time.time(), vblank=int.from_bytes(d[8:12], "big"), skips=int.from_bytes(d[0x64:0x68], "big"))
    for n in ("plot_started", "plot_shown", "sat_gfx_plot_waits"):
        if n in s.syms:
            out[n] = int.from_bytes(s.m.read(s.syms[n], 4), "big")
    return out


def freerun(s, tag, dbg, secs):
    """Free-running interval (not stepped): emulated vblanks per wall second, skipped and shown pictures, with the player left standing."""
    s.m.call("memory_write", address=hex(s.syms["wv_nat_dbg"]), size="byte", value=hex(dbg))
    s.m.call("resume")
    time.sleep(1.0)
    a = counters(s)
    time.sleep(secs)
    b = counters(s)
    blk = s.ram(0x8380, 0x20)
    row = dict(tag=tag, dbg=dbg, secs=round(b["wall"] - a["wall"], 2), vblanks=b["vblank"] - a["vblank"],
               vblank_per_s=round((b["vblank"] - a["vblank"]) / (b["wall"] - a["wall"]), 2), d_skips=b["skips"] - a["skips"],
               d_started=b.get("plot_started", 0) - a.get("plot_started", 0), d_shown=b.get("plot_shown", 0) - a.get("plot_shown", 0),
               d_waits=b.get("sat_gfx_plot_waits", 0) - a.get("sat_gfx_plot_waits", 0), state=blk[4:7].hex(), frame_record=blk[0x1c:0x20].hex())
    with open(OUT + "/trace.jsonl", "a") as fh:
        fh.write(json.dumps(row) + chr(10))
    s.log("freerun", row)
    s.m.call("pause")
    return row


def proof(s):
    s.m.call("pause")
    s.set([])
    for tag, dbg in (("N", 1), ("S", 2), ("N2", 1)):
        leg(s, tag, dbg)
    if os.environ.get("PROOF_FREERUN"):   # skin (dbg 0), native (1), skin, native: alternating, same session
        secs = float(os.environ["PROOF_FREERUN"])
        for tag, dbg in (("free_native_a", 1), ("free_skin_a", 0), ("free_native_b", 1), ("free_skin_b", 0)):
            freerun(s, tag, dbg, secs)
        s.m.call("memory_write", address=hex(s.syms["wv_nat_dbg"]), size="byte", value=hex(1))
        s.m.call("framebuffer_screenshot", path=OUT + "/after_freerun.png")
    s.stop()


def step(v, s):
    now = time.time()
    if not st["titled"]:
        st["titled"] = True
        try:
            ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), TITLE)
        except Exception as e:   # the title is a label for the owner's desk, not part of the proof
            s.log("retitle failed", e)
    a = s.ram(0x8000, 0x400)
    if st["started"]:
        return
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
    if a[0x384:0x387].hex() != "020000":   # wait for him to stand free
        return
    st["started"] = True
    proof(s)
