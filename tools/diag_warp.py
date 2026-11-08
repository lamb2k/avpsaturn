# play_yaba script, DIAGNOSTIC (one live write: sat_warp before the start; -DSAT_WARP -DSAT_READMAP build): starts the game at stage word WARP (hex),
# then the readmap bot (diag_readmap.py) as usual. Writes RUN/readmap.json.
import importlib.util, os
spec = importlib.util.spec_from_file_location("rm", r"E:\AvP\learning\lane-all\tools\diag_readmap.py")
rm = importlib.util.module_from_spec(spec); spec.loader.exec_module(rm)
done = False
def step(v, s):
    global done
    if not done:
        done = True
        s.m.call("memory_write", address=hex(s.syms["sat_warp"]), bytes="%08x" % int(os.environ["WARP"], 16))
        s.log("warp", os.environ["WARP"], s.m.read(s.syms["sat_warp"], 4).hex())
    rm.step(v, s)
fatal = rm.fatal
end = getattr(rm, "end", None)
