"""Music check of a disc (lane wv-sounds). usage: ymusic.py RUN CUE ELF [stay_seconds]
Boots CUE in my own Yaba (port 9722), walks title -> character select (the Wolverine slot) -> pick -> stage, polling about every 0.25 s: vblank, home screen, stage word, sat_audio_stats
(commands, music_started, cd_sent, last_command), the CD block status (CR1 high nibble, 3 = playing) and the SCSP key-on bit of slots 0..31. Also logs every command number the
player receives (from the commands counter). Output E:/AvP/learning/lane-wv-sounds/yaba/RUN.music.json and RUN.music.txt (the changes)."""
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, "E:/AvP/worktrees/wv-sounds/tools/wolverine")
import wv_yaba as W

RUN, CUE, ELF = sys.argv[1], sys.argv[2], sys.argv[3]
STAY = float(sys.argv[4]) if len(sys.argv) > 4 else 8
WARP = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0
STAGE_SECS = float(sys.argv[6]) if len(sys.argv) > 6 else 10
OUT = pathlib.Path("E:/AvP/learning/lane-wv-sounds/yaba")
OUT.mkdir(exist_ok=True)
raw = OUT / f"{RUN}.raw"
txt = open(OUT / f"{RUN}.music.txt", "w")
samples, last = [], None
cmdlast, cmdlog = [-1], []
W.setup(CUE)
proc = W.start(raw)
y = W.Y(proc, ELF, f"AvP SOUNDS: {RUN} music check [port 9722]")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); txt.write(s + "\n"); txt.flush()


def sample(tag=""):
    global last
    st = y.read(y.syms["sat_audio_stats"], 40)
    f = "commands sfx_started sfx_refused sfx_unknown music_started controls frames cd_sent cd_status last_command".split()
    d = {k: int.from_bytes(st[4 * i:4 * i + 4], "big") for i, k in enumerate(f)}
    try:
        cr1 = int.from_bytes(y.read(0x25890018, 2), "big")
    except Exception:
        cr1 = -1
    slots = 0
    try:
        for n in (range(32) if tag or (len(samples) % 8 == 0) else ()):
            if int.from_bytes(y.read(0x25b00000 + 0x20 * n, 2), "big") & 0x800:
                slots |= 1 << n
    except Exception:
        slots = -1
    s = dict(t=round(time.time() - t0, 1), v=y.v(), screen=y.sym("sat_home_screen") if "sat_home_screen" in y.syms else -1, stage=y.ram16(0x81e8), tag=tag,
             commands=d["commands"], music_started=d["music_started"], cd_sent=d["cd_sent"], last=hex(d["last_command"]), sfx=d["sfx_started"], unk=d["sfx_unknown"], cd_state=(cr1 >> 8) & 15 if cr1 >= 0 else -1, keyon=hex(slots))
    s['raw'] = raw.stat().st_size if raw.exists() else 0
    samples.append(s)
    if d['commands'] != cmdlast[0]:
        cmdlast[0] = d['commands']; cmdlog.append((round(time.time() - t0, 2), y.v(), d['commands'], hex(d['last_command']), d['music_started'], d['cd_sent'], s['raw']))
        L('CMD', cmdlog[-1])
    key = (s["commands"], s["music_started"], s["cd_sent"], s["cd_state"], s["screen"], s["stage"], tag)
    if key != last:
        last = key
        L(json.dumps(s))
    (OUT / f"{RUN}.music.json").write_text(json.dumps(samples))
    return s


t0 = time.time()
try:
    assert y.wait(lambda: y.v() > 20, 400), "no boot"
    lastp = 0.0; picked = False; selsince = None; seen_title = False
    while time.time() - t0 < 900:
        now = time.time()
        a = y.ram(0x8000, 0x400)
        sc = y.sym("sat_home_screen")
        sample()
        if not seen_title:   # press nothing until the title menu is up (3e loads for 30 to 50 s with the vblank count at 0)
            if sc == 1:
                seen_title = True; sample('title menu')
            else:
                time.sleep(0.5); continue
        if sc in (1, 3):
            if now - lastp > 1.5:
                lastp = now; y.pulse("start", 0.1)
            continue
        sel = a[1] == 2 and not a[0x380] and not a[0x1e8] and not a[0x1e9] and a[0x1b0] == 0
        if sel:
            if selsince is None:
                selsince = now; sample("select screen reached"); y.shot(OUT / f"{RUN}_select.png")
            if now - selsince < STAY:
                time.sleep(0.25); continue
            if a[0x1cc] != 2 and now - lastp > 0.5:
                lastp = now; y.pulse("right", 0.08)
            elif a[0x1cc] == 2 and now - lastp > 0.7:
                lastp = now
                if not picked:
                    picked = True; sample("pick")
                    if WARP:
                        y.wsym('sat_home_warp', [0, 0, 0, WARP])
                y.pulse("start", 0.1)
            continue
        if WARP and picked and y.ram16(0x81e8) == WARP:
            time.sleep(2); break
        if a[1] == 2 and a[0x380] and a[0x1e9] and a[0x1b0] == 0 and a[0x384] == 2 and a[0x384:0x387].hex() == "020000":
            break
        if a[0x1b0] == 0 and not a[0x380] and now - lastp > 0.7:
            lastp = now; y.pulse("start", 0.1)
        time.sleep(0.1)
    sample("stage reached"); y.shot(OUT / f"{RUN}_stage.png")
    for _ in range(int(STAGE_SECS * 4)):
        time.sleep(0.25); sample("stage")
finally:
    sample("end"); y.stop()
