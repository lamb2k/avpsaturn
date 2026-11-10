# Versus (Duel) matrix driver: play_smash.py's bot plus arena choice, pair choice and paused burst captures.
# env: ARENA=0e|1c|1e|24 (pokes sat_duel_force_arena at the duel menu), P1CHAR / P2CHAR = warrior|schaefer|linn|hunter|wolverine
#      (wolverine is Schaefer's slot: GUEST=1, the default of the owner recipe; GUEST=0 gives the four stock characters), PLAIN=1 (test build) runs the plain stage file instead of the duel copy, SNAPS=20,45 (game seconds from the fight start, paused burst of BURST frames each),
#      plus everything play_smash.py reads (FIGHT, ALIENS, MENU ...).
import os, time, importlib.util, pathlib
HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("play_smash", str(HERE / "play_smash.py"))
ps = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ps)
GRID = {"warrior": (0, 0), "schaefer": (0, 1), "wolverine": (0, 1), "linn": (1, 0), "hunter": (1, 1)}
def moves(frm, to):
    (r0, c0), (r1, c1) = GRID[frm], GRID[to]
    out = []   # vertical first: a cursor does not step onto the cell the other player's cursor holds (Schaefer to Linn by left, down landed on Hunter)
    if r1 > r0: out += ["down"]
    if r1 < r0: out += ["up"]
    if c1 > c0: out += ["right"]
    if c1 < c0: out += ["left"]
    return ",".join(out)
if os.environ.get("P1CHAR"): os.environ["P1MOVE"] = moves("warrior", os.environ["P1CHAR"])
if os.environ.get("P2CHAR"): os.environ["P2MOVE"] = moves("schaefer", os.environ["P2CHAR"])
poked = 0; snapped = set(); v0 = None
def step(v, s):
    global poked
    sc = s.word("sat_home_screen")
    if sc in (1, 8) and not getattr(s, "guest_set", 0) and os.environ.get("GUEST") is not None and "sat_guest_sel" in s.syms:   # bonus characters setting: 0 off (the four stock characters), 1 Wolverine in Schaefer's slot
        s.guest_set = 1
        s.m.call("memory_write", address=hex(s.syms["sat_guest_sel"]), bytes="%02x" % int(os.environ["GUEST"])); s.log("GUEST poked", os.environ["GUEST"])
    if sc == 8 and not getattr(s, "plain_set", 0) and os.environ.get("PLAIN") and "sat_duel_plain" in s.syms:
        s.plain_set = 1
        s.m.call("memory_write", address=hex(s.syms["sat_duel_plain"]), bytes="01"); s.log("PLAIN file poked")
    sym = next((n for n in ("sat_duel_force_arena", "sat_duel_test_stage") if n in s.syms), None)   # the second name: the first test builds
    if sc == 8 and not poked and os.environ.get("ARENA") and sym:
        poked = 1
        s.m.call("memory_write", address=hex(s.syms[sym]), bytes="%02x" % int(os.environ["ARENA"], 16))
        s.log("ARENA poked", os.environ["ARENA"])
    t0 = getattr(ps, "t0", None)
    global v0
    if t0 and v0 is None: v0 = v
    if t0 and os.environ.get("SNAPS"):
        el = (v - v0) / 60.0   # game seconds since the fight began (the emulator runs slower than real time under load)
        for i, t in enumerate(float(x) for x in os.environ["SNAPS"].split(",")):
            if el >= t and i not in snapped:
                snapped.add(i)
                s.set([])
                s.m.call("pause")
                d = s.work / "shots" / ("burst_%02d" % i)
                d.mkdir(parents=True, exist_ok=True)
                r = s.m.call("framebuffer_burst", directory=str(d), frames=int(os.environ.get("BURST", "3")), prefix="f")
                s.m.call("resume")
                s.log("BURST", i, "at", round(el), "->", str(d).replace("\\", "/"), "stage", s.ram(0x81e8, 2).hex(), "chars", s.ram(0x8380 + 0xd2, 1).hex(), s.ram(0x8480 + 0xd2, 1).hex())
    if t0 and os.environ.get("SCANAT") and (v - v0) / 60.0 >= float(os.environ["SCANAT"]) and ("scan", 0) not in snapped:   # records whose x word (+0x10) lies right of the camera: who is the figure at the screen edge
        snapped.add(("scan", 0))
        cam = int.from_bytes(s.ram(0x8278, 2), "big"); M = s.ram(0x8380, 0x7c80)
        out = []
        for o in range(0, len(M) - 0x40, 0x20):
            x = int.from_bytes(M[o + 0x10:o + 0x12], "big"); y = int.from_bytes(M[o + 0x14:o + 0x16], "big")
            if M[o] and cam - 60 <= x <= cam + 460: out.append("%x:%s x%d y%d" % (0x8380 + o, M[o:o + 12].hex(), x, y))
        s.log("SCAN cam", cam, len(out), " | ".join(out[:60]))
        P = s.ram(0x8380, 0x300)
        for j in range(3): s.log("PLAYER", j, "act", P[j * 0x100 + 4:j * 0x100 + 8].hex(), "d2", P[j * 0x100 + 0xd2], "x", int.from_bytes(P[j * 0x100 + 0x10:j * 0x100 + 0x12], "big"), "y", int.from_bytes(P[j * 0x100 + 0x14:j * 0x100 + 0x16], "big"), "rec", P[j * 0x100:j * 0x100 + 16].hex())
        C = s.ram(0xce80, 0x800)
        s.log("CTLPOOL", " | ".join("%x:%s/%s" % (0xce80 + o, C[o:o + 8].hex(), C[o + 0x40:o + 0x50].hex()) for o in range(0, 0x800, 0x40) if C[o]))
    if t0 and os.environ.get("RINGOUT"):   # RINGOUT=15,35: at those game seconds P2 is thrown 420 px sideways (a ring-out, the effect that showed the noise in the earlier lane's stills)
        for t in (float(x) for x in os.environ["RINGOUT"].split(",")):
            if (v - v0) / 60.0 >= t and ("ro", t) not in snapped:
                snapped.add(("ro", t))
                x = s.ram(0x8490, 2); nx = (int.from_bytes(x, "big") + 420) & 0xffff
                s.m.call("memory_write", address=hex(s.syms["RAMB"] + 0x8490), bytes="%04x" % nx); s.log("RINGOUT poke P2 x", int.from_bytes(x, "big"), "->", nx)
    if t0 and os.environ.get("GFIGHT") and (v - v0) / 60.0 > float(os.environ["GFIGHT"]):
        s.shot("duel_end"); s.log("END game s", round((v - v0) / 60.0)); s.stop(); return
    ps.step(v, s)
    if t0 and getattr(ps, "n", 0) % 120 == 11 and "sat_home_mode" in s.syms:
        s.log("HOME mode", s.word("sat_home_mode"), "hold", s.word("sat_home_hold"), "screen", s.word("sat_home_screen"), "loads", s.word("sat_rounds", 4), "file", s.word("sat_rounds"))
    if t0 and os.environ.get("EDUMP") and getattr(ps, "n", 0) % 40 == 7:   # live bodies of the enemy pools: tag 12 (0xff9580 x20, 0xc0), tag 20 (0xffae80 x16, 0x80)
        A = s.ram(0x9580, 20 * 0xc0); B = s.ram(0xae80, 16 * 0x80)
        e12 = ["%d:c%02x/t%02x/x%d/hp%d" % (i, A[i*0xc0+2], A[i*0xc0+8], int.from_bytes(A[i*0xc0+16:i*0xc0+18], "big"), int.from_bytes(A[i*0xc0+0x40:i*0xc0+0x42], "big")) for i in range(20) if A[i*0xc0:i*0xc0+4] != bytes(4)]
        e20 = ["%d:c%02x/t%02x/x%d/hp%d" % (i, B[i*0x80+2], B[i*0x80+8], int.from_bytes(B[i*0x80+16:i*0x80+18], "big"), int.from_bytes(B[i*0x80+0x40:i*0x80+0x42], "big")) for i in range(16) if B[i*0x80:i*0x80+4] != bytes(4)]
        s.log("ENEMY t12", " ".join(e12), "| t20", " ".join(e20), "| kills", s.ram(0x9a1a, 2).hex(), "spawner", s.ram(0x1816, 1).hex(), "ctl", s.word("sat_stage_ctl"))
def fatal(s, code, det): s.log("FATAL seen", hex(code), hex(det)); s.shot("fatal")
