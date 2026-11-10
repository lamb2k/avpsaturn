#!/usr/bin/env python
"""Host runner with the bonus-character wrappers linked (native Wolverine lane, Stage 0).

tools/lift_runner/apply_overrides.py builds the golden-checked host runner WITHOUT the guest wrappers: it compiles game_bind.c with
-DHOST_CHECK only (no SAT_GUESTS), never builds guests.c or wolverine.c, and renames only the overrides.txt routines to lifted_NNN. So a
host run through it never reaches f_195ec/f_1cf54/f_19f9a wrappers or any fork. This script builds the runner the way saturn/rt/build.py builds the
target: same sources (WORK/src), same renames (GUEST_WRAP, the fork entries), same game_bind.c flags, plus the fork file from tools/wolverine/forkgen.py.

usage: build_native_host.py WORK OUTDIR NAME [--ids none|ship|all] [--guests 0|1] [--defs "-DX -DY"]
  WORK    a saturn/rt/build.py work dir (src/c*.c, dispatch.inc, rt.bin, op.bin, gen/wolverine_data.inc)
  OUTDIR  scratch for objects; the runner is OUTDIR/NAME
  --guests 0  the plain runner (what apply_overrides.py builds): the baseline "unmodified Schaefer"
  --guests 1  game_bind.c with -DSAT_GUESTS, guests.c, wolverine.c, host_guests.c; fork ids --ids (default none)
Output is ROM-derived and stays on this PC. Host objects are cached by the md5 of their source text."""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

T = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(T / "tools/wolverine"))
import forkgen

GUEST_WRAP = ("1cf54", "1d03e", "1d116", "195ec", "19f9a")


def wsl(p):
    p = pathlib.Path(p).resolve().as_posix()
    return "/mnt/" + p[0].lower() + p[2:]


def run(cmd):
    r = subprocess.run(["wsl.exe", "-e", "sh", "-c", cmd], capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise SystemExit("FAILED: " + cmd[:300] + "\n" + r.stdout[-3000:] + r.stderr[-3000:])
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("outdir")
    ap.add_argument("name")
    ap.add_argument("--ids", default="none")
    ap.add_argument("--guests", type=int, default=0)
    ap.add_argument("--defs", default="")
    ap.add_argument("--mutate", default="", help="negative control: FROM=>TO replaced once in the fork text (the harness must report DIFFERENT)")
    ap.add_argument("--reloc", type=int, default=0, help="1: the relocated animation block (plan V2): the 10 table-base immediates go through WVB(), host_reloc.c is linked; WVBLOCK/WVSLOTS at run time switch it on")
    ap.add_argument("--kernel", default=str(T / "tools/lift_runner/host_kernel.c"))
    a = ap.parse_args()
    work, out = pathlib.Path(a.work), pathlib.Path(a.outdir)
    (out / "obj").mkdir(parents=True, exist_ok=True)
    overrides = (T / "saturn/game/overrides.txt").read_text().split()
    ids = () if a.ids == "none" else forkgen.SHIP_IDS if a.ids == "ship" else forkgen.ALL_IDS if a.ids == "all" else tuple(int(x) for x in a.ids.split(","))
    wrap = (GUEST_WRAP + (('24f04',) if '-DSAT_WV_NATIVE_GFX' in a.defs else ()) if a.guests else ()) + (forkgen.wrapped_names(ids) if a.guests else ())
    sources_o = forkgen.read_sources(work / "src")
    hdr = ""
    if a.reloc:
        (out / "wvreloc.h").write_bytes(("extern unsigned wv_anim_delta;" + chr(10) + "#define WVB(b) ((b)+wv_anim_delta)" + chr(10)).encode())
        hdr = " -include " + wsl(out / "wvreloc.h")
        pat = re.compile(r"\(\(u32\)(0x(?:162f90|163032|163074|1630f6)u)\)")
        n_imm = 0
        for k in list(sources_o):
            sources_o[k], c = pat.subn(lambda m: "((u32)WVB(" + m.group(1) + "))", sources_o[k])
            n_imm += c
        print("table-base immediates rewritten:", n_imm)
    objs = []
    jobs = []   # (source path, object path, extra flags)
    for name, t in sources_o.items():
        for n in overrides + list(wrap):
            t = t.replace("void f_%s(void){" % n, "void lifted_%s(void){" % n)
        h = hashlib.md5(t.encode()).hexdigest()[:12]
        src, obj = out / "obj" / ("%s_%s.c" % (name[:-2], h)), out / "obj" / ("%s_%s.o" % (name[:-2], h))
        if not obj.exists():
            src.write_bytes(t.encode())
            jobs.append((src, obj, "-DHOST -DPREEMPT -O1" + hdr))
        objs.append(obj)
    fork_text = ""
    if a.guests and ids:
        r = forkgen.build(sources_o, ids)
        bad = forkgen.check_textual_identity(sources_o, r)
        if bad:
            raise SystemExit("forkgen: textual identity failed for " + ",".join(bad))
        if a.mutate:
            f_, t_ = a.mutate.split("=>")
            assert f_ in r.text, "mutation target not found"
            r.text = r.text.replace(f_, t_, 1)
        fsrc, fobj = out / "obj" / ("wvfork_%s.c" % a.name), out / "obj" / ("wvfork_%s.o" % a.name)
        fsrc.write_bytes(r.text.encode())
        jobs.append((fsrc, fobj, "-DHOST -DPREEMPT -O1 -DSAT_WV_FORK_COUNT"))
        objs.append(fobj)
        print("fork", [hex(x) for x in r.wrapped], "copied", len(r.copied))
    g = T / "saturn/game"
    gen = work / "gen"
    extra = []
    if a.reloc:
        o = out / "obj" / ("host_reloc_%s.o" % a.name)
        jobs.append((T / "tools/lift_runner/host_reloc.c", o, "-O1"))
        extra.append(o)
    bind = "-DHOST_CHECK" + (" -DSAT_GUESTS" if a.guests else "")
    for n, flags in (("game_hot", "-DHOST_CHECK"), ("game_bind", bind + " " + a.defs)):
        o = out / "obj" / ("%s_%s.o" % (n, a.name))
        jobs.append((g / (n + ".c"), o, flags + " -O1"))
        extra.append(o)
    if a.guests:
        wv = T / "saturn/guests/wolverine/wolverine.c"
        hg = T / "tools/lift_runner/host_guests.c"
        inc = "-I%s -I%s -I%s" % (wsl(gen), wsl(T / "saturn/rt"), wsl(g))
        for src, nm, fl in ((T / "saturn/rt/guests.c", "guests", ""),
                            (wv, "wolverine", "-Dsat_guest_objects=sat_guest_wolverine_objects -DWV_HOST_ROM"),
                            (hg, "host_guests", "")):
            o = out / "obj" / ("%s_%s.o" % (nm, a.name))
            jobs.append((src, o, "-DHOST_CHECK -O1 %s %s %s" % (inc, a.defs, fl)))
            extra.append(o)
    cmds = []
    for src, obj, fl in jobs:
        cmds.append("gcc -w -g -fno-strict-aliasing %s -c '%s' -o '%s'" % (fl, wsl(src), wsl(obj)))
    # the wrapped-lifted chunks and the dispatch table
    (out / "dispatch.inc").write_bytes((work / "dispatch.inc").read_bytes())
    cl = (out / "cmds.txt")
    cl.write_bytes(("\n".join(c.replace("'", "\"") for c in cmds) + "\n").encode())
    pre = ("xargs -P 14 -d '\n' -I@ sh -c @ < '%s' && " % wsl(cl)) if cmds else ""
    link = "cd '%s' && %sgcc -w -O1 -g -rdynamic -DPREEMPT -I. '%s' %s -o '%s'" % (
        wsl(out), pre, wsl(a.kernel), " ".join("'%s'" % wsl(o) for o in objs + extra), a.name)
    run(link)
    print("built", out / a.name, "objects compiled", len(jobs))


if __name__ == "__main__":
    main()
