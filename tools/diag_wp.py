# play_yaba script, DIAGNOSTIC (debugger watchpoints, no memory writes): bot as usual; a write watchpoint on player record +0x1c/+0x1e for value WPV;
# on a hit logs SH-2 registers, backtrace, disassembly and the 68000 registers, then resumes.
import importlib.util, os
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
REC = int(os.environ.get("REC", "0x8380"), 16); armed = False; hits = 0
ADDRS = []
def step(v, s):
    global armed, hits
    if not armed:
        armed = True
        s.log("hist", str(s.m.call("set_debug_option", history="on", cpu_core="interpreter"))[:100])
        for off, val in ((0x1c, os.environ.get("WPV", "0x4a9")), (0x1e, os.environ.get("WPV", "0x4a9"))):
            a = hex(s.syms["RAMB"] + REC + off); ADDRS.append(a)
            s.log("bp", a, str(s.m.call("breakpoint_add", cpu="master", type="memory", address=a, read=False, write=True, value=val))[:120])
    import time as _t
    t1 = _t.time()
    while _t.time() - t1 < 0.045:
        st = str(s.m.call("wait_for_stop", timeout_ms=5))
        if "stopped: true" not in st:
            continue
        x = int.from_bytes(s.ram(REC + 0x1c, 4), "big")
        if False:
            s.m.call("resume"); continue
        hits += 1
        s.log("WPHIT", hex(x), str(s.m.call("debug_status"))[:600])
        for t, kw in (("registers_get", dict(cpu="master")), ("exec_history", dict(cpu="master", count=400, with_registers=True))):
            try: s.log(t, str(s.m.call(t, **kw))[:60000])
            except Exception as e: s.log(t, "err", e)
        cb = s.m.read(s.syms["sat_cpu"], 64)
        s.log("68k", [hex(int.from_bytes(cb[i:i + 4], "big")) for i in range(0, 64, 4)], "rec", s.ram(REC, 0x40).hex())
        s.m.call("resume")
        if hits > 6:
            for a in ADDRS: s.m.call("breakpoint_remove", cpu="master", type="memory", address=a)
    bot.step(v, s)
fatal = bot.fatal
end = getattr(bot, "end", None)
