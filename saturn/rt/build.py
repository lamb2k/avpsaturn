#!/usr/bin/env python
"""Build the Saturn image of the lifted game. Everything ROM-derived stays in the work directory, never in git.
usage: build.py [WORK]   default E:/AvP/learning/lane-satrt, which holds src/c*.c, dispatch.inc, rt.bin, opx.bin, opx.json, heat.json (tools/satint_merge.py), pack.bin, pack_hole.bin (tools/satint_pack.py).
env: KERNEL_CFLAGS, LIFT_OPT (-Os; -O2 overflows work RAM), JO (Jo Engine root)."""
import concurrent.futures as cf
import json
import os
import pathlib
import re
import shutil
import subprocess
import time
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
WORK = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "E:/AvP/learning/lane-satrt")
JO = pathlib.Path(os.environ.get("JO", "E:/AvP/worktrees/saturn-hw/.deps/joengine"))
BIN = JO / "Compiler/WINDOWS/bin"
GCC, OBJCOPY = [str(BIN / f"sh-elf-{t}.exe") for t in ("gcc", "objcopy")]
NM, OBJDUMP = [str(JO / f"Compiler/WINDOWS/sh-elf/bin/{t}.exe") for t in ("nm", "objdump")]
os.environ["PATH"] = str(BIN) + os.pathsep + os.environ["PATH"]   # compiler DLLs
MKISOFS = str(JO / "Compiler/WINDOWS/Other Utilities/mkisofs.exe")
SGL = JO / "Compiler/COMMON/SGL_302j"
OPT = os.environ.get("LIFT_OPT", "-Os")
CF = ["-m2", "-mb", "-fno-strict-aliasing", "-ffixed-r14", "-w", "-fno-builtin", "-I", str(HERE)]
GEN, OBJ, ISO = WORK / "gen", WORK / f"obj{OPT}", WORK / "disc"
for d in (GEN, OBJ, ISO):
    d.mkdir(parents=True, exist_ok=True)
HW_BASE, HW_LIMIT, LW_BASE, LW_LIMIT = 0x06014000, 0x06100000, 0x00200000, 0x00300000
HW_RESERVED = 0x10000 + 16 * 4096 + 8192 + 16384 + 0x8000 + 0x8000   # game RAM, stacks, kernel, graphics tables and code
LW_RESERVED = 0x20000 + 0x4000 + 0xe400   # graphics RAM, lifted bss, layer shadows, blank tags
NATIVE = ("41ca", "42e4")   # EEPROM block read and write
CART = dict(ROMB=0x02400000, OPX=0x02600000, SAT_SINK=0x02638000, SAT_OBJ=0x02648000, SAT_PACK=0x0264c000)
CART_END = 0x02800000
OPX_MAX = 0x38000
COLD2 = (0x0253f000, 116 * 1024)   # a ROM stretch the Round 1 route never read: lifted code of a cold chunk fits here
HOLE_ROM = 0x198000  # pack_hole.bin


OPMAP = json.loads((WORK / "opx.json").read_text())


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(" ".join(map(str, cmd)) + "\n" + r.stdout[-3000:] + r.stderr[-3000:])
    return r.stdout


def update(path, text):
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
    return path


def opx_rewrite(m):
    paren = "((" if m[0].count("(") == 2 else "("
    return f"OP{m[1]}{paren}0x{OPMAP[hex(int(m[2], 16))]:x}u"


def gen_sources():
    out = []
    for s in sorted((WORK / "src").glob("c*.c"), key=lambda p: int(p.stem[1:])):
        t = s.read_text()
        a, b = t.index("#else\nregister Cpu *R"), t.index("#define SHL8(")
        t = t[:a] + '#else\n#include "lift_target.h"\n#endif\n' + t[b:]
        t = re.sub(r"\bOP(8|16|32)\(\(?0x([0-9a-f]+)u", opx_rewrite, t)
        for n in NATIVE:   # replaced natively in kernel.c; the lifted body stays linked as lifted_NNN
            t = t.replace(f"void f_{n}(void){{", f"void lifted_{n}(void){{")
        out.append(update(GEN / s.name, t))
    d = re.sub(r'void f_([0-9a-f]+)\(void\)\{puts\("MISSING [0-9a-f]+"\);fflush\(stdout\);exit\(3\);\}',
               lambda m: f"void f_{m[1]}(void){{sat_fatal(0xe9,0x{m[1]}u);}}", (WORK / "dispatch.inc").read_text())
    out.append(update(GEN / "dispatch.c", "typedef unsigned int u32;extern void sat_fatal(u32,u32);\n" + d +
                      "void f_dispatch(u32 a){VF f=lookup(a);if(!f)sat_fatal(0xe1,a);f();}\n"))
    seed = WORK / "golden_seed.bin"   # 16 bytes the skipped hardware test leaves at 0xff0e90, from the golden dump
    if not seed.exists():
        with open("E:/AvP/learning/mame/golden_c/probe.tsv", "rb") as f:
            f.seek(72 + 0xe90)
            seed.write_bytes(f.read(16))
    update(GEN / "seed.inc", ",".join(str(x) for x in seed.read_bytes()))
    save = WORK / "save_seed.bin"   # settings block the arcade keeps in EEPROM, from the golden dump
    if not save.exists():
        with open("E:/AvP/learning/mame/golden_c/probe.tsv", "rb") as f:
            f.seek(72 + 0xef0)
            save.write_bytes(f.read(0x80))
    update(GEN / "save_seed.inc", ",".join(str(x) for x in save.read_bytes()))
    return out


def cc(src, obj, extra=()):
    newest = max(src.stat().st_mtime, (HERE / "lift_target.h").stat().st_mtime)
    if src.name in ("kernel.c", "pad.c", "sat_gfx.c"):
        newest = max(newest, (HERE / "sat_rt.h").stat().st_mtime, time.time() if os.environ.get("KERNEL_CFLAGS") else 0)
    if src.name == "sat_gfx.c":
        newest = max(newest, (src.parent / "sat_gfx.h").stat().st_mtime)
    if not obj.exists() or obj.stat().st_mtime < newest:
        sh([GCC, *CF, *extra, "-c", src, "-o", obj])
    return obj


def code_size(o):
    rows = (l.split() for l in sh([OBJDUMP, "-h", o]).splitlines())
    return sum(int(r[2], 16) for r in rows if len(r) > 3 and r[1].startswith((".text", ".rodata", ".data")))


def main():
    gen = gen_sources()
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        objs = list(ex.map(lambda s: cc(s, OBJ / (s.stem + ".o"), [OPT]), gen))
    gfx_dir = REPO / "saturn/gfx"
    gfx = [gfx_dir / "sat_gfx.c"]
    own = [cc(HERE / "ctx.s", OBJ / "ctx.o"), cc(HERE / "kernel.c", OBJ / "kernel.o", ["-O2", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()), cc(HERE / "present.c", OBJ / "present.o", ["-O2"]), cc(HERE / "pad.c", OBJ / "pad.o", ["-O2"] + os.environ.get("KERNEL_CFLAGS", "").split())]
    own += [cc(s, OBJ / f"gfx_{s.stem}.o", ["-O2", "-I", gfx_dir] + os.environ.get("KERNEL_CFLAGS", "").split()) for s in gfx]
    sizes = {o: code_size(o) for o in objs}
    # Hottest chunks in high work RAM, then low work RAM; the coldest run from the cart. Heat comes from the MAME route.
    heat = json.loads((WORK / "heat.json").read_text())
    objs_o = sorted(objs, key=lambda o: -heat.get(o.stem, 1 << 40))
    room_hw = HW_LIMIT - HW_BASE - HW_RESERVED
    room_lw = LW_LIMIT - LW_BASE - LW_RESERVED
    hw, lw, cold = [], [], []
    used = usedl = 0
    for o in objs_o:
        if used + sizes[o] <= room_hw:
            hw.append(o); used += sizes[o]
        elif usedl + sizes[o] <= room_lw:
            lw.append(o); usedl += sizes[o]
        else:
            cold.append(o)
    pack_size = (WORK / "pack.bin").stat().st_size
    cold1_at = (CART["SAT_PACK"] + pack_size + 3) & ~3
    cold2 = sorted((o for o in cold if sizes[o] <= COLD2[1]), key=lambda o: -sizes[o])[:1]
    cold1 = [o for o in cold if o not in cold2]
    print("placement", {"hw": len(hw), "lw": [o.stem for o in lw], "cold1": [(o.stem, sizes[o], heat.get(o.stem)) for o in cold1], "cold2": [(o.stem, sizes[o], heat.get(o.stem)) for o in cold2]})
    inp = lambda l, s: "\n".join(f'    "{o.as_posix()}"({s})' for o in l)
    tx = ".text .text.* .rodata .rodata.* .data .data.*"
    ld = f"""ENTRY(_sat_start)
SECTIONS {{
  .hw {HW_BASE:#x} : {{
{inp(own, '.text .text.*')}
{inp(hw, tx)}
{inp(own, '.rodata .rodata.* .data .data.*')}
    . = ALIGN(4);
  }}
  .hwbss (NOLOAD) : {{
    _sat_bss_start = .;
{inp(own, '.bss COMMON')}
{inp(hw, '.bss COMMON')}
    . = ALIGN(4);
    _sat_bss_end = .;
  }}
  .cold1 {cold1_at:#x} : {{
{inp(cold1, tx)}
    . = ALIGN(4);
    _sat_cold1_end = .;
  }}
  .cold2 {COLD2[0]:#x} : {{
{inp(cold2, tx)}
    . = ALIGN(4);
    _sat_cold2_end = .;
  }}
  .lw {LW_BASE:#x} : {{
    *(.text .text.* .rodata .rodata.* .data .data.*)
    . = ALIGN(4);
  }}
  .lwbss (NOLOAD) : {{ _sat_lw_bss_start = .; *(.lwgfx) *(.bss COMMON) . = ALIGN(4); _sat_lw_bss_end = .; }}
  /DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
""" + "".join(f"_{k} = {v:#x};\n" for k, v in CART.items())
    (WORK / "sat.ld").write_text(ld)
    elf = WORK / "sat.elf"
    sh([GCC, "-m2", "-mb", "-nostdlib", "-T", WORK / "sat.ld", *own, *objs, "-lgcc", "-o", elf, f"-Wl,-Map={WORK / 'sat.map'}"])
    sh([OBJCOPY, "-O", "binary", "-j", ".hw", elf, ISO / "HW.BIN"])
    sh([OBJCOPY, "-O", "binary", "-j", ".lw", elf, ISO / "LW.BIN"])
    syms = {p[2]: int(p[0], 16) for p in (l.split() for l in sh([NM, elf]).splitlines()) if len(p) == 3}
    shutil.copy(WORK / "pack.bin", ISO / "PACK.BIN")
    shutil.copy(WORK / "opx.bin", ISO / "OPX.BIN")
    if (WORK / "opx.bin").stat().st_size > OPX_MAX:
        raise SystemExit("NO-GO: store past its room")
    sh([OBJCOPY, "-O", "binary", "-j", ".cold1", elf, ISO / "COLD1.BIN"])
    sh([OBJCOPY, "-O", "binary", "-j", ".cold2", elf, WORK / "cold2.bin"])
    hw_end, lw_end = syms["_sat_bss_end"], syms["_sat_lw_bss_end"]
    print({"hw_image": (ISO / "HW.BIN").stat().st_size, "hw_end": hex(hw_end), "hw_free": HW_LIMIT - hw_end,
           "lw_image": (ISO / "LW.BIN").stat().st_size, "lw_end": hex(lw_end), "lw_free": LW_LIMIT - lw_end,
           "lifted_code_total": sum(sizes.values()), "lifted_in_hw": used, "chunks_lw": [o.stem for o in lw],
           "pack": pack_size, "cart_free": CART_END - syms["_sat_cold1_end"], "cold2_free": COLD2[0] + COLD2[1] - syms["_sat_cold2_end"]})
    if syms["_sat_cold1_end"] > CART_END or syms["_sat_cold2_end"] > COLD2[0] + COLD2[1]:
        raise SystemExit("NO-GO: past the cart")
    if hw_end > HW_LIMIT or lw_end > LW_LIMIT:
        raise SystemExit("NO-GO on this layout: segment past its RAM")
    rom = bytearray((WORK / "rt.bin").read_bytes())
    for at, name in ((HOLE_ROM, "pack_hole.bin"), (COLD2[0] - CART["ROMB"], "cold2.bin")):
        d = (WORK / name).read_bytes()
        rom[at:at + len(d)] = d
    (ISO / "ROM.BIN").write_bytes(rom)
    (WORK / "rom_final.bin").write_bytes(rom)
    b = OBJ / "boot.o"
    sh([GCC, "-m2", "-mb", "-O2", "-w", "-fno-builtin", "-I", SGL / "INC", f"-DCOLD1_ADDR={cold1_at:#x}u", "-c", HERE / "boot.c", "-o", b])
    lib = SGL / "LIB_ELF"
    sh([GCC, "-m2", "-mb", "-nostartfiles", "-T", HERE / "boot.ld", b, "-Wl,--start-group", lib / "SEGA_SYS.A", lib / "LIBCD.A", lib / "LIBSGL.A", "-lgcc", "-lc", "-Wl,--end-group",
        "-o", WORK / "boot.elf", f"-Wl,-Map={WORK / 'boot.map'},-e,_main"])
    sh([OBJCOPY, "-O", "binary", "-j", ".text", WORK / "boot.elf", ISO / "0.BIN"])
    bend = next(int(l.split()[0], 16) for l in sh([NM, WORK / "boot.elf"]).splitlines() if l.endswith("__bend"))
    print("boot", (ISO / "0.BIN").stat().st_size, "bytes, bss end", hex(bend))
    if bend > 0x06013fe0:
        raise SystemExit("loader overlaps the runtime")
    ip = WORK / "IP.BIN"
    sh([sys.executable, REPO / "tools/build_loader_ip.py", JO / "Compiler/COMMON/IP.BIN", ip])
    for n in ("ABS.TXT", "CPY.TXT", "BIB.TXT"):
        (ISO / n).write_bytes((REPO / "cd" / n).read_bytes())
    iso = WORK / "sat.iso"
    r = subprocess.run([MKISOFS, "-quiet", "-sysid", "SEGA SATURN", "-volid", "AVP_SAT_RT", "-generic-boot", str(ip), "-full-iso9660-filenames",
                        "-abstract", "ABS.TXT", "-copyright", "CPY.TXT", "-biblio", "BIB.TXT", "-o", str(iso), "."],
                       cwd=ISO, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])
    (WORK / "sat.cue").write_text(f'FILE "{iso}" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
    print("image", iso, iso.stat().st_size)


if __name__ == "__main__":
    main()
