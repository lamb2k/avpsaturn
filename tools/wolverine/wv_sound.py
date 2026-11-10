#!/usr/bin/env python
"""Wolverine's own sounds from Marvel Super Heroes vs. Street Fighter (lane wv-sounds, 2026-11-09).
ROM-derived output: it stays under E:/AvP/learning (or the owner's asset directory), never in git. Nothing here carries sample data.

Sources: the owner's mshvsf set, run in MAME 0.289 through the MSHvSF repo's tools/run_mshvsf_mame.py. The arcade's sound is a Z80 driver plus QSound: a move sends
a command number to the sound mailbox (68000 0x618000, Z80 0xc000), and the Z80 turns it into QSound voice starts (bank, address, pitch, envelope). The same command number gives
different voice samples depending on the character voice set the game loaded for that side: the VS screen sends 0x484 for a left player Wolverine, and only after it do 0x120..0x13f
play his voice. So every clip here is rendered through the real Z80 driver and QSound (mame_wvrender.lua, AUDIO_PRE=484 first) and cut from MAME's own audio, the way saturn/audio/build_pack.py
made the AvP clips: what the arcade plays is what the clip is.

usage:
  wv_sound.py render OUTDIR [CMDS_FILE]   run MAME over the commands (default: the SOUNDS list), writes OUTDIR/render.{wav,tsv,qs}
  wv_sound.py build  OUTDIR ASSETDIR      cut the clips from OUTDIR/render.wav, write ASSETDIR/wv_sound.json and wv_sound.bin (the Saturn clip format) and ASSETDIR/wav/*.wav (listening copies)
  wv_sound.py list                        print the sound list
env: MSHVSF_REPO (the repo with tools/run_mshvsf_mame.py and the ROM set), WV_SOUND_PY (its python).

Clip format (what wv_audio.py puts into a stage's sound pack): 8 bit signed mono PCM at 11025 Hz, level carried by the SCSP total level `tl` (0.375 dB a step) exactly as build_pack.py does,
so a clip is as loud, against the AvP clips, as MAME played it.
"""
import json
import os
import pathlib
import subprocess
import sys
import wave

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "saturn/audio"))
import build_pack as BP   # to_pcm8 / decimator: the same level and filter as the AvP clips

RATE = 11025
CMD_BASE = 0x2c0          # first AvP sound number a Wolverine sound takes: 0x276..0x2ff are free in the driver's table (null entries), saturn/guests/wolverine/wv_sound.h
LOAD_VOICES = 0x484       # VS screen call that loads Wolverine's voice set for the left player

# (id, name, MSHvSF command, AvP priority, channel mask, max seconds, role). Order and ids are those of saturn/guests/wolverine/wv_sound.h. Evidence: docs/notes/AVP_WOLVERINE_SOUNDS_20261109.md.
# Channels are SCSP slots 0..15 as in the game's own table: 12 (0x1000) is where Schaefer's voices play, 10 (0x400) and 11 (0x800) are shared effect channels (the rule "priority >= occupant" decides).
V, S, H = 0x1000, 0x0400, 0x0800
_ROWS = [
    # name,          cmd,   prio, mask, max s, where, role
    ("SELECT",       0x21a, 6, V, 0,   "front", "character select shout"),
    ("INTRO",        0x207, 6, V, 0.9, "stage", "round entrance: Let's go, bub."),
    ("CLAW_L",       0x124, 5, S, 0,   "stage", "claw swing, light"),
    ("CLAW_M",       0x125, 5, S, 0,   "stage", "claw swing, medium"),
    ("CLAW_H",       0x126, 5, S, 0,   "stage", "claw swing, heavy"),
    ("ATK_A",        0x20a, 6, V, 0,   "stage", "attack shout, short"),
    ("ATK_B",        0x20b, 6, V, 0,   "stage", "attack shout"),
    ("ATK_D",        0x20d, 6, V, 0,   "stage", "attack shout"),
    ("ATK_H",        0x209, 6, V, 0.5, "stage", "heavy attack shout"),
    ("HURT_A",       0x203, 6, V, 0,   "stage", "hurt voice"),
    ("HURT_B",       0x202, 6, V, 0,   "stage", "hurt voice, short"),
    ("KO",           0x200, 7, V, 0.9, "stage", "knocked out scream"),
    ("TORNADO",      0x204, 7, V, 0,   "stage", "Tornado Claw!"),
    ("BERSERKER",    0x206, 7, V, 0,   "stage", "Berserker Barrage!"),
    ("CLAW_HIT_L",   0x10e, 5, H, 0,   "stage", "claw hits an enemy, light (sharp)"),
    ("CLAW_HIT_H",   0x243, 5, H, 0,   "stage", "claw hits an enemy, heavy"),
    ("BERSERKER_GRUNT", 0x20c, 6, V, 0, "stage", "grunt per Berserker contact"),
]
SOUNDS = [dict(id=i, name=n, cmd=c, prio=p, mask=m, max_s=ms, where=w, role=r) for i, (n, c, p, m, ms, w, r) in enumerate(_ROWS)]


def sound_list():
    return SOUNDS


def mame(args, env):
    repo = pathlib.Path(os.environ.get("MSHVSF_REPO", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-MSHvSF"))
    py = os.environ.get("WV_SOUND_PY", sys.executable)
    return subprocess.run([py, "tools/run_mshvsf_mame.py", "--", "mshvsf", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", *args],
                          cwd=repo, env=dict(os.environ, **env), check=True, capture_output=True)


def render(out, cmds_file=None):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if cmds_file is None:
        cmds_file = out / "cmds.txt"
        cmds_file.write_text("".join("%x 110\n" % s["cmd"] for s in SOUNDS))
    base = str(out / "render").replace("\\", "/")
    mame(["-wavwrite", base + ".wav", "-autoboot_script", str(HERE / "mame_wvrender.lua").replace("\\", "/")],
         dict(AUDIO_CMDS=str(pathlib.Path(cmds_file).resolve()).replace("\\", "/"), AUDIO_LOG=base + ".tsv", AUDIO_QS=base + ".qs", AUDIO_PRE="%x" % LOAD_VOICES))


def read_wav(p):
    with wave.open(str(p)) as w:
        sr = w.getframerate()
        return sr, np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())


TAIL = 250   # the clip ends where the render last passes this (of 32767): the AvP clips use 40, a voice tail below 250 is inaudible under the game


def cut_clip(st, sr, a, b, max_s, rate=RATE):
    """Mono float clip: onset to the last sound (at most max_s long), lowered to `rate`, with a 3 ms fade at the end."""
    i, j = int(a * sr), int(min(b + 0.2, a + 6.0) * sr)
    m = st[i:j].astype(np.float64).mean(axis=1)
    loud = np.nonzero(np.abs(m) > BP.SILENT)[0]
    if not len(loud):
        return None
    end = np.nonzero(np.abs(m) > TAIL)[0]
    m = m[max(0, loud[0] - 16):(end[-1] if len(end) else loud[-1]) + 1]
    if max_s:
        m = m[:int(max_s * sr)]
    k = sr / rate
    h = BP.decimator(rate)
    h = np.sinc(2 * (0.45 * rate / sr) * (np.arange(63) - 31)) * np.hamming(63)
    h /= h.sum()
    y = np.convolve(m, h, mode="same")
    y = np.interp(np.arange(0, len(y) / k) * k, np.arange(len(y)), y)
    f = min(len(y) // 4, int(0.003 * rate))
    y[-f:] *= np.linspace(1, 0, f)
    return y


def build(out, assets):
    out, assets = pathlib.Path(out), pathlib.Path(assets)
    (assets / "wav").mkdir(parents=True, exist_ok=True)
    sr, st = read_wav(out / "render.wav")
    start, rows = {}, []
    for l in open(out / "render.tsv"):
        c, k, f, t = l.split()
        if k == "S":
            start[c] = float(t)
        elif k == "E":
            rows.append((int(c, 16), start[c], float(t)))
    by = {c: (a, b) for c, a, b in rows}
    blob, items = bytearray(), []
    for s in SOUNDS:
        a, b = by[s["cmd"]]
        y = cut_clip(st, sr, a, b, s.get("max_s", 0))
        if y is None:
            raise SystemExit("silent render for %s (cmd %x)" % (s["name"], s["cmd"]))
        pcm, tl = BP.to_pcm8(y)
        if len(blob) & 1:
            blob += bytes(1)
        items.append(dict(id=s["id"], name=s["name"], cmd=s["cmd"], prio=s["prio"], mask=s["mask"], where=s["where"], tl=tl, off=len(blob), n=len(pcm), seconds=round(len(pcm) / RATE, 3), role=s.get("role", "")))
        blob += pcm.tobytes()
        with wave.open(str(assets / "wav" / ("%02d_%s.wav" % (s["id"], s["name"]))), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes(np.clip(y, -32768, 32767).astype("<i2").tobytes())
    (assets / "wv_sound.bin").write_bytes(bytes(blob))
    (assets / "wv_sound.json").write_text(json.dumps(dict(rate=RATE, cmd_base=CMD_BASE, sounds=items, bytes=len(blob)), indent=1))
    return len(blob), items


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "render":
        render(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif c == "build":
        n, items = build(sys.argv[2], sys.argv[3])
        print(n, "bytes", len(items), "sounds")
    elif c == "list":
        for s in SOUNDS:
            print(s)
    else:
        raise SystemExit(__doc__)
