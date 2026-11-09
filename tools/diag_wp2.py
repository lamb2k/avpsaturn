# play_yaba script, DIAGNOSTIC (lane all, 11-08): diag_wp.py plus an execute breakpoint on f_5526a (the alien grab) and a seeded bot (SEED).
# A stop at f_5526a counts a grab and resumes; a stop with value 0x4a9 written to the player record +0x1c/+0x1e is a WPHIT (the bug).
import importlib.util, os, random, time as _t
random.seed(int(os.environ.get("SEED", "1")))
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
REC = int(os.environ.get("REC", "0x8380"), 16); armed = False; hits = 0; grabs = 0; ADDRS = []; TBL = []; tblhits = 0; GRAB = None; last_grab_log = 0; x0 = None
def step(v, s):
    global armed, hits, grabs, GRAB, last_grab_log, tblhits
    if not armed:
        armed = True
        s.log("hist", str(s.m.call("set_debug_option", **({"history": "on"} if os.environ.get("WP_HIST") else {}), cpu_core="interpreter"))[:100])
        for off in (0x1c, 0x1e):
            a = hex(s.syms["RAMB"] + REC + off); ADDRS.append(a)
            s.log("bp", a, str(s.m.call("breakpoint_add", cpu="master", type="memory", address=a, read=False, write=True, value=os.environ.get("WPV", "0x4a9")))[:120])
        for k in range(4):   # the per-character table the grab reads at 0x562e6 (ROM view address 0x56632 + 4 per character)
            a = hex(0x2400000 + 0x56632 + 4 * k); TBL.append(a.upper().replace("0X", "0x"))
            s.log("bp table", a, str(s.m.call("breakpoint_add", cpu="master", type="memory", address=a, read=True, write=False))[:100])
        GRAB = s.syms.get("f_5526a")
        if GRAB:
            s.log("bp grab", hex(GRAB), str(s.m.call("breakpoint_add", cpu="master", address=hex(GRAB)))[:120])
        else:
            s.log("no f_5526a symbol")
    t1 = _t.time()
    while _t.time() - t1 < 0.045:
        st = str(s.m.call("wait_for_stop", timeout_ms=5))
        if "stopped: true" not in st:
            continue
        ds = str(s.m.call("debug_status"))
        x = int.from_bytes(s.ram(REC + 0x1c, 4), "big")
        if (x >> 16) != 0x4a9 and (x & 0xffff) != 0x4a9 and not (GRAB and hex(GRAB)[2:].lower() in ds.lower()):   # the value filter makes a 4a9 write the only other stop
            tblhits += 1   # stop at a table read (memory read breakpoint): the stop reason names the instruction, not the address
            if tblhits <= 6:
                s.log("TABLE READ n", tblhits, "rec+1c", hex(x), "rec+d2", s.ram(REC + 0xd2, 1).hex(), " ".join(ds[:170].split()))
            s.m.call("resume"); continue
        if GRAB and hex(GRAB)[2:].lower() in ds.lower() and x >> 16 != 0x4a9 and (x & 0xffff) != 0x4a9:
            grabs += 1
            if grabs <= 3: s.log("GRAB f_5526a n", grabs, "rec+1c", hex(x), ds[:160].replace("\n", " "))
            if grabs == 1:
                s.log("grab bp removed", str(s.m.call("breakpoint_remove", cpu="master", address=hex(GRAB)))[:80])
            s.m.call("resume"); continue
        hits += 1
        s.log("WPHIT", hex(x), ds[:600])
        for t, kw in (("registers_get", dict(cpu="master")), ("exec_history", dict(cpu="master", count=200, with_registers=True))):
            try: s.log(t, str(s.m.call(t, **kw))[:30000])
            except Exception as e: s.log(t, "err", e)
        s.m.call("resume")
    if v - last_grab_log > 300:
        last_grab_log = v
        s.log("progress grabs", grabs, "hits", hits, "rec+1c", s.ram(REC + 0x1c, 4).hex())
        if os.environ.get("CLS"):
            live = []
            for base, cnt, z in ((0x8680, 24, 0x80), (0x9280, 4, 0xc0), (0x9580, 20, 0xc0)):
                blk = s.ram(base, cnt * z)
                live += [(hex(base + k * z), blk[k * z + 2], blk[k * z + 6], blk[k * z + 7]) for k in range(cnt) if blk[k * z]]
            s.log("enemies (addr class st6 st7)", live[:24])
    bot.step(v, s)
    if os.environ.get("PASSIVE") and v > 1500 and int.from_bytes(s.ram(0x83c0, 2), "big") not in (0, 0xffff) and s.ram(0x8380, 1)[0] == 1:
        s.set([])   # stand still and let the section come: the ceiling aliens drop on a player who is not moving on
    if os.environ.get("STAND") and v > 1500 and int.from_bytes(s.ram(0x83c0, 2), "big") not in (0, 0xffff) and s.ram(0x8380, 1)[0] == 1:
        # walk to screen x STAND (under the ceiling aliens) and stand there, no shooting
        sx = int.from_bytes(s.ram(REC + 0x10, 2), "big") - int.from_bytes(s.ram(0x278, 2), "big")
        tgt = int(os.environ["STAND"])
        s.set(["right"] if sx < tgt - 12 else (["left"] if sx > tgt + 12 else []))
    if os.environ.get("ANCHOR"):   # stay at the first spot: a section that is not cleared keeps its ceiling aliens coming (the old diag_l3 run sat there for 11,000 vblanks)
        global x0
        px = int.from_bytes(s.ram(REC + 0x10, 2), "big")
        if x0 is None and v > 1500: x0 = px
        if x0 is not None and px > x0 + int(os.environ.get("ANCHOR")):
            s.set(["left"] + (["c"] if v % 4 == 0 else []))
fatal = bot.fatal
def end(s):
    s.log("SUMMARY table reads", tblhits, "grabs", grabs, "wphits", hits, "rec+1c", s.ram(REC + 0x1c, 4).hex())
    e = getattr(bot, "end", None)
    if e: e(s)
