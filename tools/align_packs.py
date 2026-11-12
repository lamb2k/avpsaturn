"""Alignment checks of the disc files the runtime reads as 16/32 bit words (called by align_gate.py --work WORK; WORK/disc holds the disc files).
Facts used (saturn/gfx/sat_gfx.c, saturn/rt/kernel.c load_round, tools/rounds_pack.py write_file/assemble, saturn/rt/reveal.c):
  round file R###.BIN: a header sector (u32 region count, then (destination, length) per region), the regions in order; the tile pack is the region whose destination is SAT_PACK and starts with SGP1/2/3.
  pack: u32 reads of the header, key tables (u32 keys), spill table, rowtrim bases (u32) and offsets (u16), tile slots (128 bytes, read as longs), sprite records (4 + 4n or 4 + 8n bytes, read as longs after the mask), and the
  spill records in ROM stretches (destination ROMB + a, read as longs).
A hit is a structure that code reads as words and that sits at an address (destination + offset) which is not a multiple of the read width."""
import pathlib, re, struct

SEC = 2048

def be32(b, o): return struct.unpack(">I", b[o:o + 4])[0]
def be16(b, o): return struct.unpack(">H", b[o:o + 2])[0]

def read_header(f):
    f.seek(0)
    head = f.read(SEC)
    n = be32(head, 0)
    regs = [(be32(head, 4 + 8 * i), be32(head, 8 + 8 * i)) for i in range(n)]
    return regs

def check_round(path, pack_addr, hits, seen):
    name = path.name
    with open(path, "rb") as f:
        regs = read_header(f)
        off = SEC
        for i, (dest, ln) in enumerate(regs):
            if dest == 1:
                continue
            if dest % 4 or ln % 4:
                hits.append(f"{name} region {i}: destination 0x{dest:08x} length {ln} is not a multiple of 4 (longs are copied into it and read from it)")
            if dest == pack_addr and i > 0 and ln >= 120:   # the audio region shares the pack address; the tile pack is the later one with a pack magic
                f.seek(off)
                head = f.read(120)
                if be32(head, 0) not in (0x53475031, 0x53475032, 0x53475033):
                    off += ln
                    continue
                magic = be32(head, 0)
                sprite_mult = 4 if magic == 0x53475033 else 4   # SGP2 records are 4 + 8n, SGP3 4 + 4n: both a multiple of 4
                for s in range(4):
                    cnt, ko, do = struct.unpack_from(">III", head, 4 + s * 12)
                    for what, v in (("key table", ko), ("tile data", do)):
                        if (pack_addr + v) % 4:
                            hits.append(f"{name}: section {s} {what} at pack+0x{v:x} is not 4 aligned")
                tail = [struct.unpack_from(">II", head, 52 + 8 * s) for s in range(4)]
                spill_tab = tail[0][1]
                if magic != 0x53475031:
                    offs_at, offs16_at = struct.unpack_from(">II", head, 84)
                    if (pack_addr + offs_at) % 4: hits.append(f"{name}: rowtrim base table at pack+0x{offs_at:x} is not 4 aligned")
                    if (pack_addr + offs16_at) % 2: hits.append(f"{name}: rowtrim offset table at pack+0x{offs16_at:x} is odd")
                if spill_tab:
                    if (pack_addr + spill_tab) % 4: hits.append(f"{name}: spill table at pack+0x{spill_tab:x} is not 4 aligned")
                    f.seek(off + spill_tab)
                    k = be32(f.read(4), 0)
                    for j in range(k):
                        first, rel = struct.unpack(">II", f.read(8))
                        if (pack_addr + rel) % 4:
                            hits.append(f"{name}: spill segment {j} at 0x{(pack_addr + rel) & 0xffffffff:08x} is not 4 aligned (records are read as longs)")
                seen["packs"] = seen.get("packs", 0) + 1
            off += ln
    seen["files"] = seen.get("files", 0) + 1

def check_reveal(path, hits, seen):
    b = path.read_bytes()
    if len(b) < 24: return
    for f in range(3):
        o = be32(b, 12 + f * 4)
        if o % 4: hits.append(f"REVEAL.BIN: picture {f} record at +0x{o:x} is not 4 aligned (reveal.c reads longs from record + 4)")
    seen["reveal"] = 1

def check(work, hits, pack_addr=None):
    disc = pathlib.Path(work) / "disc"
    seen = {}
    if pack_addr is None:   # SAT_PACK from the link map symbol list written by the build (sat.map)
        m = re.search(r"0x([0-9a-f]+)\s+_?SAT_PACK", (pathlib.Path(work) / "sat.map").read_text(errors="replace")) if (pathlib.Path(work) / "sat.map").exists() else None
        pack_addr = int(m.group(1), 16) if m else 0x02400000 + 0
    if pack_addr % 4:
        hits.append(f"SAT_PACK 0x{pack_addr:08x} is not 4 aligned")
    rounds = pathlib.Path(work) / "disc"
    pat = re.compile(r"R\d{3}\.BIN$")
    files = sorted(p for d in (rounds, pathlib.Path(work) / "rounds") if d.exists() for p in d.glob("R*.BIN") if pat.match(p.name))
    for p in files:
        check_round(p, pack_addr, hits, seen)
    if (disc / "REVEAL.BIN").exists():
        check_reveal(disc / "REVEAL.BIN", hits, seen)
    print(f"align packs: {seen.get('files', 0)} round files, {seen.get('packs', 0)} tile packs, reveal {'yes' if seen.get('reveal') else 'no'}, SAT_PACK 0x{pack_addr:08x}")
