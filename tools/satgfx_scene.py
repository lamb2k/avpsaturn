#!/usr/bin/env python
"""Lane satgfx: build one standalone Saturn image per scene from a MAME dump, run it on Yaba, compare stills with MAME. Tier EMULATOR.
usage: satgfx_scene.py DUMPDIR N[,N...] [build-only]
Each N needs dumps at IRQ entries N and N+1 and the MAME still sN+2: on the board that picture is the list from N with layers from N+1.
All outputs are ROM-derived and stay under E:/AvP/learning/lane-satgfx/img. One emulator at a time; the shared ini is restored."""
import json, os, pathlib, re, shutil, struct, subprocess, sys, time
import numpy as np
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import satgfx_pack
from satgfx_ref import scenes, be
DEPS = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps")
JO = DEPS / "joengine/Compiler"
GCC = JO / "WINDOWS/bin/sh-elf-gcc.exe"
OBJCOPY = JO / "WINDOWS/bin/sh-elf-objcopy.exe"
MKISO = JO / "WINDOWS/Other Utilities/mkisofs.exe"
IP = JO / "COMMON/IP.BIN"
EXE = next((DEPS / "emulators").glob("yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34/**/yabasanshiro.exe"))
INI = pathlib.Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
BASE = pathlib.Path("E:/AvP/learning/lane-satgfx")
SRC = ROOT / "saturn/gfx"
W, H = 352, 224
os.environ["PATH"] = str(JO / "WINDOWS/bin") + os.pathsep + os.environ["PATH"]  # cc1 needs the DLLs beside gcc


def used_keys(a, b):
    """Exactly what the library looks up, for the object lists of both and the layers of b."""
    used = [set(), set(), set(), set()]
    for ob in (a.obj8,):
        n = 0
        while n < 0x400 and be(ob, n * 8 + 2) < 0x8000 and be(ob, n * 8 + 6) < 0xff00:
            o = n * 8
            yw, cw, aw = be(ob, o + 2), be(ob, o + 4), be(ob, o + 6)
            code = cw + ((yw & 0x6000) << 3)
            nx, ny = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1
            fx, fy = aw & 0x20, aw & 0x40
            for ty in range(ny):
                for tx in range(nx):
                    if fx or fy:
                        used[0].add(code + (nx - 1 - tx if fx else tx) + 0x10 * (ny - 1 - ty if fy else ty))
                    else:
                        used[0].add((code & ~15) + ((code + tx) & 15) + 0x10 * ty)
            n += 1
    F = 0xff8000
    g = lambda reg: (reg & 0xffc0) * 0x100 - 0x900000
    s = [(b.r(0xffee1a), b.r(0xffee1c)), (b.r(0xffee1e), b.r(0xffee20)), (b.r(0xffee22), b.r(0xffee24))]
    m1, m2, m3 = g(b.r(F + 0x24)), g(b.r(F + 0x26)), g(b.r(F + 0x28))
    x0, y0 = s[0][0] + 80, s[0][1] + 16
    for row in range(W and H // 8 + 1):
        for col in range(W // 8 + 1):
            c, r = ((x0 >> 3) + col) & 63, ((y0 >> 3) + row) & 63
            i = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6)
            used[1].add(be(b.gfx, m1 + i * 4) << 1 | ((i >> 5) & 1))
    y0 = s[1][1] + 16
    for row in range(H // 16 + 1):
        for c in range(64):
            r = ((y0 >> 4) + row) & 63
            i = (r & 0xf) + (c << 4) + ((r & 0x30) << 6)
            used[2].add(be(b.gfx, m2 + i * 4))
    x0, y0 = s[2][0] + 80, s[2][1] + 16
    for row in range(H // 32 + 1):
        for col in range(W // 32 + 1):
            c, r = ((x0 >> 5) + col) & 63, ((y0 >> 5) + row) & 63
            i = (r & 7) + (c << 3) + ((r & 0x38) << 6)
            used[3].add(be(b.gfx, m3 + i * 4) & 0x3fff)
    return used


def build(a, b, raw, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "ram.bin").write_bytes(b.ram)
    (out / "gfx.bin").write_bytes(b.gfx)
    (out / "obj.bin").write_bytes(a.obj8)
    data, secs = satgfx_pack.pack(raw, used_keys(a, b))
    (out / "pack.bin").write_bytes(data)
    flags = [*os.environ.get("SATGFX_CFLAGS", "").split(), "-O2", "-m2", "-fno-tree-loop-distribute-patterns", "-I", str(SRC)]
    subprocess.run([str(GCC), *flags, "-std=c90", "-Wall", "-Wextra", "-Werror", "-c", str(SRC / "sat_gfx.c"), "-o", "sat_gfx.o"], cwd=out, check=True)
    subprocess.run([str(GCC), *flags, "-c", str(SRC / "standalone_main.c"), "-o", "main.o"], cwd=out, check=True)
    subprocess.run([str(GCC), "-m2", "-nostartfiles", "-nostdlib", "-T", str(SRC / "standalone.ld"), "main.o", "sat_gfx.o", "-lgcc", "-Wl,-Map,game.map", "-o", "game.elf"], cwd=out, check=True)
    cd = out / "cd"
    cd.mkdir(exist_ok=True)
    subprocess.run([str(OBJCOPY), "-O", "binary", "game.elf", "cd/0.BIN"], cwd=out, check=True)
    shutil.copy(IP, out / "IP.BIN")
    for t in ("ABS.TXT", "BIB.TXT", "CPY.TXT"):
        (cd / t).write_text("satgfx\n")
    subprocess.run([str(MKISO), "-quiet", "-sysid", "SEGA SATURN", "-volid", "SATGFX", "-abstract", "ABS.TXT", "-biblio", "BIB.TXT", "-copyright", "CPY.TXT",
                    "-generic-boot", "IP.BIN", "-full-iso9660-filenames", "-o", "game.iso", "cd"], cwd=out, check=True)
    (out / "game.cue").write_text('FILE "game.iso" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
    return secs, len(data), (cd / "0.BIN").stat().st_size


def symbols(elf):
    out = {}
    for line in subprocess.run([str(JO / "WINDOWS/sh-elf/bin/nm.exe"), str(elf)], capture_output=True, text=True, check=True).stdout.splitlines():
        m = re.match(r"([0-9a-f]+) \w _(\w+)$", line)
        if m:
            out[m.group(2)] = int(m.group(1), 16)
    return out


STATS = ">I" + "H" * 14 + "I" * 6


def run(out, name):
    from capture_frontend_cram import Mcp
    while subprocess.run(["tasklist", "/FI", "IMAGENAME eq yabasanshiro.exe"], capture_output=True, text=True).stdout.lower().count("yabasanshiro.exe"):
        print("emulator busy, waiting", flush=True)
        time.sleep(10)
    original = INI.read_bytes()
    text = original.decode("latin-1")
    for key, value in (("Video\\VideoCore", "1"), ("Sound\\SoundCore", "0"), ("autostart", "true")):
        text = re.sub(rf"(?m)^{re.escape(key)}=.*$", (key + "=" + value).replace("\\", "\\\\"), text)
    INI.write_bytes(text.encode("latin-1"))
    proc = subprocess.Popen([str(EXE), "-nb", "-a", "-i", str(out / "game.cue")], cwd=str(out))
    syms = symbols(out / "game.elf")
    res = {}
    try:
        mcp = Mcp("http://127.0.0.1:9640/mcp")
        t = time.time()
        while True:
            try:
                mcp.initialize()
                break
            except Exception:
                if time.time() - t > 30:
                    raise
                time.sleep(0.5)
        t = time.time()
        done = 0
        while time.time() - t < 25:
            try:
                done = mcp.u32(syms["scene_done"])
            except RuntimeError:
                done = 0
            if done:
                break
            time.sleep(0.5)
        res["done"] = done
        time.sleep(1)
        mcp.call("framebuffer_screenshot", path=str(out / "yaba.png"))
        raw = mcp.read(syms["sat_gfx_stats"], struct.calcsize(STATS))
        res["ticks"] = [mcp.u32(syms["scene_ticks"]), mcp.u32(syms["scene_ticks"] + 4)]
        f = struct.unpack(STATS, raw)
        names = ["frames", "objects", "commands", "commands_peak", "uploads", "uploads_peak", "sprite_slots", "sprite_slots_peak", "layer_uploads",
                 "layer_writes", "s1_peak", "s2_peak", "s3_peak", "colours", "top_bank", "missing", "ref_cmd", "ref_spr", "ref_layer", "ref_bank", "nonmono"]
        res.update(dict(zip(names, f)))
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(15)
        # Lanes share this file: put the settings back as the campaign requires, whatever a stopped run left in it.
        text = original.decode("latin-1")
        for key, value in ((r"Video\VideoCore", "4"), (r"Sound\SoundCore", "1")):
            text = re.sub(rf"(?m)^{re.escape(key)}=.*$", (key + "=" + value).replace("\\", "\\\\"), text)
        INI.write_bytes(text.encode("latin-1"))
    return res


def compare(out, snap):
    m = Image.open(snap).convert("RGB").crop((16, 0, 368, 224))
    y = Image.open(out / "yaba.png").convert("RGB")
    size = y.size
    if size == (800, 612):  # the debug rig window: picture rows 52..560
        y = y.crop((0, 52, 800, 561))
    y = y.resize((W, H), Image.BOX)
    # The still is the rig's scaled window, so edges smear; a one pixel neighbourhood is the fair pixel test.
    am0 = np.array(m, int); ay0 = np.array(y, int)
    near = np.full(am0.shape[:2], 999)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near = np.minimum(near, np.abs(np.roll(np.roll(am0, dy, 0), dx, 1) - ay0).max(axis=2))
    am, ay = np.array(m, int), np.array(y, int)
    d = np.abs(am - ay).max(axis=2)
    pair = Image.new("RGB", (W * 2, H))
    pair.paste(m, (0, 0))
    pair.paste(y, (W, 0))
    pair.save(out / "pair.png")
    Image.fromarray((np.clip(d * 4, 0, 255)).astype(np.uint8)).save(out / "diff.png")
    return {"yaba_size": size, "over_16": int((d > 16).sum()), "over_48": int((d > 48).sum()), "pct_over_16": round(100 * float((d > 16).mean()), 2), "pct_over_48": round(100 * float((d > 48).mean()), 2), "pct_near_over_48": round(100 * float((near > 48).mean()), 3)}


def main():
    dump = BASE / sys.argv[1]
    ns = [int(x) for x in sys.argv[2].split(",")]
    raw = (BASE / "gfx.bin").read_bytes()
    all_s = {s.irq: s for s in scenes(dump / "scene.bin")}
    report = {}
    for n in ns:
        out = BASE / "img" / str(n)
        secs, packsize, binsize = build(all_s[n], all_s[n + 1], raw, out)
        r = {"pack_sections": secs, "pack_bytes": packsize, "image_bytes": binsize}
        if len(sys.argv) <= 3:
            r.update(run(out, n))
            r.update(compare(out, dump / "snap" / f"s{n + 2:05d}.png"))
        report[n] = r
        print(n, json.dumps(r), flush=True)
    (BASE / "img" / "report.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
