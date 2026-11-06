#!/usr/bin/env python
"""Item 26: the package for a real Saturn with a 4 MB cart. Builds the image with the frame-cost bars on, then lays out data track, CD audio, cue, hashes and the test steps.
usage: build_package.py WORK OUT   WORK as saturn/rt/build.py wants it, plus WORK/audio/pack.bin and WORK/audio/music/t*.raw. OUT is under E:/AvP, never git: everything in it is ROM-derived.
Raw audio tracks are 44.1 kHz stereo little-endian as build_pack.py writes them; the cue names them BINARY, which burn tools and optical drive emulators read as CD audio in this byte order."""
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
work, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
env = dict(os.environ, KERNEL_CFLAGS=(os.environ.get("KERNEL_CFLAGS", "") + " -DSAT_READOUT").strip())
subprocess.run([sys.executable, str(REPO / "saturn/rt/build.py"), str(work)], check=True, env=env)
out.mkdir(parents=True, exist_ok=True)
for f in out.iterdir():
    if f.is_file():
        f.unlink()
shutil.copy(work / "sat.iso", out / "avp_saturn.iso")
dma = dict(env, KERNEL_CFLAGS=env["KERNEL_CFLAGS"] + " -DSAT_TILE_DMA")   # second data track: tile uploads by SCU DMA, for the on/off decision
subprocess.run([sys.executable, str(REPO / "saturn/rt/build.py"), str(work)], check=True, env=dma)
shutil.copy(work / "sat.iso", out / "avp_saturn_dma.iso")
cue = 'FILE "avp_saturn.iso" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n'
for f in sorted((work / "audio/music").glob("t*.raw")):
    shutil.copy(f, out / f.name)
    cue += f'FILE "{f.name}" BINARY\n  TRACK {int(f.name[1:3]):02d} AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n'
(out / "avp_saturn.cue").write_text(cue, newline="\n")
(out / "avp_saturn_dma.cue").write_text(cue.replace("avp_saturn.iso", "avp_saturn_dma.iso"), newline="\n")
shutil.copy(HERE / "HARDWARE_TEST.md", out / "HARDWARE_TEST.md")
commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(REPO), "status", "--short", "saturn"], capture_output=True, text=True).stdout.strip()
lines = [f"commit {commit}{' (saturn/ has uncommitted changes)' if dirty else ''}"]
for f in sorted(out.iterdir()):
    if f.name != "SHA256SUMS.txt":
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
(out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", newline="\n")
print("\n".join(lines))
print("bytes", sum(f.stat().st_size for f in out.iterdir()))
