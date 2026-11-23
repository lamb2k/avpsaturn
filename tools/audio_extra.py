#!/usr/bin/env python
"""Add sound clips the route census left out to the finished round sound packs (WORK/audio/rNNN.bin), without a new census, and (fix7c3) make every clip smaller: coverage lane.
usage: audio_extra.py WORK RENDERS [--report FILE] [--clips FILE]
  WORK     the build directory (rounds.json, sound_rank.json, audio/rNNN.bin). The first run keeps the packs as WORK/audio_orig/; every run patches from that copy, so it is idempotent.
  RENDERS  the render set (sfx.wav, sfx.tsv, sounds.json) that saturn/audio/build_pack.py reads (tools run: E:/AvP/learning/lane-audio). Renders are generated, never committed.
Which commands: TARGET below, in each file whose census sound list (rounds.json) holds them or that tools/sound_extra.txt names ("STAGEHEX CMDHEX USES", 00 = front end, 26 = ending, ALL = every stage file).
A command in the census list was only missing because its render never ended (a looping sound), which build_pack.py left out; saturn/audio/build_pack.py loop_clip() now cuts it into a seamless loop.
Fit rule (the one tools/rounds_config.py uses): SCSP_ROOM 0x7e000 bytes of header, tables and clips; score = route uses * 1000 + 500 for the sounds every stage keeps (KO, continue, game over).
A new clip that does not fit takes the room of the lowest scored clips of that file, only ones scoring below it; if that is not enough it is left out and reported (not with PACK_RESTORE).
Aliases (the same sample under several commands: 0x8e / 0x14e / 0x14f, 0x5b / 0x12c, 0x64 / 0x134) share one clip.
Switches (env, each default off; fix7c3, option 1: smaller clips, the same sounds):
  PACK_TRIM=1     head and tail of every one-shot clip go where it stays 50 dB under its own peak (build_pack.clip_variant), with a 5 ms fade. Loops are never touched.
  PACK_RATE=1     a one-shot clip is stored at 8,000 Hz or 5,512.5 Hz when at most 0.1 percent (-30 dB) of its energy lies above the new Nyquist (build_pack.pick_rate); the row's rate byte tells
                  sat_audio.c (built with AUDIO_CFLAGS=-DSAT_PACK_RATE) which OCT/FNS to play it at. The level stays the old row's TL.
  PACK_RESTORE=1  no eviction: every clip the packs dropped to fit (sound_rank.json dropped) comes back where it now fits, best scored first, together with the new clips; the ALL jingles go to every stage file.
With none of the switches the result is the fix7c2 pack set."""
import csv, json, os, pathlib, shutil, struct, sys
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "saturn" / "audio"))
import build_pack as bp
from wolverine.wv_audio import ROUND_SOUND_TABLE_ROOM, SCSP_PCM_ROOM, STAGE_HIT_CUES

SCSP_ROOM = 0x7e000
TARGET = [0x8e, 0x14e, 0x14f, 0x156, 0x5b, 0x64, 0x67, 0x7f, 0x87, 0x94, 0x12c, 0x134, 0x4f, 0x56, 0x26d, 0x252, 0x202,
          0x4a, 0x10f, 0x111, 0x115, 0x41, 0x10c]
RATE = 11025
TRIM, RATEON, RESTORE = (os.environ.get(k) == "1" for k in ("PACK_TRIM", "PACK_RATE", "PACK_RESTORE"))
RATE_HZ = {0: 11025.0, 1: 8000.0, 2: 5512.5}


def parse(b):
    assert b[:4] == b"SAU1"
    ns, nm, nb = struct.unpack(">HHI", b[4:12])
    rows = []
    for i in range(ns):
        cmd, prio, mh, ml, tl, fl, pad, off, n = struct.unpack(">HBBBBBBII", b[12 + 16 * i:28 + 16 * i])
        rows.append(dict(cmd=cmd, prio=prio, mask=mh << 8 | ml, tl=tl, loop=fl, rate=pad, off=off, n=n))
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
        hdr += struct.pack(">HBBBBBBII", r["cmd"], r["prio"], r["mask"] >> 8, r["mask"] & 255, r["tl"], r["loop"], r.get("rate", 0), offs[r["clip"]], r["n"])
    return hdr + mus + b"".join(parts)


def main():
    work, rend = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    report = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    clips_out = sys.argv[sys.argv.index("--clips") + 1] if "--clips" in sys.argv else None
    rj = json.load(open(work / "rounds.json"))
    rank = json.load(open(work / "sound_rank.json"))
    uses = {int(k, 16): {int(c, 16): n for c, n in v.items()} for k, v in rank["uses"].items()}
    dropped_old = {name: [int(c, 16) for c in cs] for name, cs in rank["dropped"].items()}
    table = json.load(open(rend / "sounds.json"))["sounds"]
    orig = work / "audio_orig"
    if not orig.exists():
        shutil.copytree(work / "audio", orig, ignore=shutil.ignore_patterns("music"))
    extra, extra_all = {}, {}
    for l in open(pathlib.Path(__file__).with_name("sound_extra.txt")):
        l = l.split("#")[0].split()
        if len(l) == 3:
            if l[0].upper() == "ALL":
                extra_all[int(l[1], 16)] = int(l[2])
            else:
                extra.setdefault(int(l[0], 16), {})[int(l[1], 16)] = int(l[2])
    files = rj["files"]
    stage_files = [f for f in files if f["stages"][0] not in (0, 0x26)]
    any_sound = set.intersection(*(set(f["sound"]) for f in stage_files))   # the sounds every stage keeps (KO, continue, game over)
    st = bp.read_wav(rend / "sfx.wav")
    rows_log = {r[0]: r for r in bp.log_rows(rend / "sfx.tsv")}
    cache = {}
    stats = {}   # cmd -> per-clip report row

    def render(c, rate_hz, trim):
        _, a, b, capped = rows_log[c]
        return bp.clip_variant(st, a, b, rate_hz, trim=trim)[0]

    def made(c, tl=None):
        """The clip of command c as the packs should carry it. tl given = keep that level (an existing clip); None = level from the clip's own peak."""
        key = (c, tl)
        if key in cache:
            return cache[key]
        _, a, b, capped = rows_log[c]
        info = table[f"{c:x}"]
        y11 = render(c, RATE, False)   # the clip as the fix7c2 packs carry it
        if capped and len(y11) > bp.LOOP_MAX:
            y = bp.loop_clip(y11, RATE)
            assert y is not None, hex(c)
            code, ratios, y11 = 0, {}, y
        else:
            trimmed = render(c, RATE, True) if TRIM else y11
            if RATEON and not capped:
                _, code, ratios = bp.pick_rate(trimmed)
            else:
                code, ratios = 0, {r: bp.band_ratio(trimmed, RATE, r / 2) for r, _ in bp.RATE_STEPS}
            y = trimmed if code == 0 else render(c, RATE_HZ[code], TRIM)
        # level: the clip keeps the level of the fix7c2 clip (a row's own TL, or the TL its 11,025 Hz render would get); a lower rate or a trim must not make it quieter, so the new samples are
        # scaled up to the old RMS over the span both have (never beyond the 8 bit peak)
        tl2 = tl if tl is not None else bp.to_pcm8(y11)[1]
        pcm = bp.to_pcm8_tl(y, tl2)
        hz = RATE_HZ[code]
        if code != 0 or TRIM:
            sec = min(len(y11) / 11025.0, len(y) / hz)
            a_old, a_new = y11[:int(sec * 11025)], y[:int(sec * hz)]
            r_old, r_new = float(np.sqrt((a_old * a_old).mean())) if len(a_old) else 0.0, float(np.sqrt((a_new * a_new).mean())) if len(a_new) else 0.0
            if r_new > 0 and r_old > r_new:
                pk = float(np.abs(pcm).max()) or 1.0
                sc = min(r_old / r_new, 127.0 / pk)
                if sc > 1.0:
                    pcm = bp.to_pcm8_tl(y * sc, tl2)
        out = dict(pcm=pcm, tl=tl2, rate=code, loop=int(capped), prio=info["prio"], mask=sum(1 << x for x in info["chans"]), ratios=ratios, y11=y11, y=y)
        cache[key] = out
        return out
    clip = {c: made(c) for c in TARGET}
    alias = {}   # looping targets: the same sample under several commands (circular correlation of equal length loops)
    for i, c in enumerate(TARGET):
        for d in TARGET[:i]:
            a, b = clip[c]["pcm"].astype(float), clip[d]["pcm"].astype(float)
            if clip[c]["loop"] and clip[d]["loop"] and abs(len(a) - len(b)) <= 32 and d not in alias:
                k = min(len(a), len(b)); a, b = a[:k] - a[:k].mean(), b[:k] - b[:k].mean()
                cc = np.fft.irfft(np.fft.rfft(a) * np.conj(np.fft.rfft(b)), k).max() / max(1.0, np.sqrt((a * a).sum() * (b * b).sum()))
                if cc > 0.97:
                    alias[c] = alias.get(d, d); break
    summary, file_rows = [], []
    shrink_seen = {}
    for i, f in enumerate(files):
        s = f["stages"][0]
        b = (orig / f"r{i:03d}.bin").read_bytes()
        rows, mus, nm, blob = parse(b)
        offsets = sorted({r["off"] for r in rows} | {len(blob)})
        available = {start: stop - start for start, stop in zip(offsets, offsets[1:])}
        blobs, idx = [], {}   # the clip table of this file: unique offsets
        for r in rows:
            offset = r["off"]
            samples = available.get(offset, 0)
            # Legacy aliases can advertise more samples than their stored clip.
            # Keep playback inside that clip when new clips follow it in the bank.
            r["n"] = min(r["n"], samples)
            if offset not in idx:
                idx[offset] = len(blobs)
                blobs.append(b"")
            r["clip"] = idx[offset]
            # Commands sharing an offset can have different sample counts.
            if r["n"] > len(blobs[r["clip"]]):
                blobs[r["clip"]] = blob[offset:offset + r["n"]]
        # ---- shrink the existing one-shot clips (PACK_TRIM / PACK_RATE): the clip is made again from the render at the row's own level and replaces the old one only if it reproduces it
        if TRIM or RATEON:
            groups = {}
            for r in rows:
                groups.setdefault(r["clip"], []).append(r)
            for k, g in groups.items():
                rep = min(g, key=lambda r: r["cmd"])
                if rep["loop"] or rep["cmd"] not in rows_log:
                    continue
                if rep["cmd"] not in shrink_seen:
                    m = made(rep["cmd"], tl=rep["tl"])
                    old = np.frombuffer(blobs[k], dtype=np.int8)
                    ref = bp.to_pcm8_tl(m["y11"], rep["tl"])
                    shrink_seen[rep["cmd"]] = (len(ref) == len(old) and bool((ref == old).mean() > 0.99), m, len(old))
                ok, m, nold = shrink_seen[rep["cmd"]]
                if not ok:
                    continue
                pcm = m["pcm"].tobytes()
                blobs[k] = pcm
                for r in g:
                    r["n"] = len(pcm); r["rate"] = m["rate"]

        def score(c):
            return max(uses.get(s, {}).get(c, 0), extra.get(s, {}).get(c, 0), extra_all.get(c, 0) if (RESTORE and s not in (0x26,)) else 0) * 1000 + (500 if c in any_sound else 0)

        def size(rs, bl):
            return 12 + 16 * (len(rs) + nm) + sum(len(x) + (len(x) & 1) for x in bl)
        u = uses.get(s, {})
        have = {r["cmd"] for r in rows}
        # candidates: TARGET commands this file's arcade stage plays, plus (PACK_RESTORE) the clips this file dropped
        want = [c for c in TARGET if c not in have and (c in f["sound"] or c in extra.get(s, {}) or (RESTORE and c in extra_all and s != 0x26)) and score(c) > (500 if c in any_sound else 0)]
        restore = [c for c in dropped_old.get(f["name"], []) if c not in have and c in rows_log and c not in want] if RESTORE else []
        added, evicted, unfit, restored = [], [], [], []
        stage_hits = STAGE_HIT_CUES.get(s, ())
        ordinary = sorted((c for c in want + restore if c not in stage_hits), key=lambda c: -score(c))
        for position, c in enumerate(ordinary + list(stage_hits)):
            added_after_mix = position >= len(ordinary)
            if added_after_mix and any(row["cmd"] == c for row in rows):
                continue
            key = alias.get(c, c)
            new_clip = None
            if key != c and key in [x["cmd"] for x in rows if x["cmd"] in TARGET]:
                new_clip = next(x["clip"] for x in rows if x["cmd"] == key)
            try:
                cl = made(c)
            except AssertionError:   # a render that never ended and has no steady period
                unfit.append(hex(c)); continue
            pcm_bytes = cl["pcm"].tobytes()
            if new_clip is None and not cl["loop"]:   # a near identical clip already in the file is shared (build_pack's rule), at the same rate
                for r in rows:
                    if r["rate"] != cl["rate"] or r["loop"] or abs(r["n"] - len(cl["pcm"])) > bp.SAME_LENGTH:
                        continue
                    o = np.frombuffer(blobs[r["clip"]], dtype=np.int8)
                    samples = len(cl["pcm"])
                    if len(o) >= samples and samples and bp.correlation(o[:samples], cl["pcm"]) >= bp.SAME_SOUND:
                        new_clip = r["clip"]; pcm_bytes = None; break
            cost = 16 + (0 if new_clip is not None else len(pcm_bytes) + (len(pcm_bytes) & 1))
            if not RESTORE and not added_after_mix:
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
            new_size = size(rows, blobs) + cost
            new_table = 12 + 16 * (len(rows) + nm + 1)
            if added_after_mix:
                fits = new_table <= ROUND_SOUND_TABLE_ROOM and new_size - new_table <= SCSP_PCM_ROOM
            else:
                fits = new_size <= SCSP_ROOM
            if not fits:
                unfit.append(hex(c)); continue
            if new_clip is None:
                blobs.append(pcm_bytes); new_clip = len(blobs) - 1
            rows.append(dict(cmd=c, prio=cl["prio"], mask=cl["mask"], tl=cl["tl"], loop=cl["loop"], rate=cl["rate"], off=0, n=len(cl["pcm"]), clip=new_clip))
            (restored if c in restore else added).append(hex(c))
        used = sorted({r["clip"] for r in rows}); ren = {k: j for j, k in enumerate(used)}
        for r in rows:
            r["clip"] = ren[r["clip"]]
        blobs = [blobs[k] for k in used]
        nb = build(rows, mus, nm, blobs)
        if stage_hits:
            samples = struct.unpack_from(">I", nb, 8)[0]
            assert samples <= SCSP_PCM_ROOM and len(nb) - samples <= ROUND_SOUND_TABLE_ROOM, (i, len(nb))
            free_before, free_after = SCSP_PCM_ROOM - len(blob), SCSP_PCM_ROOM - samples
        else:
            assert len(nb) <= SCSP_ROOM, (i, len(nb))
            free_before, free_after = SCSP_ROOM - len(b), SCSP_ROOM - len(nb)
        (work / "audio" / f"r{i:03d}.bin").write_bytes(nb)
        file_rows.append(dict(file=i, name=f["name"], stage=f"{s:02x}", pack_before=len(b), pack_after=len(nb), free_before=free_before, free_after=free_after, clips=len(rows),
                              added=" ".join(added), restored=" ".join(restored), evicted=" ".join(f"{c}({n})" for c, n in evicted), unfit=" ".join(unfit),
                              dropped_old=" ".join(hex(c) for c in dropped_old.get(f["name"], []))))
        if added or evicted or unfit or restored:
            summary.append(dict(file=i, name=f["name"], added=added, restored=restored, evicted=evicted, unfit=unfit, free_before=free_before, free_after=free_after))
    # ---- per-clip report: levels as played (sample * 10^(-TL * 0.375 / 20)), RMS over the first min(old, new) seconds
    for c, (ok, m, nold) in shrink_seen.items():
        y11, hz, tl = m["y11"], RATE_HZ[m["rate"]], m["tl"]
        old = bp.to_pcm8_tl(y11, tl).astype(float)
        new = m["pcm"].astype(float)
        sec = min(len(old) / 11025.0, len(new) / hz)

        def rms(a, r):
            a = a[:int(sec * r)]
            return float(np.sqrt((a * a).mean())) if len(a) else 0.0
        stats[c] = dict(cmd=c, status="ok" if ok else "left alone (the render does not reproduce the pack clip)", before=nold, after=len(new) if ok else nold, rate=int(hz) if ok else 11025,
                        band_8000=round(m["ratios"].get(8000.0, 0), 6), band_5512=round(m["ratios"].get(5512.5, 0), 6),
                        peak_change_db=round(20 * np.log10(max(1e-9, np.abs(new).max()) / max(1e-9, np.abs(old).max())), 2),
                        rms_change_db=round(20 * np.log10(max(1e-9, rms(new, hz)) / max(1e-9, rms(old, 11025.0))), 2))
    for c in TARGET:
        m = clip[c]
        stats[c] = dict(cmd=c, status="new", before=0, after=len(m["pcm"]), rate=int(RATE_HZ[m["rate"]]), band_8000=round(m["ratios"].get(8000.0, 0), 6), band_5512=round(m["ratios"].get(5512.5, 0), 6))
    txt = "\n".join(json.dumps(x) for x in summary)
    print(txt)
    print("files changed", len(summary), "of", len(files), "| aliases", {hex(k): hex(v) for k, v in alias.items()}, "| TRIM", TRIM, "RATE", RATEON, "RESTORE", RESTORE)
    if report:
        open(report, "w").write(txt + "\n")
        with open(str(report) + ".files.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(file_rows[0])); w.writeheader(); w.writerows(file_rows)
    if clips_out:
        keys = ["cmd", "status", "before", "after", "rate", "band_8000", "band_5512", "peak_change_db", "rms_change_db"]
        with open(clips_out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader()
            for c in sorted(stats):
                d = dict(stats[c]); d["cmd"] = hex(c); w.writerow(d)


if __name__ == "__main__":
    main()
