#!/usr/bin/env python
"""Lane rounds: from census.json (tools/rounds_census.py) write WORK/rounds.json (holes, stage -> file, keys per file) and WORK/audio/rNN.bin + music tracks.
usage: rounds_config.py CENSUS.json WORK AUDIO_RENDERS [ROUTE_CENSUS,ROUTE_CENSUS...]   ROUTE_CENSUS: tools/golden_census.py directories of real routes, for use counts. AUDIO_RENDERS holds sfx.wav, sfx.tsv, music.wav, music.tsv, sounds.json (saturn/audio/render_mame.lua).
Each stage word has its own file; the same recipe for every stage. Env ROUNDS_VARIANTS=SPEC (tools/rounds_variants.py) adds a file per character set per stage, all with that stage's keep list; the base file stays the fallback for three characters. Sound: the stage's commands, least used on the real routes dropped if past SCSP RAM, reported with their uses. WORK/sound_rank.json keeps the counts. ROM-derived: E:/AvP/learning only."""
import concurrent.futures as cf, glob, json, os, pathlib, queue, shutil, subprocess, sys
C = json.load(open(sys.argv[1])); W = pathlib.Path(sys.argv[2]); A = pathlib.Path(sys.argv[3])
REPO = pathlib.Path(__file__).resolve().parents[1]
SCSP_ROOM = 0x7e000
USES = {}   # stage -> command -> enqueues over all real routes
for c in (sys.argv[4].split(",") if len(sys.argv) > 4 else []):
    for f in glob.glob(c + "/sections/*.sounds.txt"):
        u = USES.setdefault(int(pathlib.Path(f).name[:4], 16), {})
        for l in open(f):
            a, n = l.split()
            a = int(a, 16) & 0xffff
            u[a] = u.get(a, 0) + int(n)
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
# Pages that two or more stages read hold data any stage can reach (object records, scripts): every stage keeps them, without the page either side. A record at 0x333d4,
# read in stages 06, 10 and 12 but not kept in 1c, read as zeros there and gave fatal 0xe2 at 0xa9cc4 (Hunter, whole-game run).
SHARED_MIN = int(os.environ.get("ROUNDS_SHARED_MIN", "2"))
_n = {}
for s in order:
    if s:
        for p in set(pg[s]):
            _n[p] = _n.get(p, 0) + 1
SHARED = {p for p, c in _n.items() if c >= SHARED_MIN} if SHARED_MIN else set()
for f in files:
    s = f["stages"][0]
    if s == 0:
        f["keep_pages"] = pad(sorted({p for v in pg.values() for p in v}))
    else:
        nxt = next((x for x in order if x > s), None)
        f["keep_pages"] = sorted(set(pad(sorted(set(pg[s]) | set(pg[0]) | set(pg.get(nxt, []))))) | SHARED)
# Pages the lifted code read on real runs (-DSAT_READMAP, readmiss.py --out) that a stage's file did not keep: env ROUNDS_READ_EXTRA=JSON {stage hex: [pages]}.
if os.environ.get("ROUNDS_READ_EXTRA"):
    _x = json.load(open(os.environ["ROUNDS_READ_EXTRA"]))
    for f in files:
        f["keep_pages"] = sorted(set(f["keep_pages"]) | set(_x.get(hex(f["stages"][0]), [])))
    print("read extra pages", sum(len(v) for v in _x.values()))
VD, variant_file = None, {}
if os.environ.get("ROUNDS_VARIANTS"):
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import rounds_variants
    VD = rounds_variants.Data(os.environ["ROUNDS_VARIANTS"])
    for base in list(files[1:]):
        s = base["stages"][0]
        row = variant_file[s] = [stage_file[s]]
        for m in rounds_variants.MASKS:
            row.append(len(files))
            files.append(dict(base, name=f"{base['name']}_m{m:x}", mask=m))
(W / "rounds.json").write_text(json.dumps({"holes": C["holes"], "page": P, "stage_file": {str(k): v for k, v in stage_file.items()}, "files": files, "variant_masks": list(rounds_variants.MASKS) if VD else [], "variant_file": {str(k): v for k, v in variant_file.items()}}))
tab = json.load(open(A / "sounds.json"))["sounds"]
is_music = lambda c: tab.get(f"{c:x}", {}).get("cls") == "music"
music = sorted({c for f in files for c in f["sound"] if is_music(c)})
aw = W / "audio_build"; aw.mkdir(exist_ok=True)
for n in ("sfx.wav", "sfx.tsv", "music.wav", "music.tsv", "sounds.json"):
    if not (aw / n).exists():
        os.link(A / n, aw / n)
def run(route, extra=(), aw=aw):
    r = aw / "route.tsv"
    r.write_text("".join(f"{c:x}\tr\n" for c in route))
    subprocess.run([sys.executable, str(REPO / "saturn/audio/build_pack.py"), str(aw), str(r), *extra], check=True, stdout=subprocess.DEVNULL, env=dict(os.environ, PACK_MUSIC_CACHE="1"))
    return json.load(open(aw / "pack.json"))
run(music, ["--all"])
allsfx = json.load(open(aw / "pack.json"))["sfx"]
size = {x["cmd"]: x["n"] for x in allsfx}
clip = {x["cmd"]: x["off"] for x in allsfx}   # near-identical renders share one clip
(W / "audio").mkdir(exist_ok=True)
dropped, ranks = {}, {}
any_sound = set(ANY["sound"])
slots = queue.Queue()   # one audio build directory per worker
for n in range(int(os.environ.get("ROUNDS_JOBS", "6"))):
    d = W / f"audio_build{n}"; d.mkdir(exist_ok=True)
    music_dir = d / "music"
    if music_dir.exists():
        shutil.rmtree(music_dir)
    (d / "music_cache.json").unlink(missing_ok=True)
    for x in ("sfx.wav", "sfx.tsv", "music.wav", "music.tsv", "sounds.json"):
        if not (d / x).exists():
            os.link(A / x, d / x)
    slots.put(d)
def one(job):
    i, f = job
    d = slots.get()
    want = [c for c in f["sound"] if c in size]
    use = USES.get(f["stages"][0], {})
    score = VD.sound_score(f["stages"][0], f["mask"], want, any_sound) if "mask" in f else {c: use.get(c, 0) * 1000 + (500 if c in any_sound else 0) for c in want}
    want.sort(key=lambda c: (-score[c], size[c], c))
    used, keep, clips = 0, [], set()
    for c in want:   # most used first; a clip shared with one already kept costs nothing
        cost = 0 if clip[c] in clips else size[c]
        if used + cost <= SCSP_ROOM:
            keep.append(c); used += cost; clips.add(clip[c])
    p = run(sorted(set(keep) | set(music)), aw=d)
    # Sharing can differ in the real build: take off the least used until it fits, then try the rest once.
    while (d / "pack.bin").stat().st_size > SCSP_ROOM:
        keep.pop(); p = run(sorted(set(keep) | set(music)), aw=d)
    real = (d / "pack.bin").stat().st_size
    add = []
    for c in (c for c in want if c not in keep):
        if real + 16 + size[c] <= SCSP_ROOM:   # 16: its table row
            add.append(c); real += 16 + size[c]
    if add:
        keep += add
        p = run(sorted(set(keep) | set(music)), aw=d)
    assert (d / "pack.bin").stat().st_size <= SCSP_ROOM
    dropped[f["name"]] = [hex(c) for c in want if c not in keep]
    ranks[f["name"]] = {hex(c): use.get(c, 0) for c in want if c not in keep}
    shutil.copy(d / "pack.bin", W / "audio" / f"r{i:03d}.bin")
    print(f["name"], "sfx", len(p["sfx"]), "clip bytes", (W / "audio" / f"r{i:03d}.bin").stat().st_size, "dropped (route uses)", ranks[f["name"]], flush=True)
    slots.put(d)
with cf.ThreadPoolExecutor(slots.qsize()) as ex:
    list(ex.map(one, enumerate(files)))
(W / "sound_rank.json").write_text(json.dumps(dict(dropped=ranks, uses={f"{s:02x}": {hex(c): n for c, n in u.items()} for s, u in USES.items()})))
if (W / "audio/music").exists():
    shutil.rmtree(W / "audio/music")
shutil.copytree(music_dir, W / "audio/music")   # every worker built the same tracks
print("music", [hex(c) for c in music], "bytes", sum(p.stat().st_size for p in (W / "audio/music").iterdir()))
