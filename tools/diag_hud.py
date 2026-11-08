# play_yaba script (reads only): bot as usual; every 2 s reads the CPS2 object list (SAT_OBJ) and logs, for entries with attr 0x80 and without,
# the block positions (x, y in board coordinates, block size). Writes RUN/hud_objs.json. Shots at 20 s, 40 s, 60 s.
import importlib.util, json, time
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
t0 = time.time(); last = 0; shots = set(); acc = {"hud": {}, "world": {}, "samples": 0}
def sample(s):
    d = s.m.read(s.syms["SAT_OBJ"], 0x2000)
    for i in range(0, len(d), 8):
        xw, yw, cw, aw = (int.from_bytes(d[i + k:i + k + 2], "big") for k in (0, 2, 4, 6))
        if aw & 0xff00 == 0xff00:
            break
        k = "%d,%d,%dx%d,%x" % (xw & 0x3ff, yw & 0x3ff, ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1, aw & 0xff)
        g = acc["hud" if aw & 0x80 else "world"]; g[k] = g.get(k, 0) + 1
    acc["samples"] += 1
    acc.setdefault("missing", []).append([s.v, int.from_bytes(s.m.read(s.syms["sat_gfx_stats"] + 32, 4), "big")])
    (s.work / "hud_objs.json").write_text(json.dumps(acc))
def step(v, s):
    global last
    if time.time() - last > 2 and v > 1500:
        last = time.time()
        try: sample(s)
        except Exception as e: s.log("hud", e)
    for t in (20, 40, 60, 80):
        if time.time() - t0 > t + 60 and t not in shots:
            shots.add(t); s.shot("hud%d" % t)
    bot.step(v, s)
fatal = bot.fatal
end = bot.end
