#!/usr/bin/env python3
"""Run tools/vdp2_cycle_check.py's rules over a VDP2 register-write trace of a real run (the register log of the patched strict Ymir, E:/AvP/learning/lane-hwboot/ymir_regs.log:
`seq WHO PC=pc W16 25F800xx value`). The state is rebuilt from the writes and judged at the end of every burst of consecutive VDP2 register writes while the display is on and
a layer is enabled, so register writers the static scan cannot see (computed values, other files, a mode that rewrites the cycles) are caught in the actual play-through.
This is a regression test for the access cycle rules, NOT a model of what the console does when a rule is broken: nothing is known about that except the owner's photos.
usage: vdp2_trace_check.py LOG [--layout old|new] [--limit N]   (old = the fix5/fix6 memory layout, new = fix7's, none = another program: cell banks taken from its cell reads; exit 1 when any state breaks a rule)"""
import argparse, importlib.util, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("chk", HERE / "vdp2_cycle_check.py")
chk = importlib.util.module_from_spec(spec); spec.loader.exec_module(chk)

ONLY = ""
CYC = (0x10, 0x12, 0x14, 0x16, 0x18, 0x1a, 0x1c, 0x1e)


def judge(regs, old, cfg_text, layout="new"):
    cfg = chk.parse_cfg_text(chk.fit_filtered_macros(cfg_text, 1))
    g = lambda o: regs.get(o, 0)
    cfg.update({"SAT_V2_CHCTLA": str(g(0x28)), "SAT_V2_CHCTLB": str(g(0x2a)), "SAT_V2_PLSZ": str(g(0x3a)),
                "SAT_V2_PNC0": str(g(0x30)), "SAT_V2_PNC1": str(g(0x32)), "SAT_V2_PNC2": str(g(0x34)), "SAT_V2_PNC3": str(g(0x36)),
                "SAT_V2_MPAB0": str(g(0x40)), "SAT_V2_MPCD0": str(g(0x42)), "SAT_V2_MPAB1": str(g(0x44)), "SAT_V2_MPCD1": str(g(0x46)),
                "SAT_V2_MPAB2": str(g(0x48)), "SAT_V2_MPCD2": str(g(0x4a)), "SAT_V2_MPAB3": str(g(0x4c)), "SAT_V2_MPCD3": str(g(0x4e))})
    layers = chk.layer_model(cfg, g(0x98), old)
    codes = chk.words_to_codes([g(o) for o in CYC])
    if layout == "none":   # another program (SGL reference, Brooklyn Bangout): cell locations unknown, take the banks where the layer has cell reads
        for n, L in enumerate(layers):
            L["cells"] = [(chk.BANK_BASE[b], chk.BANK_BASE[b] + 0x20000) for b in chk.BANKS if any(c == n + 4 for c in codes[b])] or [(0, 1)]
    enabled = {n for n in range(4) if g(0x20) >> n & 1}
    errs, warns, info = [], [], []
    chk.check(codes, layers, enabled, g(0x0e), "state", errs, warns, info)
    if ONLY:
        errs = [e for e in errs if ONLY in e]
    return errs, warns, enabled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log"); ap.add_argument("--layout", default="new"); ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--only", default="", help="judge only the rules whose message contains this text (e.g. CPU for the split-bank CPU slot rule)")
    a = ap.parse_args()
    global ONLY
    ONLY = a.only
    cfg_text = (HERE.parent / "saturn" / "gfx" / "sat_vdp2_cfg.h").read_text(encoding="utf-8")
    regs, prev_burst, states, bursts = {}, False, {}, 0
    old = a.layout == "old"
    def eval_now():
        nonlocal bursts
        if not (regs.get(0x00, 0) & 0x8000) or not (regs.get(0x20, 0) & 0xf):
            return
        key = tuple(regs.get(o, 0) for o in CYC + (0x0e, 0x20, 0x28, 0x2a, 0x30, 0x32, 0x34, 0x36, 0x3a, 0x40, 0x42, 0x44, 0x46, 0x48, 0x4a, 0x4c, 0x4e, 0x98))
        bursts += 1
        if key in states:
            states[key][2] += 1
            return
        errs, warns, enabled = judge(regs, old, cfg_text, a.layout)
        states[key] = [errs, warns, 1, dict(regs)]
    rx = re.compile(r"^\d+ \S+ PC=\S+ W16 25F80([0-9A-F]{3}) ([0-9A-F]+)$")
    with open(a.log, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = rx.match(line.strip())
            if m:
                regs[int(m.group(1), 16)] = int(m.group(2), 16)
                prev_burst = True
            else:
                if prev_burst:
                    eval_now()
                prev_burst = False
    bad = [(k, v) for k, v in states.items() if v[0]]
    print(f"{bursts} register bursts judged with the display on, {len(states)} distinct states, {len(bad)} break a rule")
    for k, v in sorted(states.items(), key=lambda kv: -kv[1][2])[:a.limit]:
        r = v[3]
        print(f"  x{v[2]:<6} cycles {' '.join('%04x' % r.get(o, 0) for o in CYC)}  ZMCTL {r.get(0x98, 0):04x}  BGON {r.get(0x20, 0):02x}  -> " + ("FAIL: " + v[0][0] if v[0] else "ok"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
