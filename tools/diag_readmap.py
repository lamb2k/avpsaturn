# play_yaba script, DIAGNOSTIC build only (-DSAT_READMAP): the bot as usual; every 2 s reads sat_readmap (pages of the program ROM the lifted code read
# since the last stage file load) and ORs it under the loaded file's index. Writes RUN/readmap.json: {file index: [pages]}. No memory writes.
import importlib.util, json, time
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
last = 0
acc = {}


def sample(s):
    f = bot.rounds(s)[0]
    m = s.m.read(s.syms["sat_readmap"], 256)
    pages = acc.setdefault(str(f), set())
    for i, b in enumerate(m):
        for k in range(8):
            if b >> k & 1:
                pages.add(i * 8 + k)
    p = s.work / "readmap.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    for k, v in acc.items():
        old[k] = sorted(set(old.get(k, [])) | v)
    p.write_text(json.dumps(old))


def step(v, s):
    global last
    if time.time() - last > 2:
        last = time.time()
        try:
            sample(s)
        except Exception as e:
            s.log("readmap", e)
    bot.step(v, s)


def fatal(s, c, d):
    sample(s)
    bot.fatal(s, c, d)


def end(s):
    sample(s)
    bot.end(s)
