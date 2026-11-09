# play_yaba script, DIAGNOSTIC (lane all, 11-08): from boot on a -DSAT_WARP image, warp to stage word WARP (hex), run the whole-game bot, save slot 3 the first time stage 0xc reaches section 6
# (the state diag_l3 was started from, vblanks advancing), copy it to OUT_STATE and stop. One live write: sat_warp, as tools/diag_warp.py.
import importlib.util, os, shutil
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
done = False; saved = False
def step(v, s):
    global done, saved
    if not done and v > 300:
        done = True
        s.m.call("memory_write", address=hex(s.syms["sat_warp"]), bytes="%08x" % int(os.environ["WARP"], 16))
        s.log("warp", os.environ["WARP"], s.m.read(s.syms["sat_warp"], 4).hex())
    bot.step(v, s)
    if not saved and bot.stage == 0xc and bot.sec == 6 and v > 1000:
        saved = True
        s.log("mkstate", bot.safe_save(s, 3), "v", v)
        shutil.copy(os.environ.get("SAVES", "E:/AvP/learning/lane-all/yaba7/saves") + "/_003.yss", os.environ["OUT_STATE"])
        s.log("state copied to", os.environ["OUT_STATE"])
        s.stop()
fatal = bot.fatal
end = getattr(bot, "end", None)
