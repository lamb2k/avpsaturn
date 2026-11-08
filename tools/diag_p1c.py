# play_yaba script, DIAGNOSTIC (reads only): bot as usual; every step reads the player record REC (default ff8380) and logs each change of +0x1c and +0x00..0x20 head.
import importlib.util, os
spec = importlib.util.spec_from_file_location("bot", r"E:\AvP\worktrees\lane-all\saturn\rt\play_full_bot.py")
bot = importlib.util.module_from_spec(spec); spec.loader.exec_module(bot)
REC = int(os.environ.get("REC", "0x8380"), 16); last = None
def step(v, s):
    global last
    try:
        r = s.ram(REC, 0x40)
        if r[0x1c:0x20] != (last or b"")[0x1c:0x20]:
            s.log("P1C", hex(int.from_bytes(r[0x1c:0x20], "big")), r.hex())
        last = r
    except Exception as e:
        s.log("p1c", e)
    bot.step(v, s)
fatal = bot.fatal
end = getattr(bot, "end", None)
