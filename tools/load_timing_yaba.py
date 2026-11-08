# Load timing + cart page check wrapper (EMULATOR). INNER = a play script (lane-home k1.py / d4.py / br.py); its step runs unchanged.
# Load start: the first poll where the kernel's vblank count stops (round_check masks interrupts for load_round). Load end: sat_rounds.loads
# increments (right after sat_gfx_display(1), the stage picture back on). Both stamped with Yaba's emulated frame count (framebuffer_screenshot).
# At each load end the cart is dumped and every region of that round file (ROM restores, tile pack, sprite spills) compared with the file's bytes.
import importlib.util, os, re, struct, time, json, pathlib
spec = importlib.util.spec_from_file_location("inner", os.environ["INNER"]); inner = importlib.util.module_from_spec(spec); spec.loader.exec_module(inner)
ROUNDS = pathlib.Path(os.environ.get("ROUNDS_DIR", "E:/AvP/learning/lane-disc/rounds_ref"))
TAG = os.environ.get("TAG", "x"); MAXLOADS = int(os.environ.get("MAXLOADS", "99"))
st = dict(lastv=None, lastt=0, start=None, loads=None, events=[])
def frame(s, name):
    r = s.m.call("framebuffer_screenshot", path=str(s.work / "shots" / f"{TAG}_{name}.png"))
    m = re.search(r'"?frame(?:_count|s)?"?\s*[:=]\s*(\d+)', r)
    return int(m.group(1)) if m else -1, r[:200]
def cart_check(s, file):
    b = (ROUNDS / f"R{file:03d}.BIN").read_bytes(); n = struct.unpack_from(">I", b)[0]; at = 2048; res = []
    packs = 0
    for i in range(n):
        d, z = struct.unpack_from(">II", b, 4 + 8 * i)
        if d == 1: continue
        packs += d == 0x02654000
        body = b[at:at + z]; at += z
        if packs < 2 and d == 0x02654000: continue   # sound set: SCSP takes it, the tile pack then overwrites it
        got = b"".join(bytes(s.m.read(d + o, min(0x8000, z - o))) for o in range(0, z, 0x8000))
        bad = sum(got[k:k + 2048] != body[k:k + 2048] for k in range(0, z, 2048))
        res.append((hex(d), z // 2048, bad))
    return res
def step(v, s):
    now = time.time(); loads = s.word("sat_rounds", 4)
    if st["loads"] is None: st["loads"] = loads
    if st["start"] is None and v > 0 and st["lastv"] == v and now - st["lastt"] > 0.12 and loads == st["loads"]:
        st["start"] = frame(s, f"ld{loads}_start"); st["sv"] = v; s.log("LOAD START frame", st["start"][0], "vblank", v)
    if v != st["lastv"]: st["lastv"] = v; st["lastt"] = now
    if loads != st["loads"]:
        end = frame(s, f"ld{loads}_end"); file = s.word("sat_rounds", 0); secs = s.word("sat_rounds", 8)
        cc = cart_check(s, file)
        ev = dict(load=loads, file=file, sectors=secs, start=st["start"][0] if st["start"] else None, end=end[0],
                  frames=(end[0] - st["start"][0]) if st["start"] else None, cart=cc, cart_bad=sum(x[2] for x in cc), stw=hex(s.ram16(0x81e8)))
        st["events"].append(ev); s.log("LOAD", json.dumps(ev)); st["loads"] = loads; st["start"] = None
        if len(st["events"]) >= MAXLOADS: s.log("MAXLOADS"); s.stop(); return
    inner.step(v, s)
def end(s):
    s.log("SUMMARY", json.dumps([{k: e[k] for k in ("load", "file", "sectors", "frames", "cart_bad", "stw")} for e in st["events"]]))
def fatal(s, f, d): s.log("FATAL in", TAG, hex(f), hex(d))
