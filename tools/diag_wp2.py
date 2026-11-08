# play_yaba script, DIAGNOSTIC (lane all, 11-08): diag_wp.py plus an execute breakpoint on f_5526a (the alien grab) and a seeded bot (SEED).
# A stop at f_5526a counts a grab and resumes; a stop with value 0x4a9 written to the player record +0x1c/+0x1e is a WPHIT (the bug).
import importlib.util, os, random, time as _t
random.seed(int(os.environ.get("SEED", "1")))
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
REC = int(os.environ.get("REC", "0x8380"), 16); armed = False; hits = 0; grabs = 0; ADDRS = []; GRAB = None; last_grab_log = 0
def step(v, s):
    global armed, hits, grabs, GRAB, last_grab_log
    if not armed:
        armed = True
        s.log("hist", str(s.m.call("set_debug_option", **({"history": "on"} if os.environ.get("WP_HIST") else {}), cpu_core="interpreter"))[:100])
        for off in (0x1c, 0x1e):
            a = hex(s.syms["RAMB"] + REC + off); ADDRS.append(a)
            s.log("bp", a, str(s.m.call("breakpoint_add", cpu="master", type="memory", address=a, read=False, write=True, value=os.environ.get("WPV", "0x4a9")))[:120])
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
    bot.step(v, s)
fatal = bot.fatal
def end(s):
    s.log("SUMMARY grabs", grabs, "wphits", hits, "rec+1c", s.ram(REC + 0x1c, 4).hex())
    e = getattr(bot, "end", None)
    if e: e(s)
