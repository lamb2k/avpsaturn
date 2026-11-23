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
import os

import numpy as np

CD_FRAME = 588   # stereo samples at 44.1 kHz
SILENT = 40      # of 32767, the end trim threshold
MUSIC_MAX_S = 80.0   # every track fits one CD with the data track
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


def decimator(rate, source_rate=44100):
    n = 63
    cut = 0.45 * rate / source_rate
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


# ---- fix7c3 (coverage lane): smaller clips, same sounds. Switches PACK_TRIM and PACK_RATE (env, default off) are read by tools/audio_extra.py; the functions live here next to clip_of.
TRIM_DB = 50.0       # the head and the tail go where the clip stays below this many dB under its own peak (never below SILENT)
TRIM_WIN = 64        # envelope window, samples at 44.1 kHz (1.5 ms)
TRIM_FADE_S = 0.005  # fade out into the cut, fade in when the head was cut
BAND_MAX = float(os.environ.get("PACK_BAND", "0.001"))     # (env PACK_BAND) a clip drops to a lower rate only if at most this share of its energy (-30 dB) lies above the new Nyquist frequency
RATE_STEPS = [(5512.5, 2), (8000.0, 1)]   # lowest first; code 0 = 11025 Hz (the pack row's rate byte; sat_audio.c with SAT_PACK_RATE: OCT/FNS from the code)


def clip_variant(st, a, b, rate, tail_s=0.25, trim=False):
    """clip_of at any rate, with an optional trim of head and tail at TRIM_DB under the peak (a short fade into the cut). Mono float, lat."""
    i, j = int(a * 44100), min(len(st), int((b + tail_s) * 44100))
    m = st[i:j].astype(np.float64).mean(axis=1)
    loud = np.nonzero(np.abs(m) > SILENT)[0]
    if not len(loud):
        return None, 0
    lo, hi = max(0, loud[0] - 16), loud[-1] + 1
    if trim:
        floor = max(SILENT, float(np.abs(m).max()) * 10 ** (-TRIM_DB / 20))
        n = (len(m) + TRIM_WIN - 1) // TRIM_WIN
        e = np.abs(np.concatenate([m, np.zeros(n * TRIM_WIN - len(m))])).reshape(n, TRIM_WIN).max(axis=1)
        w = np.nonzero(e > floor)[0]
        t_lo, t_hi = max(0, w[0] * TRIM_WIN - 16), min(len(m), (w[-1] + 1) * TRIM_WIN)
        head_cut, tail_cut = t_lo > lo, t_hi < hi
        lo, hi = max(lo, t_lo), min(hi, t_hi)
        m = m[:hi].copy()
        f = min(int(TRIM_FADE_S * 44100), (hi - lo) // 4)
        if tail_cut and f:
            m[hi - f:hi] *= np.linspace(1.0, 0.0, f, endpoint=False)
        if head_cut and f:
            m[lo:lo + f] *= np.linspace(0.0, 1.0, f, endpoint=False)
    m = m[lo:hi]
    lat = (i + lo) / 44100 - a
    y = np.convolve(m, decimator(rate), mode="same")
    k = 44100 / rate
    return np.interp(np.arange(0, len(y) / k) * k, np.arange(len(y)), y), lat


def band_ratio(y, rate, nyquist):
    """Share of the clip's energy above nyquist (Hz); y is a float clip at rate."""
    if len(y) < 8:
        return 0.0
    f = np.abs(np.fft.rfft(y * np.hanning(len(y)))) ** 2
    fr = np.fft.rfftfreq(len(y), 1.0 / rate)
    tot = float(f.sum())
    return float(f[fr > nyquist].sum() / tot) if tot > 0 else 0.0


def pick_rate(y11):
    """(rate_hz, code, ratios) for a clip at 11025 Hz: the lowest step whose Nyquist leaves at most BAND_MAX of the energy above it."""
    ratios = {r: band_ratio(y11, 11025, r / 2) for r, _ in RATE_STEPS}
    for r, code in RATE_STEPS:
        if ratios[r] <= BAND_MAX:
            return r, code, ratios
    return 11025.0, 0, ratios


def to_pcm8_tl(y, tl):
    """8 bit signed at a given TL (the level of the clip it replaces)."""
    g = 127 / (32767 * 10 ** (-tl * 0.375 / 20))
    return np.clip(np.round(y * g), -128, 127).astype(np.int8)


def correlation(a, b):
    a, b = a.astype(np.float64), b.astype(np.float64)
    return np.dot(a, b) / max(1.0, np.sqrt(np.dot(a, a) * np.dot(b, b)))


def to_pcm8(y):
    """8 bit signed with the level moved to the SCSP's TL (0.375 dB a step)."""
    peak = max(1.0, float(np.abs(y).max()))
    tl = int(np.clip(np.floor(-20 * np.log10(peak / 32767) / 0.375), 0, 255))
    g = 127 / (32767 * 10 ** (-tl * 0.375 / 20))
    return np.clip(np.round(y * g), -128, 127).astype(np.int8), tl


LOOP_MAX = 0xffff   # the SCSP's 16 bit loop end, in samples
LOOP_TARGET_S = 0.6


def loop_clip(y, rate):
    """A render that never ended (the Z80 loops it until a stop control; render_mame.lua caps it at 10 s) as a short seamless loop: skip the first second (attack), find the period, and
    cut a whole number of periods of about LOOP_TARGET_S, starting where the two ends meet best. The slot loops the whole clip (loop start 0), so the attack is not replayed. None if no
    steady period is found (the caller then leaves the sound out as before)."""
    a = int(rate * 1.0)
    if len(y) < a + int(rate * 3.0):
        return None
    x = y[a:].astype(np.float64)
    x = x - x.mean()
    n = len(x)
    f = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    ac = ac / max(1.0, ac[0])
    lo, hi = int(0.02 * rate), int(min(LOOP_TARGET_S * 2, 5.0) * rate)
    p = lo + int(np.argmax(ac[lo:hi]))
    if ac[p] < 0.5:
        return None
    m = max(1, int(round(LOOP_TARGET_S * rate / p)))
    best = None
    for L in range(max(lo, m * p - 24), min(LOOP_MAX, m * p + 25)):
        c = correlation(x[:rate], x[L:L + rate]) if len(x) > L + rate else -1
        if best is None or c > best[0]:
            best = (c, L)
    L = best[1]
    if L > LOOP_MAX or best[0] < 0.5:
        return None
    # start where x[s] and x[s + L] agree in value and slope within one period
    sc = np.arange(0, min(p, len(x) - L - 2))
    cost = np.abs(x[sc] - x[sc + L]) + np.abs((x[sc + 1] - x[sc]) - (x[sc + L + 1] - x[sc + L]))
    s0 = int(sc[int(np.argmin(cost))])
    # the last X samples of the loop fade into the X samples that follow the loop in the render (equal power), so the wrap has no step
    X = min(256, L // 4)
    if a + s0 + L + X > len(y):
        X = 0
    z = y[a + s0:a + s0 + L + X].astype(np.float64)
    out = z[:L].copy()
    if X:
        w = np.sin(np.linspace(0, np.pi / 2, X, endpoint=False))
        out[:X] = z[:X] * w + z[L:L + X] * np.cos(np.linspace(0, np.pi / 2, X, endpoint=False))
    return out


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
            if len(y) > LOOP_MAX:   # a render that never ended: keep a seamless loop of it
                y2 = loop_clip(y, rate)
                if y2 is not None:
                    y = y2
        if not (full or cmd in route):
            continue
        pcm, tl = to_pcm8(y)
        if len(pcm) > 0xffff:
            census.setdefault("too_long", []).append(hex(cmd)); print(f"{cmd:x}: {len(pcm)} samples, past the SCSP's 16 bit loop end, left out"); continue
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
    # Reading and looping the music is most of a run, and its result depends only on which tracks: many pack builds with the same tracks reuse it (env PACK_MUSIC_CACHE).
    rows = [r for r in sorted(log_rows(work / "music.tsv")) if full or r[0] in route]
    cache, cached = work / "music_cache.json", None
    if os.environ.get("PACK_MUSIC_CACHE") and cache.exists():
        c = json.load(open(cache))
        if c["cmds"] == [r[0] for r in rows]:
            cached = c["music"]
    music, track, ms = [], 2, None if cached is not None else read_wav(work / "music.wav")
    for cmd, a, b, capped in [] if cached is not None else rows:
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
    if cached is not None:
        music = cached
    elif os.environ.get("PACK_MUSIC_CACHE"):
        json.dump(dict(cmds=[r[0] for r in rows], music=music), open(cache, "w"))
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
