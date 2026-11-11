"""Build gate for the loader image (0.BIN, linked to boot.elf with --emit-relocs): every data address it references must be inside its own variables and aligned.

Catches the SGL library relocation defect (fixlib.py): a variable addressed at its section base plus the input VMA is out of its object's range, outside the loader
variable area, and often misaligned, which is an address error on the console. Checks:
  A  every defined data/bss symbol with a size is aligned for its size (4 for 4 bytes or more, 2 for 2 or 3);
  B  every 32-bit address (DIR32 relocation) into the loader RAM window (0x06004000..0x06014000) lies between the load address and __bend;
  C  a DIR32 relocation against a named object symbol with a size lands inside that symbol (or one past it);
  D  a DIR32 relocation against a section symbol lands inside the same OBJECT's own input section of that name (link map), never in a neighbour's;
  E  a data target (.data/.bss) is never at an odd address unless it is a byte symbol.
usage: python check_boot_data.py boot.elf boot.map   (exit 1 with the list of failures)
"""
import re
import struct
import sys
import pathlib

WIN_LO, WIN_HI = 0x06004000, 0x06014000
BS = chr(92)


def read_elf(path):
    d = pathlib.Path(path).read_bytes()
    assert d[:4] == b'\x7fELF' and d[5] == 2
    shoff = struct.unpack_from('>I', d, 0x20)[0]
    shentsize, shnum, shstrndx = struct.unpack_from('>HHH', d, 0x2e)
    secs = []
    for i in range(shnum):
        n, ty, fl, addr, off, size, link, info, al, es = struct.unpack_from('>IIIIIIIIII', d, shoff + i * shentsize)
        secs.append(dict(name=n, type=ty, addr=addr, off=off, size=size, link=link, info=info))
    so = secs[shstrndx]['off']
    for s in secs:
        e = d.index(b'\0', so + s['name'])
        s['name'] = d[so + s['name']:e].decode()
    return d, secs


def read_symbols(d, secs):
    st = next(s for s in secs if s['type'] == 2)
    stro = secs[st['link']]['off']
    out = []
    for i in range(st['size'] // 16):
        n, v, sz, info, oth, shn = struct.unpack_from('>IIIBBH', d, st['off'] + i * 16)
        e = d.index(b'\0', stro + n)
        out.append(dict(name=d[stro + n:e].decode(), value=v, size=sz, type=info & 0xf, shndx=shn))
    return out


def parse_map(path):
    """Input sections (start, end, name, object) from the GNU ld map; the name and the numbers may be on two lines."""
    out, pend = [], None
    rx = re.compile(r'^\s(\.[\w.$]+|COMMON)\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(\S.*)$')
    rx2 = re.compile(r'^\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(\S.*)$')
    rxn = re.compile(r'^\s(\.[\w.$]+|COMMON)$')
    for l in pathlib.Path(path).read_text(errors='replace').splitlines():
        m = rx.match(l)
        if m:
            a = int(m.group(2), 16)
            out.append((a, a + int(m.group(3), 16), m.group(1), m.group(4).strip()))
            pend = None
            continue
        m = rxn.match(l)
        if m:
            pend = m.group(1)
            continue
        m = rx2.match(l)
        if m and pend:
            a = int(m.group(1), 16)
            out.append((a, a + int(m.group(2), 16), pend, m.group(3).strip()))
        pend = None
    return out


def check(elf, mapf):
    d, secs = read_elf(elf)
    syms = read_symbols(d, secs)
    byn = {s['name']: s for s in syms}
    bend = byn['__bend']['value'] if '__bend' in byn else byn['_end']['value']
    inputs = parse_map(mapf)
    bad = []

    def sec_of(addr):
        return next((s['name'] for s in secs if s['addr'] and s['addr'] <= addr < s['addr'] + s['size']), None)

    def secname(ndx):
        return secs[ndx]['name'] if 0 < ndx < len(secs) else ''

    for s in syms:   # A
        if s['shndx'] in (0, 0xfff1) or s['type'] not in (0, 1) or s['size'] == 0 or not (WIN_LO <= s['value'] <= bend):
            continue
        if secname(s['shndx']) in ('.bss', '.data') or s['shndx'] == 0xfff2:
            al = 4 if s['size'] >= 4 else 2 if s['size'] >= 2 else 1
            if s['value'] % al:
                bad.append(f"A misaligned variable {s['name']} at {s['value']:#x} size {s['size']}")
    for rs in secs:   # B to E
        if rs['type'] != 4:
            continue
        tgt = secs[rs['info']]
        for r in range(rs['size'] // 12):
            off, info, add = struct.unpack_from('>IIi', d, rs['off'] + r * 12)
            if (info & 0xff) != 1:
                continue
            X = off if off >= tgt['addr'] else tgt['addr'] + off   # executables carry the address, objects the offset
            T = struct.unpack_from('>I', d, tgt['off'] + (X - tgt['addr']))[0]
            sym = syms[info >> 8]
            if not (WIN_LO <= T < WIN_HI):
                continue
            nm = sym['name'] or secname(sym['shndx'])
            where = f"reloc at {X:#x} -> {T:#x} ({nm})"
            if T > bend:
                bad.append("B " + where + f" beyond the loader variables (__bend {bend:#x})")
                continue
            if sym['type'] == 3 or not sym['name']:   # section symbol
                sn = secname(sym['shndx'])
                src = next((i for i in inputs if i[2] == '.text' and i[0] <= X < i[1]), None)
                if src is not None and sn:
                    own = [i for i in inputs if i[3] == src[3] and i[1] > i[0]]   # any input section of that object (the output .text also holds its .rodata and .data)
                    if not any(i[0] <= T <= i[1] for i in own):
                        bad.append("D " + where + f" outside its own object ({src[3].split(BS)[-1]})")
            elif sym['size'] and sym['type'] == 1:
                if not (sym['value'] <= T <= sym['value'] + sym['size']):
                    bad.append("C " + where + f" outside symbol {sym['name']} [{sym['value']:#x}+{sym['size']:#x}]")
            if sec_of(T) in ('.bss', '.data') and T % 2 and sym['size'] != 1:
                bad.append("E " + where + " odd data address")
    return bad


if __name__ == "__main__":
    b = check(sys.argv[1], sys.argv[2])
    print("\n".join(b) if b else "boot data check: ok")
    sys.exit(1 if b else 0)
