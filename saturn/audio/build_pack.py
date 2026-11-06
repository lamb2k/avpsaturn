#!/usr/bin/env python
"""Build the Saturn audio pack and CD music tracks from the MAME renders (render_mame.lua). Output stays in WORK; never commit.
usage: build_pack.py WORK ROUTE_TSV [--all] [--rate 11025]
reads WORK/{sfx,music}.{wav,tsv}, WORK/sounds.json; writes WORK/pack.bin, WORK/clips/*.wav (reference), WORK/music/*.raw (CDDA), WORK/pack.json

Pack, big endian:
  'SAU1' u16 nsfx u16 nmusic u32 clip_bytes
  nsfx x 16 bytes:   u16 cmd, u8 prio, u8 chan_mask_hi, u8 chan_mask_lo, u8 tl, u8 flags (1 loop), u8 pad, u32 offset, u32 samples
  nmusic x 16 bytes: u16 cmd, u8 intro_track, u8 loop_track, u16 intro_cd_frames, 10 pad. intro_track 0: no intro. loop_track 0: ends after the intro.
  clip_bytes of 8 bit signed PCM, to the start of SCSP RAM.
Near-identical renders share one clip (the alternating pairs are the same sample on two channels).
CD tracks start at 2, track 1 being data; WORK/music/tNN_cccc.raw are 16 bit little endian 44.1 kHz stereo, whole CD frames.
"""
import json, pathlib, struct, sys, wave
import numpy as np

CD_FRAME = 588   # stereo samples at 44.1 kHz
SILENT = 40      # of 32767, the end trim threshold
MUSIC_MAX_S = 110.0
SAME_SOUND = 0.985   # correlation for two renders to share one clip
SAME_LENGTH = 32     # samples
NEAR_SAME = 1.5   # mean absolute difference of 8 bit samples


def read_wav(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == 44100 and w.getnchannels() == 2
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2)


def log_rows(p):
    start, rows = {}, []
    for l in open(p):
        c, k, t = l.split()
        if k == "S":
            start[c] = float(t)
        else:
            rows.append((int(c, 16), start[c], float(t), k == "M"))
    return rows


def decimator(rate):
    n = 63
    cut = 0.45 * rate / 44100
    h = np.sinc(2 * cut * (np.arange(n) - (n - 1) / 2)) * np.hamming(n)
    return h / h.sum()


def clip_of(st, a, b, rate, tail_s=0.25):
    """Mono float clip from the render, onset to last sound, lowered to rate."""
    i, j = int(a * 44100), min(len(st), int((b + tail_s) * 44100))
    m = st[i:j].astype(np.float64).mean(axis=1)
    loud = np.nonzero(np.abs(m) > SILENT)[0]
    if not len(loud):
        return None, 0
    m = m[max(0, loud[0] - 16):loud[-1] + 1]
    lat = (i + max(0, loud[0] - 16)) / 44100 - a
    y = np.convolve(m, decimator(rate), mode="same")
    k = 44100 / rate
    return np.interp(np.arange(0, len(y) / k) * k, np.arange(len(y)), y), lat


def correlation(a, b):
    a, b = a.astype(np.float64), b.astype(np.float64)
    return np.dot(a, b) / max(1.0, np.sqrt(np.dot(a, a) * np.dot(b, b)))


def to_pcm8(y):
    """8 bit signed with the level moved to the SCSP's TL (0.375 dB a step)."""
    peak = max(1.0, float(np.abs(y).max()))
    tl = int(np.clip(np.floor(-20 * np.log10(peak / 32767) / 0.375), 0, 255))
    g = 127 / (32767 * 10 ** (-tl * 0.375 / 20))
    return np.clip(np.round(y * g), -128, 127).astype(np.int8), tl


def loop_of(m):
    """Find (loop_start_s, loop_end_s) by matching the last 8 s of the render earlier in it; none if the track ended."""
    sr = 44100 // 16
    x = m.mean(axis=1)[::16].astype(np.float64)
    w = 8 * sr
    if len(x) < 3 * w or np.abs(x[-w:]).max() < 300:
        return None
    t = x[-w:] - x[-w:].mean()
    n = len(x) - w
    fx = np.fft.rfft(x, 2 * len(x))
    ft = np.fft.rfft(t[::-1], 2 * len(x))
    cor = np.fft.irfft(fx * ft)[w - 1:w - 1 + n]
    e = np.cumsum(x * x)
    en = np.sqrt(np.maximum(1.0, e[w - 1:w - 1 + n] - np.concatenate(([0], e[:n - 1]))))
    cor = cor / en / np.sqrt((t * t).sum())
    lim = n - sr * 4   # a real repeat, not the window on itself
    if lim < 1:
        return None
    best = int(np.argmax(cor[:lim]))
    if cor[best] < 0.9:
        return None
    period = n - best
    # walk the start back while the signal still repeats at this period
    s = best
    while s > sr // 2:
        a, b = x[s - sr // 2:s], x[s - sr // 2 + period:s + period]
        if np.dot(a, b) / max(1.0, np.sqrt(np.dot(a, a) * np.dot(b, b))) < 0.9:
            break
        s -= sr // 2
    return s / sr, (s + period) / sr


def main():
    work = pathlib.Path(sys.argv[1])
    route = {int(l.split("\t")[0], 16): l.split("\t")[1] for l in open(sys.argv[2])}
    rate = int(sys.argv[sys.argv.index("--rate") + 1]) if "--rate" in sys.argv else 11025
    full = "--all" in sys.argv
    table = json.load(open(work / "sounds.json"))["sounds"]
    (work / "clips").mkdir(exist_ok=True)
    (work / "music").mkdir(exist_ok=True)
    st = read_wav(work / "sfx.wav")
    sfx, blob, uniq = [], bytearray(), []
    census = {"route_bytes": 0, "all_bytes": 0, "silent": [], "looping": [], "shared": 0}
    for cmd, a, b, capped in sorted(log_rows(work / "sfx.tsv")):
        info = table[f"{cmd:x}"]
        y, lat = clip_of(st, a, b, rate)
        if y is None:
            census["silent"].append(hex(cmd))
            continue
        census["all_bytes"] += len(y)
        census["route_bytes"] += len(y) if cmd in route else 0
        if capped:
            census["looping"].append(hex(cmd))
        if not (full or cmd in route):
            continue
        pcm, tl = to_pcm8(y)
        if len(pcm) > 0xffff:
            raise SystemExit(f"{cmd:x}: {len(pcm)} samples, past the SCSP's 16 bit loop end")
        off = None
        for u, uo in uniq:
            k = min(len(u), len(pcm))
            if abs(len(u) - len(pcm)) <= SAME_LENGTH and correlation(u[:k], pcm[:k]) >= SAME_SOUND:
                off, pcm = uo, u      # each keeps its own level through TL
                census["shared"] += 1
                break
        if off is None:
            off = len(blob)
            uniq.append((pcm, off))
            blob += pcm.tobytes()
            if len(blob) & 1:
                blob += bytes(1)
        mask = sum(1 << c for c in info["chans"])
        sfx.append(dict(cmd=cmd, prio=info["prio"], mask=mask, tl=tl, loop=capped, off=off, n=len(pcm), lat=lat, s=len(pcm) / rate))
        with wave.open(str(work / "clips" / f"{cmd:04x}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            w.writeframes(np.clip(y, -32768, 32767).astype("<i2").tobytes())
    st = None
    music, track, ms = [], 2, read_wav(work / "music.wav")
    for cmd, a, b, capped in sorted(log_rows(work / "music.tsv")):
        if not (full or cmd in route):
            continue
        m = ms[int(a * 44100):int(min(b, a + MUSIC_MAX_S) * 44100)]
        loud = np.nonzero(np.abs(m).max(axis=1) > SILENT)[0]
        if not len(loud):
            continue
        m = m[loud[0]:]
        lp = loop_of(m)
        def cd_track(x):
            nonlocal track
            x = np.vstack([x, np.zeros((-len(x) % CD_FRAME, 2), dtype=x.dtype)])
            (work / "music" / f"t{track:02d}_{cmd:04x}.raw").write_bytes(x.astype("<i2").tobytes())
            track += 1
            return track - 1
        intro, loop = 0, 0
        if lp:                                  # intro as its own track, then the repeat
            a_f, b_f = int(lp[0] * 75) * CD_FRAME, int(lp[1] * 75) * CD_FRAME
            if a_f:
                intro = cd_track(m[:a_f])
            loop = cd_track(m[a_f:b_f])
        elif capped and np.abs(m[-2 * 44100:]).max() > SILENT:   # still playing, no repeat found within the render: repeat the whole render, with a seam
            loop = cd_track(m)
        else:
            loud = np.nonzero(np.abs(m).max(axis=1) > SILENT)[0]
            intro = cd_track(m[:loud[-1] + 1])
        intro_frames = (work / "music" / f"t{intro:02d}_{cmd:04x}.raw").stat().st_size // (CD_FRAME * 4) if intro else 0
        music.append(dict(cmd=cmd, intro=intro, loop=loop, intro_cd_frames=intro_frames, loop_s=lp, seam=bool(loop and not lp)))
    hdr = struct.pack(">4sHHI", b"SAU1", len(sfx), len(music), len(blob))
    for s in sfx:
        hdr += struct.pack(">HBBBBBBII", s["cmd"], s["prio"], s["mask"] >> 8, s["mask"] & 255, s["tl"], int(s["loop"]), 0, s["off"], s["n"])
    for m in music:
        hdr += struct.pack(">HBBH10x", m["cmd"], m["intro"], m["loop"], m["intro_cd_frames"])
    (work / "pack.bin").write_bytes(hdr + bytes(blob))
    json.dump(dict(rate=rate, census=census, sfx=sfx, music=music), open(work / "pack.json", "w"), indent=0)
    print(dict(rate=rate, sfx=len(sfx), clip_bytes=len(blob), header=len(hdr), route_clip_bytes=census["route_bytes"], all_clip_bytes=census["all_bytes"],
               shared=census["shared"], silent=len(census["silent"]), looping=census["looping"], longest=max((s["s"], hex(s["cmd"])) for s in sfx)))
    for m in music:
        print("music", hex(m["cmd"]), m)
    print("music bytes", sum((work / "music" / f).stat().st_size for f in [p.name for p in (work / "music").iterdir()]))


if __name__ == "__main__":
    main()
