#!/usr/bin/env python
"""Standalone proof of the audio library. All output stays in WORK; never commit.
usage: standalone.py build WORK SCRIPT     SCRIPT: lines "frame sound voice sweep" (hex after the frame)
       standalone.py run WORK [seconds]    debug-rig Yaba under the lock; counters, chip trace and SCSP RAM over MCP. Tier: EMULATOR
       standalone.py compare WORK          what the chip trace and RAM say plays (MODELLED mix) against WORK/ref.wav (MAME, same script)
This Yaba setup gives no audio output to record, for any disc (see docs/notes/AVP_NOTES_AUDIO.md), so the comparison stops at the SCSP's inputs."""
import json, os, pathlib, shutil, socket, struct, subprocess, sys, time, wave
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
JO = pathlib.Path("E:/AvP/worktrees/saturn-hw/.deps")
BIN = JO / "joengine/Compiler/WINDOWS/bin"
OBJ = JO / "joengine/Compiler/WINDOWS/sh-elf/bin"
MKISOFS = JO / "joengine/Compiler/WINDOWS/Other Utilities/mkisofs.exe"
EXE = pathlib.Path(os.environ.get("YABA_EXE", JO / "emulators/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-d7767591/yabasanshiro.exe"))
INI = pathlib.Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
STATS = "commands sfx_started sfx_refused sfx_unknown music_started controls frames cd_sent cd_status last_command".split()
EVENT = "on_frame off_frame slot word0 sa_low tl pan position_max".split()
CLIP_BASE = 0x20
SCSP_RAM = 0x25A00000
MAME_FPS = 59.637
RATE = 44100


def sh(cmd, cwd=None):
    env = dict(os.environ, PATH=str(BIN) + os.pathsep + os.environ["PATH"])
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, cwd=cwd, env=env)
    if r.returncode:
        raise SystemExit(" ".join(map(str, cmd)) + "\n" + r.stdout[-3000:] + r.stderr[-3000:])
    return r.stdout


def build(work, script):
    rows = [l.split() for l in open(script) if l.strip()]
    (work / "script.inc").write_text("".join(f"{{{r[0]}UL,0x{r[1]}UL,0x{r[2]}UL,0x{r[3]}UL}},\n" for r in rows))
    elf = work / "audio.elf"
    sh([BIN / "sh-elf-gcc.exe", "-m2", "-mb", "-O2", *os.environ.get("AUDIO_CFLAGS", "").split(), "-std=gnu89", "-Wall", "-Wextra", "-Werror", "-fno-builtin", "-nostdlib", "-T", HERE / "standalone.ld",
        "-I", work, "-I", HERE, "-Wa,-I" + str(work), HERE / "standalone_main.c", HERE / "sat_audio.c", "-lgcc", "-o", elf, f"-Wl,-Map={work / 'audio.map'}"])
    iso_dir = work / "disc"
    shutil.rmtree(iso_dir, ignore_errors=True)
    iso_dir.mkdir()
    sh([BIN / "sh-elf-objcopy.exe", "-O", "binary", elf, iso_dir / "0.BIN"])
    for n in ("ABS.TXT", "CPY.TXT", "BIB.TXT"):
        shutil.copy(REPO / "cd" / n, iso_dir / n)
    ip = work / "IP.BIN"
    sh([sys.executable, REPO / "tools/build_loader_ip.py", JO / "joengine/Compiler/COMMON/IP.BIN", ip])
    iso = work / "audio.iso"
    sh([MKISOFS, "-quiet", "-sysid", "SEGA SATURN", "-volid", "AVP_AUDIO", "-generic-boot", ip, "-full-iso9660-filenames",
        "-abstract", "ABS.TXT", "-copyright", "CPY.TXT", "-biblio", "BIB.TXT", "-o", iso, "."], cwd=iso_dir)
    cue = f'FILE "{iso}" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n'
    for f in sorted((work / "music").glob("t*.raw")):
        cue += f'FILE "{f}" BINARY\n  TRACK {int(f.name[1:3]):02d} AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n'
    (work / "audio.cue").write_text(cue)
    print("image", (iso_dir / "0.BIN").stat().st_size, "rows", len(rows))


def port_busy():
    s = socket.socket()
    s.settimeout(0.3)
    busy = s.connect_ex(("127.0.0.1", 9640)) == 0
    s.close()
    return busy


def words(m, addr, count):
    return list(struct.unpack(f">{count}I", m.read(addr, 4 * count)))


def run(work, secs):
    from capture_frontend_cram import Mcp
    syms = {}
    for l in sh([OBJ / "nm.exe", work / "audio.elf"]).splitlines():
        p = l.split()
        if len(p) == 3:
            syms[p[2].lstrip("_")] = int(p[0], 16)
    while port_busy():
        print("Yaba lock held, waiting", flush=True)
        time.sleep(10)
    orig = INI.read_bytes()
    want = {"Video\\VideoCore": "1", "Sound\\SoundCore": "0", "General\\CdRomISO": str(work / "audio.cue").replace("\\", "/"), "autostart": "true",
            "General\\EnableEmulatedBios": "true"}
    lines = [f"{l.split('=')[0]}={want[l.split('=')[0]]}" if l.split("=")[0] in want else l for l in orig.decode("latin-1").splitlines()]
    proc = None
    try:
        INI.write_bytes(("\n".join(lines) + "\n").encode("latin-1"))
        proc = subprocess.Popen([str(EXE)], cwd=str(EXE.parent))
        m = Mcp("http://127.0.0.1:9640/mcp")
        t0 = time.time()
        while True:
            try:
                m.initialize()
                break
            except Exception:
                if time.time() - t0 > 30:
                    raise
                time.sleep(0.3)
        t1 = time.time()
        while time.time() - t1 < secs:
            time.sleep(4)
            st = dict(zip(STATS, words(m, syms["sat_audio_stats"], len(STATS))))
            print(round(time.time() - t1), json.dumps(st), flush=True)
        n = words(m, syms["audio_event_count"], 1)[0]
        ev = [dict(zip(EVENT, words(m, syms["audio_events"] + i * 4 * len(EVENT), len(EVENT)))) for i in range(n)]
        out = dict(stats=st, events=ev, init_ok=words(m, syms["audio_init_ok"], 1)[0], done=words(m, syms["audio_done"], 1)[0],
                   cost_max_ticks=words(m, syms["audio_cost_max"], 1)[0], cd_status_frames=words(m, syms["audio_cd_status_frames"], 16),
                   cd_fad_first=words(m, syms["audio_cd_fad_first"], 1)[0], cd_fad_last=words(m, syms["audio_cd_fad_last"], 1)[0], cd_track=words(m, syms["audio_cd_track"], 1)[0],
                   cd_level=int.from_bytes(m.read(0x25B00000 + 0x20 * 16 + 0x16, 2), "big"))
        pack = (work / "pack.bin").read_bytes()
        keep = 12 + 16 * (int.from_bytes(pack[4:6], "big") + int.from_bytes(pack[6:8], "big"))
        clip = pack[keep:]
        ram = b"".join(m.read(SCSP_RAM + CLIP_BASE + a, min(0x4000, len(clip) - a)) for a in range(0, len(clip), 0x4000))
        (work / "scsp_ram.bin").write_bytes(ram)
        out["scsp_ram_equals_pack"] = ram[:len(clip) & ~1] == clip[:len(clip) & ~1]
        (work / "trace.json").write_text(json.dumps(out, indent=0))
        print(json.dumps({k: v for k, v in out.items() if k != "events"}))
        for e in ev:
            print(e)
    finally:
        if proc:
            proc.kill()
            proc.wait(10)
        INI.write_bytes(orig)


def envelope(x, rate, ms=10):
    import numpy as np
    n = int(rate * ms / 1000)
    m = len(x) // n
    return np.sqrt((x[:m * n] ** 2).mean(axis=1).reshape(m, n).mean(axis=1) + 1e-6)


def compare(work):
    """Per event: the MODELLED mix from the chip trace, against MAME, in 10 ms loudness and in level."""
    import numpy as np
    with wave.open(str(work / "ref.wav")) as w:
        ref = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2).astype(float)
    ref = ref[int(float(open(work / "ref.tsv").readline().split()[1]) * RATE):]
    tr = json.loads((work / "trace.json").read_text())
    ram = np.frombuffer((work / "scsp_ram.bin").read_bytes(), dtype=np.int8).astype(float)
    pack = json.loads((work / "pack.json").read_text())
    by_off = {}
    for s in pack["sfx"]:
        by_off.setdefault(s["off"], []).append(s)
    model = np.zeros_like(ref)
    rows = []
    for e in tr["events"]:
        sa = (((e["word0"] & 15) << 16) | e["sa_low"]) - CLIP_BASE
        same = by_off[sa]
        clip = next((s for s in same if s["tl"] == e["tl"]), same[0])
        at = int((e["on_frame"] - 1) / MAME_FPS * RATE)   # the script's frame numbers run on both sides
        stop = int((e["off_frame"] - 1) / MAME_FPS * RATE) if e["off_frame"] else len(model)
        y = np.repeat(ram[sa:sa + clip["n"]], 4)[:max(0, stop - at)]
        gain = 32767 / 127 * 10 ** (-e["tl"] * 0.375 / 20)
        pan = (e["pan"] >> 8) & 31
        cut = 10 ** (-3 * (pan & 15) / 20)
        n = min(len(y), len(model) - at)
        if n <= 0:
            continue
        model[at:at + n, 0] += y[:n] * gain * (1.0 if pan & 16 else cut)
        model[at:at + n, 1] += y[:n] * gain * (cut if pan & 16 else 1.0)
        rows.append((clip["cmd"], e["slot"], e["on_frame"], at, n, e["position_max"]))
    e_r, e_m = envelope(ref, RATE), envelope(model, RATE)
    print("sound slot on_frame position_max env_corr level_dB onset_ms   (MODELLED mix vs MAME)")
    corr = []
    for cmd, slot, f, at, n, pos in rows:
        i, j = at * 100 // RATE, (at + n) * 100 // RATE
        lead = min(i, 30)
        x, y = e_r[i - lead:j + 30], e_m[i:j]
        if len(y) < 5 or len(x) < len(y):
            continue
        best = max(range(len(x) - len(y) + 1), key=lambda d: float(np.dot(x[d:d + len(y)], y)))
        xx = x[best:best + len(y)]
        c = float(np.corrcoef(xx, y)[0, 1])
        corr.append(c)
        print(f"{cmd:4x} {slot:2d} {f:5d} {pos:2d} {c:.3f} {20 * np.log10(y.max() / max(1, xx.max())):+.1f} {(best - lead) * 10:+d}")
    print("median env_corr", round(float(np.median(corr)), 3), "events", len(corr))


if __name__ == "__main__":
    work = pathlib.Path(sys.argv[2])
    if sys.argv[1] == "build":
        build(work, sys.argv[3])
    elif sys.argv[1] == "run":
        run(work, float(sys.argv[3]) if len(sys.argv) > 3 else 40)
    else:
        compare(work)
