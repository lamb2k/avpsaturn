#!/usr/bin/env python
"""Run tools/golden_census.lua over a route and turn its raw output into the documented census directory. ROM-derived addresses: stays under E:/AvP, never commit output.
usage: golden_census.py run ROUTE OUTDIR | golden_census.py post OUTDIR [CFG_JSON]"""
import json, os, pathlib, shutil, subprocess, sys
OLD = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot")
HERE = pathlib.Path(__file__).resolve().parent


def ranges(words):
    out, s, p = [], None, None
    for a in sorted(words):
        if s is None:
            s = p = a
        elif a == p + 2:
            p = a
        else:
            out.append((s, p + 2))
            s = p = a
    if s is not None:
        out.append((s, p + 2))
    return out


def run(route, out):
    out.mkdir(parents=True, exist_ok=True)
    w = out / "mame"
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(OLD / ".deps/mame/full_route_nvram_baseline", w / "nvram/avspu")
    (w / "cfg").mkdir()
    env = dict(os.environ, AVSP_ROUTE=str(route).replace("\\", "/"), CENSUS_RAW=str(out / "raw.txt").replace("\\", "/"))
    r = subprocess.run([str(OLD / ".deps/mame/mame0289/mame.exe"), "avspu", "-rompath", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-autoboot_delay", "0",
                        "-nvram_directory", str(w / "nvram"), "-cfg_directory", str(w / "cfg"), "-snapshot_directory", str(out / "snap"), "-autoboot_script", str(HERE / "golden_census.lua")],
                       cwd=OLD, env=env, stdout=open(out / "stdout.txt", "w"), stderr=subprocess.STDOUT, timeout=int(os.environ.get("CENSUS_TIMEOUT", "3300")))
    print("exit", r.returncode)


def post(out, cfgpath):
    seen = set()
    if cfgpath:
        for k, n in json.load(open(cfgpath))["seen"].items():
            a = int(k, 16)
            seen.update(a + i for i in range(0, n, 2))
    data, k = {}, None
    for l in open(out / "raw.txt"):
        p = l.split()
        if p[0] == "K":
            k = p[1]
            data[k] = dict(meta=dict(first=int(p[3]), last=int(p[5]), irq=int(p[7]), maxobj=int(p[9])), T=[set(), set(), set(), set()], S={}, P=set(), O=set())
        elif p[0] == "T":
            data[k]["T"][int(p[1])].add(int(p[2], 16))
        elif p[0] == "S":
            data[k]["S"][p[1]] = int(p[2])
        elif p[0] in "PO":
            data[k][p[0]].add(int(p[1], 16))
    d = out / "sections"
    d.mkdir(exist_ok=True)
    rows = ["key\tfirst_frame\tlast_frame\tirq\tmax_objects\tsprite_keys\tscroll1_keys\tscroll2_keys\tscroll3_keys\tsounds\treg_words\tpcrel_words\tfetch_words"]
    for k, v in sorted(data.items(), key=lambda x: x[1]["meta"]["first"]):
        name = k.replace("/", "_")
        rom = {a for a in v["P"] if a < 0x200000}
        pcrel = {a for a in v["O"] if a not in seen} if seen else set(v["O"])
        fetch = v["O"] - pcrel
        with open(d / f"{name}.tiles.txt", "w") as f:
            for i in range(4):
                for t in sorted(v["T"][i]):
                    f.write(f"{i} {t:x}\n")
        (d / f"{name}.sounds.txt").write_text("".join(f"{s} {n}\n" for s, n in sorted(v["S"].items())))
        for suffix, words in (("reg", rom), ("pcrel", pcrel), ("fetch", fetch)):
            (d / f"{name}.{suffix}.txt").write_text("".join(f"{a:x} {b:x}\n" for a, b in ranges(words)))
        m = v["meta"]
        rows.append("\t".join(map(str, [k, m["first"], m["last"], m["irq"], m["maxobj"], *[len(x) for x in v["T"]], len(v["S"]), len(rom), len(pcrel), len(fetch)])))
    (out / "sections.tsv").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


if sys.argv[1] == "run":
    run(pathlib.Path(sys.argv[2]).resolve(), pathlib.Path(sys.argv[3]))
else:
    post(pathlib.Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None)
