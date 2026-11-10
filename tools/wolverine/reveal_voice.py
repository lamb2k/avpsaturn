#!/usr/bin/env python
"""Wolverine's "Berserker Barrage!" voice for the reveal (saturn/rt/reveal.c, disc file RVVOICE.BIN), cut from the owner's MSHvSF QSound sample ROM on this PC.
ROM-derived: the output stays out of git (build.py reads REVEAL_VOICE or GUEST_ASSETS/reveal_voice.bin and the disc image takes it).
usage:
  reveal_voice.py dump  WORKDIR                       run MAME 0.289 (mshvsf, no sound, no video) through tools/wolverine/mame_voice.lua: WORKDIR/qsound.bin, the 8 MB sample ROM
  reveal_voice.py cut   WORKDIR OUT.bin               cut the clip (CLIP below) from WORKDIR/qsound.bin, resample to 22050 Hz, 8 bit signed, write OUT.bin
  reveal_voice.py build OUT.bin [WORKDIR]             dump (when WORKDIR/qsound.bin is not there yet) then cut
  reveal_voice.py intro SOUND_ASSETS OUT.bin          THE REVEAL'S VOICE (owner 11-10): Wolverine's round-entrance line "Let's go, bub." (arcade sound command 0x207, 0.9 s), taken from the clip the
                                                      wv-sounds lane rendered through the real Z80 driver and QSound (tools/wolverine/wv_sound.py, voice set loaded with 0x484 first, so the whole line, not
                                                      only the first QSound clip): SOUND_ASSETS is its asset directory (wv_sound.json and wv_sound.bin, 8 bit signed mono PCM at 11025 Hz, level in tl).
env for dump: MSHVSF_REPO (the repo with tools/run_mshvsf_mame.py and the ROM set), MSHVSF_PY (its python).
The clip is QSound sample ROM bank/start/end as the Z80 sound driver starts it: sound command CMD of the arcade's table, voice start (bank, address, end) read from the DSP writes
(tools/wolverine/mame_voicescan.lua sends every command in turn). QSound plays 8 bit signed samples at 24038 Hz when its rate register is 0x1000.
File format (big endian): 'RVV1', u32 samples, u8 SCSP total level (0 loudest, 0.375 dB a step), u8 octave nibble (0xe = 11025 Hz, 0xf = 22050 Hz; 0 = not set, read as 0xf, which is what wv_sound.py reveal writes: 8 reserved bytes), 6 reserved bytes, then the samples
(PCM 8 bit signed, played by SCSP slot 18)."""
import os
import pathlib
import struct
import subprocess
import sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
QSOUND_HZ = 24038.0
OUT_HZ = 22050
# (bank, first address, end address) in the sample ROM: byte offset = (bank & 0x7f) << 16 | address. The clip is NOT identified yet (docs/notes/AVP_WOLVERINE_REVEAL_20261109.md, "Voice"):
# set REVEAL_VOICE_CLIP=BANK:START:END (hex, e.g. 20:b400:e7ff) to cut one, or fill CLIP in here once the owner has picked it by ear. With neither, no voice file is made and the reveal is silent.
CLIP = None
if os.environ.get("REVEAL_VOICE_CLIP"):
    CLIP = tuple(int(x, 16) for x in os.environ["REVEAL_VOICE_CLIP"].split(":"))
PEAK = 120          # the clip is scaled to this peak (of 127) so the SCSP plays it at full level without clipping
FADE_MS = 4         # a 4 ms fade at both ends takes the click out


def dump(work):
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    repo = pathlib.Path(os.environ.get("MSHVSF_REPO", "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-MSHvSF"))
    py = os.environ.get("MSHVSF_PY", str(pathlib.Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"))
    seq = work / "empty_seq.txt"
    seq.write_text("")
    env = dict(os.environ, WV_ROOT=str(work).replace("\\", "/"), WV_SEQ=str(seq).replace("\\", "/"), WV_LAST="30")
    subprocess.run([py, "tools/run_mshvsf_mame.py", "--", "mshvsf", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo",
                    "-autoboot_script", str(HERE / "mame_voice.lua").replace("\\", "/")], cwd=repo, env=env, check=True, capture_output=True)
    if not (work / "qsound.bin").exists():
        raise SystemExit("NO-GO: MAME did not write qsound.bin")


def cut(work, out):
    rom = np.fromfile(pathlib.Path(work) / "qsound.bin", dtype=np.int8)
    if not CLIP:
        raise SystemExit("no clip chosen: set REVEAL_VOICE_CLIP=BANK:START:END (hex) or CLIP in reveal_voice.py")
    bank, a, e = CLIP
    clip = rom[(bank & 0x7f) << 16 | a:(bank & 0x7f) << 16 | e].astype(np.float64)
    n = int(len(clip) * OUT_HZ / QSOUND_HZ)
    x = np.interp(np.linspace(0, len(clip) - 1, n), np.arange(len(clip)), clip)
    x -= x.mean()
    x *= PEAK / max(1.0, np.abs(x).max())
    f = int(OUT_HZ * FADE_MS / 1000)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    pcm = np.clip(np.rint(x), -128, 127).astype(np.int8).tobytes()
    if len(pcm) % 2:
        pcm += b"\0"
    pathlib.Path(out).write_bytes(b"RVV1" + struct.pack(">IBB", len(pcm), 0, 0xf) + bytes(6) + pcm)
    return dict(samples=len(pcm), seconds=len(pcm) / OUT_HZ, file_bytes=16 + len(pcm))


def intro(assets, out):
    """the INTRO clip of the wv-sounds lane's assets as RVVOICE.BIN, at its own rate and level"""
    import json
    assets = pathlib.Path(assets)
    j = json.loads((assets / "wv_sound.json").read_text())
    blob = (assets / "wv_sound.bin").read_bytes()
    s = next(x for x in j["sounds"] if x["name"] == "INTRO")
    assert j["rate"] == 11025, "the reveal plays 11025 Hz clips (octave nibble 0xe)"
    pcm = blob[s["off"]:s["off"] + s["n"]]
    if len(pcm) % 2:
        pcm += b"\0"
    pathlib.Path(out).write_bytes(b"RVV1" + struct.pack(">IBB", len(pcm), s["tl"], 0xe) + bytes(6) + pcm)
    return dict(command=hex(s["cmd"]), samples=len(pcm), seconds=round(len(pcm) / 11025, 3), tl=s["tl"], file_bytes=16 + len(pcm))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "dump":
        dump(sys.argv[2])
    elif cmd == "cut":
        print(cut(sys.argv[2], sys.argv[3]))
    elif cmd == "intro":
        print(intro(sys.argv[2], sys.argv[3]))
    elif cmd == "build":
        work = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else pathlib.Path(sys.argv[2]).parent / "voice_work")
        if not (work / "qsound.bin").exists():
            dump(work)
        print(cut(work, sys.argv[2]))
    else:
        raise SystemExit(__doc__)
