# play_yaba script, DIAGNOSTIC (debugger only, no memory writes): interpreter core; write watchpoints (no value filter) on player record +0x1c and +0x1e;
# every hit logs the new +0x1c, SH-2 PC and PR, then resumes. Bot as usual.
import importlib.util, os, re, time
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
REC = int(os.environ.get("REC", "0x8380"), 16); armed = False
def step(v, s):
    global armed
    if not armed:
        armed = True
        s.log("core", str(s.m.call("set_debug_option", history="on", cpu_core="interpreter"))[:100])
        for off in (0x1c, 0x1e):
            a = hex(s.syms["RAMB"] + REC + off)
            s.log("bp", a, str(s.m.call("breakpoint_add", cpu="master", type="memory", address=a, read=False, write=True))[:80])
    t1 = time.time()
    while time.time() - t1 < 0.045:
        st = str(s.m.call("wait_for_stop", timeout_ms=5))
        if "stopped: true" not in st:
            continue
        x = int.from_bytes(s.ram(REC + 0x1c, 4), "big")
        r = str(s.m.call("registers_get", cpu="master"))
        pc = re.search(r"PC=(0x[0-9A-F]+)", r); pr = re.search(r"PR=(0x[0-9A-F]+)", r)
        s.log("W", hex(x), pc and pc[1], pr and pr[1])
        if not (0x100000 <= x < 0x200000) and x:
            s.log("BAD", r.replace("\n", " | "))
            try: s.log("HIST", str(s.m.call("exec_history", cpu="master", count=200, with_registers=True)).replace("\n", " | ")[:40000])
            except Exception as e: s.log("hist err", e)
        s.m.call("resume")
    bot.step(v, s)
fatal = bot.fatal
end = bot.end
