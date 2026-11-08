# play_yaba script, DIAGNOSTIC (lane all, 11-08): from a loaded state (no warp), AFTER_V vblanks later compare the ROM view (0x2400000 + address) with ROM.BIN for the const pages and the control pages. RAM only read.
import importlib.util, os, json
spec = importlib.util.spec_from_file_location("rc", r"E:\AvP\learning\lane-all\tools\diag_romcheck.py")
os.environ.setdefault("WARP", "0x0c")
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
start = None
def step(v, s):
    global start
    if start is None: start = v
    rc.bot.step(v, s)
    if v - start >= int(os.environ.get("AFTER_V", "700")):
        bad_cp = rc.check(s, rc.CP); ctrl = rc.check(s, set(range(0, 2048, 7)) - rc.CPALL)
        res = dict(vblank=v, rounds=rc.bot.rounds(s), const636_pages=len(rc.CP), const636_mismatch=len(bad_cp), const636_bad=bad_cp[:80], page_159_bad=0x159 in bad_cp, control_mismatch=len(ctrl))
        s.log("ROMCHECK", json.dumps(res)); open(s.work / "romcheck.json", "w").write(json.dumps(res)); s.stop()
fatal = rc.bot.fatal
