# play_yaba script, DIAGNOSTIC (lane all, 11-08): on a -DSAT_WARP image, warp to stage word WARP, let the bot run until the stage's round file has loaded (stage word = WARP and the loader counter moved), 400 vblanks more,
# then compare the lifted code's ROM view (ROMB = 0x2400000 + address, what PB() reads) with ROM.BIN for the const pages (CP json), the extra pages of the all-immediates list (CPALL json), and every other page.
# Writes RUN/romcheck.json and stops. RAM only read, after the one sat_warp write (as tools/diag_warp.py).
import importlib.util, os, json
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
ROM = open(os.environ["ROM_BIN"], "rb").read()
CP = set(json.load(open(os.environ["CP"]))); CPALL = set(json.load(open(os.environ["CPALL"])))
WARP = int(os.environ["WARP"], 16); done = False; r0 = None; at = None
def runs(pages):
    out = []; ps = sorted(pages)
    for p in ps:
        if out and out[-1][1] == p - 1 and p - out[-1][0] < 3: out[-1][1] = p
        else: out.append([p, p])
    return out
def check(s, pages):
    bad = []
    for a, b in runs(pages):
        n = (b - a + 1) * 1024
        got = s.m.read(0x2400000 + a * 1024, n)
        for p in range(a, b + 1):
            o = (p - a) * 1024
            if got[o:o + 1024] != ROM[p * 1024:(p + 1) * 1024]: bad.append(p)
    return bad
def step(v, s):
    global done, r0, at
    if not done and v > 300:
        done = True
        s.m.call("memory_write", address=hex(s.syms["sat_warp"]), bytes="%08x" % WARP)
        s.log("warp", hex(WARP))
    bot.step(v, s)
    if bot.stage == WARP and at is None:
        at = v; r0 = bot.rounds(s)[1]
    if at is not None and bot.rounds(s)[1] != r0 and not hasattr(step, "t"):
        step.t = v
    if hasattr(step, "t") and v - step.t >= 400:
        rem = set(range(2048))
        bad_cp = check(s, CP); bad_all = check(s, CPALL - CP); ctrl = check(s, set(range(0, 2048, 7)) - CPALL)
        res = dict(stage=hex(WARP), vblank=v, rounds=bot.rounds(s), const636_pages=len(CP), const636_mismatch=len(bad_cp), const636_bad=bad_cp[:50],
                   extra_all_pages=len(CPALL - CP), extra_all_mismatch=len(bad_all), extra_all_bad=bad_all[:50], control_pages=len(set(range(0, 2048, 7)) - CPALL), control_mismatch=len(ctrl))
        s.log("ROMCHECK", json.dumps(res)); open(s.work / "romcheck.json", "w").write(json.dumps(res)); s.stop()
fatal = bot.fatal
end = getattr(bot, "end", None)
