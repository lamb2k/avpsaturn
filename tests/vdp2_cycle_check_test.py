#!/usr/bin/env python3
"""Tests for tools/vdp2_cycle_check.py: the word sets that ran on the console (F5, fix6) must FAIL, the manual-conformant set must PASS, and the checker's tables must equal the
independent ones in Ymir's source. usage: python tests/vdp2_cycle_check_test.py [YMIR_ROOT]"""
import importlib.util, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("chk", ROOT / "tools" / "vdp2_cycle_check.py")
chk = importlib.util.module_from_spec(spec); spec.loader.exec_module(chk)

F5 = [0x0123, 0xff67, 0x4444, 0x4444, 0x5555, 0x5555, 0x5555, 0x5555]       # fix5 in play and menus (fit 1)
F5_TITLE = [0x012f, 0xff6f, 0x4444, 0x4444, 0x5555, 0x5555, 0x5555, 0x5555]  # fix5 before NBG3 was added
FIX6 = [0x0123, 0xee67, 0xeeee, 0x44ee, 0xeeee, 0xe55e, 0xeeee, 0xe55e]
REVIEW = [0x0167, 0x0123, 0x44ff, 0xffff, 0xf55f, 0xeeee, 0xf55f, 0xeeee]    # the review's set for the OLD memory layout (NBG0 map in A0)
NEW1 = [0x2311, 0x67fe, 0x004f, 0xf4fe, 0x55ff, 0xeeee, 0x55ff, 0xeeee]      # fix7, fit 1
NEW0 = [0x231f, 0x67fe, 0x0f4f, 0xfffe, 0x5fff, 0xeeee, 0x5fff, 0xeeee]      # fix7, fit 0

fails = 0
def expect(name, words, fit, want_pass, old=False):
    global fails
    errs, warns, info = chk.run_check(ROOT, words, fit, old_layout=old)
    ok = (not errs) == want_pass
    print(("ok   " if ok else "FAIL ") + f"{name} fit {fit}: {'pass' if not errs else str(len(errs)) + ' errors'}" + ("" if ok else "  <-- unexpected"))
    if not ok:
        fails += 1
        for e in errs[:6]: print("       ", e)

expect("F5 (play), the layout it ran with", F5, 1, False, True)
expect("F5 (title words), the layout it ran with", F5_TITLE, 1, False, True)
expect("fix6, the layout it ran with", FIX6, 1, False, True)
expect("fix6 words on the new layout", FIX6, 1, False)
expect("review set, old layout (it only fixes names and CPU, not the blank-name banks)", REVIEW, 1, False, True)
expect("fix7 words, fit 1", NEW1, 1, True)
expect("fix7 words, fit 0", NEW0, 0, True)
expect("fit-1 words with the fit off (extra reads: warnings only)", NEW1, 0, True)
expect("fit-0 words with the fit on", NEW0, 1, False)

# the cfg itself, both fits
for fit in (1, 0):
    errs, warns, info = chk.run_check(ROOT, None, fit)
    print(("ok   " if not errs else "FAIL ") + f"cfg fit {fit}"); fails += bool(errs)
r = subprocess.run([sys.executable, str(ROOT / "tools" / "vdp2_cycle_check.py"), "--quiet"], capture_output=True, text=True)
print(("ok   " if r.returncode == 0 else "FAIL ") + "whole check incl. register writers: " + r.stdout.strip().splitlines()[-1]); fails += r.returncode != 0

# Table 3.4 equals Ymir's kLoResPatterns (derived from real games)
ymir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Game Dev/Emulators/Ymir-baseline-a9f0cdae")
hp = ymir / "libs/ymir-core/include/ymir/hw/vdp/vdp_state.hpp"
if hp.exists():
    t = hp.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"kLoResPatterns\[8\] = \{(.*?)\};", t, re.S)
    masks = [int(x, 2) for x in re.findall(r"0b([01]{8})", m.group(1))]
    mine = [sum(1 << c for c in chk.LEGAL[p]) for p in range(8)]
    ok = masks == mine
    print(("ok   " if ok else "FAIL ") + "Table 3.4 matches Ymir kLoResPatterns (valid cell timings per name timing)"); fails += not ok
else:
    print("skip  Ymir source not found")

print("info  shipped-game vectors are listed in the notes (docs/notes/AVP_HWBOOT_FIX7_20261111.md); not asserted here")
print("tests:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
