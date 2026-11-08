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
HW_RESERVED = 0x10000 + 16 * 2048 + 8192 + 16384 + 0x8000 + 0x8000   # game RAM, stacks, kernel, graphics tables and code
LW_RESERVED = 0x20000 + 0x4000 + 0xe400   # graphics RAM, lifted bss, layer shadows, blank tags
NATIVE = ("41ca", "42e4")   # EEPROM block read and write
# Readable replacements, saturn/game. GAME_OVERRIDES=0 builds without them, for an A/B.
OVERRIDES = () if os.environ.get("GAME_OVERRIDES") == "0" else tuple((REPO / "saturn/game/overrides.txt").read_text().split())
CART = dict(ROMB=0x02400000, OPX=0x02600000, SAT_SINK=0x02640000, SAT_OBJ=0x02650000, SAT_PACK=0x02654000)
CART_END = 0x02800000
OPX_MAX = 0x40000
COLD1_ROOM = 0x20000   # cart tail for cold code that no ROM stretch takes
COLD1_AT = CART_END - COLD1_ROOM
# ROM stretches no walk of any stage or character reads (tools/rounds_census.py, WORK/rounds.json): cold chunks of lifted code stay in them for the whole game, per-round tiles take the rest.
ROUNDS = json.loads((WORK / "rounds.json").read_text())
STRETCHES = [(0x02400000 + a, n) for a, n in ROUNDS["holes"] if n >= 0x4000]


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
        for n in NATIVE + OVERRIDES:   # replaced natively; the lifted body stays linked as lifted_NNN
            t = t.replace(f"void f_{n}(void){{", f"void lifted_{n}(void){{")
        for n in OVERRIDES:   # memory is tight and the target never falls back: the replaced body goes
            t = re.sub(r"^void lifted_%s\(void\)\{.*?^\}\n" % n, "", t, flags=re.M | re.S)
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
    # Stage word -> row; row, variant -> file. Row 0 is the front end. Mask ff81cc -> variant; 0 is the one-for-all file.
    vf, masks = ROUNDS.get("variant_file", {}), ROUNDS.get("variant_masks", [])
    rows = [[0] * (len(masks) + 1)]
    srow = [0] * 256
    for i in range(256):
        f = ROUNDS["stage_file"].get(str(i), 0)
        if f:
            srow[i] = len(rows)
            rows.append(vf.get(str(i), [f] * (len(masks) + 1)))
    mvar = [masks.index(m) + 1 if m in masks else 0 for m in range(16)]
    update(GEN / "rounds.inc", "static const u8 stage_row[256] = {%s};\nstatic const u8 mask_variant[16] = {%s};\nstatic const unsigned short row_file[%d][%d] = {%s};\n" % (
        ",".join(map(str, srow)), ",".join(map(str, mvar)), len(rows), len(masks) + 1, ",".join("{" + ",".join(map(str, r)) + "}" for r in rows)))
    return out


def cc(src, obj, extra=()):
    newest = max(src.stat().st_mtime, (HERE / "lift_target.h").stat().st_mtime)
    if src.name in ("kernel.c", "pad.c", "sat_gfx.c", "home.c", "home_cold.c"):
        newest = max(newest, (HERE / "sat_rt.h").stat().st_mtime, time.time() if os.environ.get("KERNEL_CFLAGS") else 0)
    if src.name == "sat_gfx.c":
        newest = max(newest, (src.parent / "sat_gfx.h").stat().st_mtime)
    if not obj.exists() or obj.stat().st_mtime < newest:
        sh([GCC, *CF, *extra, "-c", src, "-o", obj])
    return obj


def code_size(o):
    rows = (l.split() for l in sh([OBJDUMP, "-h", o]).splitlines())
    return sum(int(r[2], 16) for r in rows if len(r) > 3 and r[1].startswith((".text", ".rodata", ".data")))


SHARED_MIN = int(os.environ.get("ROUND_SHARED_MIN", "10"))   # stages
MIN_RUN = int(os.environ.get("ROUND_MIN_RUN", "1"))   # pages; a stretch costs 8 bytes of table, about 1 KB of a page is 8 sprites


def round_files(rom, code_end, cold1_at):
    """One RNN.BIN per stage. Sprites past the cart's room go to ROM stretches that stage does not read; whatever any file overwrites, each stage that reads it gets back."""
    sys.path.insert(0, str(REPO / "tools"))
    import rounds_pack
    raw = pathlib.Path(os.environ.get("GFX_BIN", "E:/AvP/learning/lane-satgfx/gfx.bin")).read_bytes()
    room = cold1_at - CART["SAT_PACK"]
    page = ROUNDS["page"]
    code = bytearray(0x200000 // page)   # pages holding lifted cold code never take tiles
    for at, end in code_end:
        for q in range((at - CART["ROMB"]) // page, (end - CART["ROMB"] + page - 1) // page):
            code[q] = 1
    plans, written = [], set()
    # Census gap: a mode or setting outside the census can read common tables a walk of this stage never touched. Pages most stages read stay in every stage. Costs sprites only in stages already short of room.
    base = [f for f in ROUNDS["files"] if re.fullmatch(r"stage[0-9a-f]{2}", f["name"])]
    seen = {}
    for f in base:
        for q in set(f["keep_pages"]):
            seen[q] = seen.get(q, 0) + 1
    shared = {q for q, c in seen.items() if c >= SHARED_MIN}
    rank = json.loads((WORK / "key_rank.json").read_text()) if (WORK / "key_rank.json").exists() else {}   # tools/rounds_rank.py
    # ARENA_KEEP (test): the duel's RANDOM arenas also keep the pages stage 02's walk reads, so their spilled sprites stay off what the duel reads there.
    k02 = set(next(f for f in base if f["name"] == "stage02")["keep_pages"]) if os.environ.get("ARENA_KEEP") else set()
    for f in ROUNDS["files"]:
        keep = set(f["keep_pages"]) | shared
        if k02 and set(f.get("stages", [])) & {0x0e, 0x1c, 0x1e, 0x24}: keep |= k02
        free, st = [], None
        for q in range(0x200000 // page + 1):
            ok = q < 0x200000 // page and q not in keep and not code[q]
            if ok and st is None:
                st = q
            if not ok and st is not None:
                if q - st >= MIN_RUN:
                    free.append([st * page, (q - st) * page])
                st = None
        free.sort(key=lambda r: -r[1])
        p, dropped = rounds_pack.fit(raw, [set(k) for k in f["keys"]], room, free, {int(x): v for x, v in rank.get(f["name"], {}).items()})
        for first, a, take in p["segs"]:
            written.update(range(a // page, (a + (take * 128 + 2047 & -2048) + page - 1) // page))
        plans.append((p, dropped))
    stats = {}
    for i, (f, (p, dropped)) in enumerate(zip(ROUNDS["files"], plans)):
        own = {x for first, a, take in p["segs"] for x in range(a // page, (a + (take * 128 + 2047 & -2048) + page - 1) // page)}
        back = sorted((written & (set(f["keep_pages"]) | shared)) - own)
        restores, st = [], None
        for q in back + [None]:
            if st is not None and (q is None or q != st[1]):
                restores.append((CART["ROMB"] + st[0] * page, bytes(rom[st[0] * page:st[0] * page + ((st[1] - st[0]) * page + 2047 & -2048)]))); st = None   # whole sectors of ROM, so no padding lands on the next page
            if q is None:
                break
            st = [q, q + 1] if st is None else [st[0], q + 1]
        audio = (WORK / "audio" / f"r{i:03d}.bin").read_bytes()
        n = rounds_pack.write_file(ISO / f"R{i:03d}.BIN", audio, restores, rounds_pack.assemble(p, CART["SAT_PACK"]))
        stats[f["name"]] = dict(file=n, sprites_in_main=p["inmain"], sprites_spill=sum(x[2] for x in p["segs"]), spill_runs=len(p["segs"]), restore=sum(len(d) for _, d in restores), restore_runs=len(restores), dropped_keys=len(dropped), dropped=dropped, audio=len(audio))
        print(f["name"], {k: v for k, v in stats[f["name"]].items() if k != "dropped"}, flush=True)
    (WORK / "round_stats.json").write_text(json.dumps(stats, indent=0))


def refresh_restores(rom):
    """Round files restore ROM pages, and a page can hold cold code, whose calls name kernel addresses: a kept file must carry this build's bytes. Layout as boot.c reads it: one head sector of count, then destination and bytes pairs."""
    import struct
    n = 0
    for f in ISO.glob("R[0-9][0-9][0-9].BIN"):
        with open(f, "r+b") as h:
            head = h.read(2048)
            at, changed = 2048, False
            for i in range(struct.unpack_from(">I", head)[0]):
                dest, size = struct.unpack_from(">II", head, 4 + i * 8)
                if dest == 1:
                    continue
                if CART["ROMB"] <= dest < CART["ROMB"] + len(rom):
                    h.seek(at)
                    want = bytes(rom[dest - CART["ROMB"]:dest - CART["ROMB"] + size])
                    if h.read(size) != want:
                        h.seek(at); h.write(want); changed = True
                at += size
            n += changed
    return n


def main():
    gen = gen_sources()
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        objs = list(ex.map(lambda s: cc(s, OBJ / (s.stem + ".o"), [OPT]), gen))
    home = "SAT_HOME" in os.environ.get("KERNEL_CFLAGS", "")
    if home:
        sh([sys.executable, REPO / "tools/home_font.py", WORK, os.environ.get("GFX_BIN", "E:/AvP/learning/lane-satgfx/gfx.bin")])
    gfx_dir = REPO / "saturn/gfx"
    gfx = [gfx_dir / "sat_gfx.c"]
    own = [cc(HERE / "ctx.s", OBJ / "ctx.o"), cc(HERE / "kernel.c", OBJ / "kernel.o", ["-O2", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()), cc(HERE / "present.c", OBJ / "present.o", ["-O2"]), cc(HERE / "pad.c", OBJ / "pad.o", ["-O2"] + os.environ.get("KERNEL_CFLAGS", "").split())]
    own += [cc(REPO / "saturn/audio/sat_audio.c", OBJ / "sat_audio.o", ["-Os"] + os.environ.get("AUDIO_CFLAGS", "").split())]
    own += [cc(s, OBJ / f"gfx_{s.stem}.o", ["-O2", "-I", gfx_dir, "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()) for s in gfx]
    if home:
        own += [cc(HERE / "home.c", OBJ / "home.o", ["-Os"] + os.environ.get("KERNEL_CFLAGS", "").split())]
    home_cold = [cc(HERE / "home_cold.c", OBJ / "home_cold.o", ["-Os"] + os.environ.get("KERNEL_CFLAGS", "").split())] if home else []
    if OVERRIDES:
        own += [cc(REPO / "saturn/game" / f"{n}.c", OBJ / f"game_{n}.o", ["-O2", "-DSAT_TARGET", "-I", REPO / "saturn/game"]) for n in ("game_hot", "game_bind")]
    sizes = {o: code_size(o) for o in objs}
    # Hottest chunks in high work RAM, then low work RAM; the coldest run from the cart. Heat comes from the MAME route.
    heat = json.loads((WORK / "heat.json").read_text())
    objs_o = sorted(objs, key=lambda o: -heat.get(o.stem, 1 << 40))
    room_hw = HW_LIMIT - HW_BASE - HW_RESERVED
    room_lw = LW_LIMIT - LW_BASE - LW_RESERVED
    # The seven hottest chunks hold about 97% of the instructions and always go first. The rest barely differ in heat, so they are chosen to fill the RAM.
    hw, used = [], 0
    room_hw -= 9600   # own code and data the count leaves out
    for o in objs_o[:7]:
        if used + sizes[o] <= room_hw:
            hw.append(o); used += sizes[o]
    tail = [o for o in objs_o if o not in hw]
    fill = {0: []}
    for o in tail:
        for total, picked in list(fill.items()):
            t = total + sizes[o]
            if used + t <= room_hw and t not in fill:
                fill[t] = picked + [o]
    best_fill = max(fill)
    hw += fill[best_fill]; used += best_fill
    rest = [o for o in objs_o if o not in hw]
    cold1_at = COLD1_AT
    room_cold1 = COLD1_ROOM
    best = None
    for mask in range(1 << len(rest)):
        out = [o for i, o in enumerate(rest) if mask >> i & 1]
        if sum(sizes[o] for o in rest) - sum(sizes[o] for o in out) > room_lw - 8192:   # margin: bss the size count leaves out
            continue
        placed, rooms = [[] for _ in STRETCHES], [s[1] for s in STRETCHES]
        for o in sorted(out, key=lambda o: -sizes[o]):   # largest first into the ROM stretches, tightest that fits
            fit = [i for i in range(len(rooms)) if sizes[o] <= rooms[i]]
            if fit:
                i = min(fit, key=lambda i: rooms[i])
                placed[i].append(o); rooms[i] -= sizes[o]
        two = [o for p in placed for o in p]
        three = []
        if sum(sizes[o] for o in out if o not in two and o not in three) > room_cold1:
            continue
        score = (sum(heat.get(o.stem, 1 << 40) for o in out), len(out))
        if best is None or score < best[0]:
            best = (score, out, placed, three)
    if best is None:
        raise SystemExit(f"NO-GO: no placement fits: rest {sum(sizes[o] for o in rest)} room_lw {room_lw} cold1 {room_cold1} stretches {STRETCHES} sizes {sorted(sizes[o] for o in rest)}")
    cold = best[1]
    placed = best[2]
    cold2 = [o for p in placed for o in p]
    cold3 = best[3]
    cold1 = [o for o in cold if o not in cold2 and o not in cold3]
    # The cart tail holds only what cold code needs; the rest is sprite room.
    cold1_at = CART_END - ((sum(sizes[o] for o in cold1) + sum(code_size(o) for o in home_cold) + 0x1fff) & ~0xfff)
    lw = [o for o in rest if o not in cold]
    usedl = sum(sizes[o] for o in lw)
    print("placement", {"hw": len(hw), "lw": [o.stem for o in lw], "cold1": [(o.stem, sizes[o], heat.get(o.stem)) for o in cold1], "stretches": [[o.stem for o in p] for p in placed]})
    inp = lambda l, s: "\n".join(f'    "{o.as_posix()}"({s})' for o in l)
    tx = ".text .text.* .rodata .rodata.* .data .data.*"
    stretch_ld = "".join(f"""  .st{i} {s[0]:#x} : {{
{inp(placed[i], tx)}
    . = ALIGN(4);
    _sat_st{i}_end = .;
  }}
""" for i, s in enumerate(STRETCHES))
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
{inp(cold1 + home_cold, tx)}
    . = ALIGN(4);
    _sat_cold1_end = .;
  }}
{stretch_ld}  .lw {LW_BASE:#x} : {{
    *(.text .text.* .rodata .rodata.* .data .data.*)
    . = ALIGN(4);
  }}
  .lwbss (NOLOAD) : {{ _sat_lw_bss_start = .; *(.lwgfx) *(.bss COMMON) . = ALIGN(4); _sat_lw_bss_end = .; }}
  /DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
""" + "".join(f"_{k} = {v:#x};\n" for k, v in CART.items())
    (WORK / "sat.ld").write_text(ld)
    elf = WORK / "sat.elf"
    sh([GCC, "-m2", "-mb", "-nostdlib", "-T", WORK / "sat.ld", *own, *home_cold, *objs, "-lgcc", "-o", elf, f"-Wl,-Map={WORK / 'sat.map'}"])
    sh([OBJCOPY, "-O", "binary", "-j", ".hw", elf, ISO / "HW.BIN"])
    sh([OBJCOPY, "-O", "binary", "-j", ".lw", elf, ISO / "LW.BIN"])
    syms = {p[2]: int(p[0], 16) for p in (l.split() for l in sh([NM, elf]).splitlines()) if len(p) == 3}
    shutil.copy(WORK / "opx.bin", ISO / "OPX.BIN")
    if (WORK / "opx.bin").stat().st_size > OPX_MAX:
        raise SystemExit("NO-GO: store past its room")
    sh([OBJCOPY, "-O", "binary", "-j", ".cold1", elf, ISO / "COLD1.BIN"])
    if not (ISO / "COLD1.BIN").stat().st_size:   # the loader halts on an empty read
        (ISO / "COLD1.BIN").write_bytes(bytes(4))
    for i in range(len(STRETCHES)):
        sh([OBJCOPY, "-O", "binary", "-j", f".st{i}", elf, WORK / f"st{i}.bin"])
    hw_end, lw_end = syms["_sat_bss_end"], syms["_sat_lw_bss_end"]
    print({"hw_image": (ISO / "HW.BIN").stat().st_size, "hw_end": hex(hw_end), "hw_free": HW_LIMIT - hw_end,
           "lw_image": (ISO / "LW.BIN").stat().st_size, "lw_end": hex(lw_end), "lw_free": LW_LIMIT - lw_end,
           "lifted_code_total": sum(sizes.values()), "lifted_in_hw": used, "chunks_lw": [o.stem for o in lw],
           "cart_free": CART_END - syms["_sat_cold1_end"], "stretch_free": [s[0] + s[1] - syms[f"_sat_st{i}_end"] for i, s in enumerate(STRETCHES)]})
    if syms["_sat_cold1_end"] > CART_END or any(syms[f"_sat_st{i}_end"] > s[0] + s[1] for i, s in enumerate(STRETCHES)):
        raise SystemExit("NO-GO: past the cart")
    if hw_end > HW_LIMIT or lw_end > LW_LIMIT:
        raise SystemExit("NO-GO on this layout: segment past its RAM")
    rom = bytearray((WORK / "rt.bin").read_bytes())
    for i, st in enumerate(STRETCHES):
        d = (WORK / f"st{i}.bin").read_bytes()
        at = st[0] - CART["ROMB"]
        rom[at:at + len(d)] = d
    (ISO / "ROM.BIN").write_bytes(rom)
    # KEEP_ROUND_FILES=1, for a kernel-only rebuild: round files never touch pages holding cold code, so they stay valid while those pages are the same.
    # The pack in main ends where cold1 starts: a kept file built for a lower cold1 would have its last tiles overwritten by cold code (seen as wrong tiles on crates in stages 24 and 1e).
    ends = [[st[0], syms[f"_sat_st{i}_end"]] for i, st in enumerate(STRETCHES)] + [[cold1_at, 0]]
    ends_file = WORK / "round_code_ends.json"
    if os.environ.get("KEEP_ROUND_FILES") and (not ends_file.exists() or json.loads(ends_file.read_text()) == ends):
        n = refresh_restores(rom)
        print("round files kept; ROM restore bytes refreshed in", n, "files")
    else:
        round_files(rom, [tuple(e) for e in ends[:-1]], cold1_at)
    ends_file.write_text(json.dumps(ends))
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
