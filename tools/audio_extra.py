#!/usr/bin/env python
"""Add sound clips the route census left out to the finished round sound packs (WORK/audio/rNNN.bin), without a new census: coverage lane, fix7c2.
usage: audio_extra.py WORK RENDERS [--report FILE]
  WORK     the build directory (rounds.json, sound_rank.json, audio/rNNN.bin). The first run keeps the packs as WORK/audio_orig/; every run patches from that copy, so it is idempotent.
  RENDERS  the render set (sfx.wav, sfx.tsv, sounds.json) that saturn/audio/build_pack.py reads (tools run: E:/AvP/learning/lane-audio). Renders are generated, never committed.
Which commands: TARGET below, in each file whose census sound list (rounds.json) holds them or that tools/sound_extra.txt names ("STAGEHEX CMDHEX USES", '00' = front end, '26' = ending).
A command in the census list was only missing because its render never ended (a looping sound), which build_pack.py left out; saturn/audio/build_pack.py loop_clip() now cuts it into a seamless loop.
Fit rule (the one tools/rounds_config.py uses): SCSP_ROOM 0x7e000 bytes of header, tables and clips; score = route uses * 1000 + 500 for the sounds every stage keeps (KO, continue, game over).
A new clip that does not fit takes the room of the lowest scored clips of that file, only ones scoring below it; if that is not enough it is left out and reported.
Aliases (the same sample under several commands: 0x8e / 0x14e / 0x14f, 0x5b / 0x12c, 0x64 / 0x134) share one clip."""
import json, os, pathlib, shutil, struct, sys
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "saturn" / "audio"))
import build_pack as bp

SCSP_ROOM = 0x7e000
TARGET = [0x8e, 0x14e, 0x14f, 0x156, 0x5b, 0x64, 0x67, 0x7f, 0x87, 0x94, 0x12c, 0x134, 0x4f, 0x56]
RATE = 11025


def parse(b):
    assert b[:4] == b"SAU1"
    ns, nm, nb = struct.unpack(">HHI", b[4:12])
    rows = []
    for i in range(ns):
        cmd, prio, mh, ml, tl, fl, _, off, n = struct.unpack(">HBBBBBBII", b[12 + 16 * i:28 + 16 * i])
        rows.append(dict(cmd=cmd, prio=prio, mask=mh << 8 | ml, tl=tl, loop=fl, off=off, n=n))
    mus = b[12 + 16 * ns:12 + 16 * (ns + nm)]
    blob = b[12 + 16 * (ns + nm):12 + 16 * (ns + nm) + nb]
    assert len(blob) == nb
    return rows, mus, nm, blob


def build(rows, mus, nm, blobs):
    """blobs: list of bytes, each referenced by row['clip'] (index)."""
    off, parts, offs = 0, [], []
    for c in blobs:
        offs.append(off); parts.append(c); off += len(c)
        if off & 1:
            parts.append(b"\0"); off += 1
    rows = sorted(rows, key=lambda r: r["cmd"])
    hdr = b"SAU1" + struct.pack(">HHI", len(rows), nm, off)
    for r in rows:
        hdr += struct.pack(">HBBBBBBII", r["cmd"], r["prio"], r["mask"] >> 8, r["mask"] & 255, r["tl"], r["loop"], 0, offs[r["clip"]], r["n"])
    return hdr + mus + b"".join(parts)


def main():
    work, rend = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    report = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    rj = json.load(open(work / "rounds.json"))
    rank = json.load(open(work / "sound_rank.json"))
    uses = {int(k, 16): {int(c, 16): n for c, n in v.items()} for k, v in rank["uses"].items()}
    table = json.load(open(rend / "sounds.json"))["sounds"]
    orig = work / "audio_orig"
    if not orig.exists():
        shutil.copytree(work / "audio", orig, ignore=shutil.ignore_patterns("music"))
    extra = {}
    for l in open(pathlib.Path(__file__).with_name("sound_extra.txt")):
        l = l.split("#")[0].split()
        if len(l) == 3:
            extra.setdefault(int(l[0], 16), {})[int(l[1], 16)] = int(l[2])
    files = rj["files"]
    stage_files = [f for f in files if f["stages"][0] not in (0, 0x26)]
    any_sound = set.intersection(*(set(f["sound"]) for f in stage_files))   # the sounds every stage keeps (KO, continue, game over)
    # the clips: render, looping ones cut to a loop
    st = bp.read_wav(rend / "sfx.wav")
    rows_log = {r[0]: r for r in bp.log_rows(rend / "sfx.tsv")}
    clip = {}
    for c in TARGET:
        _, a, b, capped = rows_log[c]
        y, _ = bp.clip_of(st, a, b, RATE)
        if capped and len(y) > bp.LOOP_MAX:
            y = bp.loop_clip(y, RATE)
        assert y is not None and len(y) <= bp.LOOP_MAX, hex(c)
        pcm, tl = bp.to_pcm8(y)
        info = table[f"{c:x}"]
        clip[c] = dict(pcm=pcm, tl=tl, prio=info["prio"], mask=sum(1 << x for x in info["chans"]), loop=int(capped))
    # aliases: the same looping sample under several commands (circular correlation of equal length loops)
    alias = {}
    for i, c in enumerate(TARGET):
        for d in TARGET[:i]:
            a, b = clip[c]["pcm"].astype(float), clip[d]["pcm"].astype(float)
            if clip[c]["loop"] and clip[d]["loop"] and abs(len(a) - len(b)) <= 32 and d not in alias:
                k = min(len(a), len(b)); a, b = a[:k] - a[:k].mean(), b[:k] - b[:k].mean()
                cc = np.fft.irfft(np.fft.rfft(a) * np.conj(np.fft.rfft(b)), k).max() / max(1.0, np.sqrt((a * a).sum() * (b * b).sum()))
                if cc > 0.97:
                    alias[c] = alias.get(d, d); break
    out_rows = []
    summary = []
    for i, f in enumerate(files):
        s = f["stages"][0]
        src = orig / f"r{i:03d}.bin"
        b = src.read_bytes()
        rows, mus, nm, blob = parse(b)
        have = {r["cmd"] for r in rows}
        u = uses.get(s, {})
        # only sounds the arcade plays in this stage (route uses or tools/sound_extra.txt); the census list alone also names sounds with no play in a stage
        want = [c for c in TARGET if c not in have and (c in f["sound"] or c in extra.get(s, {})) and max(u.get(c, 0), extra.get(s, {}).get(c, 0)) > 0]
        # the clip table of this file: unique offsets
        blobs, idx = [], {}
        for r in rows:
            if r["off"] not in idx:
                idx[r["off"]] = len(blobs); blobs.append(blob[r["off"]:r["off"] + r["n"]])
            r["clip"] = idx[r["off"]]
        def score(c):
            return max(u.get(c, 0), extra.get(s, {}).get(c, 0)) * 1000 + (500 if c in any_sound else 0)
        def size(rs, bl):
            return 12 + 16 * (len(rs) + nm) + sum(len(x) + (len(x) & 1) for x in bl)
        before = SCSP_ROOM - size(rows, blobs)
        added, evicted, unfit = [], [], []
        for c in sorted(want, key=lambda c: -score(c)):
            key = alias.get(c, c)
            new_clip = None
            if key != c and key in [x["cmd"] for x in rows if x["cmd"] in TARGET]:
                new_clip = next(x["clip"] for x in rows if x["cmd"] == key)
            cost = 16 + (0 if new_clip is not None else len(clip[c]["pcm"]) + (len(clip[c]["pcm"]) & 1))
            # plan the evictions first: lowest scored clip groups, and only while the room they free is needed; the plan must cost fewer route uses than the new clip brings
            groups = {}
            for r in rows:
                groups.setdefault(r["clip"], []).append(r)
            order = sorted((max(score(r["cmd"]) for r in g), k) for k, g in groups.items() if k != new_clip and all(r["cmd"] not in TARGET for r in g))
            free, plan, lost = SCSP_ROOM - size(rows, blobs), [], 0
            for sc, k in order:
                if free >= cost:
                    break
                g = groups[k]
                free += len(blobs[k]) + (len(blobs[k]) & 1) + 16 * len(g)
                plan.append(k); lost += sum(score(r["cmd"]) for r in g)
            if free >= cost and lost < score(c) + (1 if not plan else 0):
                for k in plan:
                    evicted += [(hex(r["cmd"]), score(r["cmd"])) for r in groups[k]]
                    rows = [r for r in rows if r["clip"] != k]
                    blobs[k] = b""
            if SCSP_ROOM - size(rows, blobs) < cost:
                unfit.append(hex(c)); continue
            if new_clip is None:
                blobs.append(clip[c]["pcm"].tobytes()); new_clip = len(blobs) - 1
            cl = clip[c]
            rows.append(dict(cmd=c, prio=cl["prio"], mask=cl["mask"], tl=cl["tl"], loop=cl["loop"], off=0, n=len(cl["pcm"]), clip=new_clip))
            added.append(hex(c))
        # drop the emptied blobs, renumber
        used = sorted({r["clip"] for r in rows}); ren = {k: j for j, k in enumerate(used)}
        for r in rows:
            r["clip"] = ren[r["clip"]]
        blobs = [blobs[k] for k in used]
        nb = build(rows, mus, nm, blobs)
        assert len(nb) <= SCSP_ROOM, (i, len(nb))
        (work / "audio" / f"r{i:03d}.bin").write_bytes(nb)
        if added or evicted or unfit:
            summary.append(dict(file=i, name=f["name"], added=added, evicted=evicted, unfit=unfit, free_before=before, free_after=SCSP_ROOM - len(nb)))
    txt = "\n".join(json.dumps(x) for x in summary)
    print(txt)
    print("files changed", len(summary), "of", len(files), "| aliases", {hex(k): hex(v) for k, v in alias.items()})
    if report:
        open(report, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
