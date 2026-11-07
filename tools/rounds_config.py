#!/usr/bin/env python
"""Lane rounds: from census.json (tools/rounds_census.py) write WORK/rounds.json (holes, stage -> file, keys per file) and WORK/audio/rNN.bin + music tracks.
usage: rounds_config.py CENSUS.json WORK AUDIO_RENDERS   AUDIO_RENDERS holds sfx.wav, sfx.tsv, music.wav, music.tsv, sounds.json (saturn/audio/render_mame.lua).
Each stage word has its own file; the same recipe for every stage. Sound: the stage's commands, largest clips dropped if past SCSP RAM, reported. ROM-derived: E:/AvP/learning only."""
import json, os, pathlib, shutil, subprocess, sys
C = json.load(open(sys.argv[1])); W = pathlib.Path(sys.argv[2]); A = pathlib.Path(sys.argv[3])
REPO = pathlib.Path(__file__).resolve().parents[1]
SCSP_ROOM = 0x7e000
ANY = C["stages"].pop("any", dict(keys=[[], [], [], []], sound=[], pages=[]))   # KO, continue, game over: every stage has them
# Tiles only KO and continue show (player death, continue screen). Enemies on screen at a KO belong to their stage and are already in its own set.
seen = [set().union(*(v["keys"][i] for v in C["stages"].values())) for i in range(4)]
extra = [sorted(set(ANY["keys"][i]) - seen[i]) for i in range(4)]
print("tiles only seen on KO and continue", [len(e) for e in extra])
for v in C["stages"].values():
    v["keys"] = [sorted(set(a) | set(b)) for a, b in zip(v["keys"], extra)]
    v["sound"] = sorted(set(v["sound"]) | set(ANY["sound"]))
    v["pages"] = sorted(set(v["pages"]) | set(ANY["pages"]))
files = [dict(name="front", stages=[0], keys=C["stages"]["00"]["keys"], sound=C["stages"]["00"]["sound"])]
stage_file = {0: 0}
for k in sorted(C["stages"]):
    s = int(k, 16)
    if s == 0:
        continue
    stage_file[s] = len(files)
    files.append(dict(name=f"stage{s:02x}", stages=[s], keys=C["stages"][k]["keys"], sound=C["stages"][k]["sound"]))
# What a stage must find intact: its own pages, the next stage's (read before the load, while the word settles) and the front end's, each with a page either side. The front end keeps all of them.
order = sorted(int(k, 16) for k in C["stages"])
P = C["page"]
pad = lambda ps: sorted({p + d for p in ps for d in (-1, 0, 1) if 0 <= p + d < 0x200000 // P})
pg = {s: C["stages"][f"{s:02x}"]["pages"] for s in order}
for f in files:
    s = f["stages"][0]
    if s == 0:
        f["keep_pages"] = pad(sorted({p for v in pg.values() for p in v}))
    else:
        nxt = next((x for x in order if x > s), None)
        f["keep_pages"] = pad(sorted(set(pg[s]) | set(pg[0]) | set(pg.get(nxt, []))))
(W / "rounds.json").write_text(json.dumps({"holes": C["holes"], "page": P, "stage_file": {str(k): v for k, v in stage_file.items()}, "files": files}))
tab = json.load(open(A / "sounds.json"))["sounds"]
is_music = lambda c: tab.get(f"{c:x}", {}).get("cls") == "music"
music = sorted({c for f in files for c in f["sound"] if is_music(c)})
aw = W / "audio_build"; aw.mkdir(exist_ok=True)
for n in ("sfx.wav", "sfx.tsv", "music.wav", "music.tsv", "sounds.json"):
    if not (aw / n).exists():
        os.link(A / n, aw / n)
def run(route, extra=()):
    r = aw / "route.tsv"
    r.write_text("".join(f"{c:x}\tr\n" for c in route))
    subprocess.run([sys.executable, str(REPO / "saturn/audio/build_pack.py"), str(aw), str(r), *extra], check=True, stdout=subprocess.DEVNULL)
    return json.load(open(aw / "pack.json"))
run(music, ["--all"])
size = {x["cmd"]: x["n"] for x in json.load(open(aw / "pack.json"))["sfx"]}
(W / "audio").mkdir(exist_ok=True)
dropped = {}
for i, f in enumerate(files):
    want = [c for c in f["sound"] if c in size]
    want.sort(key=lambda c: size[c])
    used, keep = 0, []
    for c in want:
        if used + size[c] <= SCSP_ROOM:
            keep.append(c); used += size[c]
    dropped[f["name"]] = [hex(c) for c in want if c not in keep]
    p = run(sorted(set(keep) | set(music)))
    # Identical clips are shared, so the real size is smaller than the sum: put back what still fits, largest last.
    real = (aw / "pack.bin").stat().st_size
    more = [c for c in want if c not in keep]
    add = []
    for c in more:
        if real + size[c] <= SCSP_ROOM:
            add.append(c); real += size[c]
    if add:
        keep += add
        p = run(sorted(set(keep) | set(music)))
    dropped[f["name"]] = [hex(c) for c in want if c not in keep]
    shutil.copy(aw / "pack.bin", W / "audio" / f"r{i:02d}.bin")
    print(f["name"], "sfx", len(p["sfx"]), "clip bytes", (W / "audio" / f"r{i:02d}.bin").stat().st_size, "dropped", dropped[f["name"]], flush=True)
if (W / "audio/music").exists():
    shutil.rmtree(W / "audio/music")
shutil.copytree(aw / "music", W / "audio/music")
print("music", [hex(c) for c in music], "bytes", sum(p.stat().st_size for p in (W / "audio/music").iterdir()))
