"""Hardware fix (hwboot lane 2026-11-10): SGL 3.02 LIB_ELF members were converted from COFF and keep a non-zero input VMA on .data and .bss (the .text size).
This ld ignores the input VMA, so a DIR32 relocation against a section symbol resolves to section base + VMA instead of the section base: CDC_SUB.O's cd_stat
(and similar library variables) were read and written at a wrong address, 2 mod 4 for some members. Yaba and Ymir do not trap a misaligned long, so the discs
ran there; the SH-2 raises an address error, which is where the console stopped inside GFS_Init. The patch subtracts the section VMA from the in-place addend of
every such relocation. Used by build.py on copies of the archives; the originals are never touched.
usage: python fixlib.py AR_EXE IN.A OUT.A"""
import pathlib, shutil, struct, subprocess, sys, tempfile


def patch_object(path):
    d = bytearray(pathlib.Path(path).read_bytes())
    if d[:4] != b'\x7fELF' or d[5] != 2:
        return 0
    shoff = struct.unpack_from('>I', d, 0x20)[0]
    shentsize, shnum, _ = struct.unpack_from('>HHH', d, 0x2e)
    secs = [struct.unpack_from('>IIIIIIIIII', d, shoff + i * shentsize) for i in range(shnum)]
    n = 0
    for s in secs:
        if s[1] != 4:   # SHT_RELA
            continue
        tgt, symtab = secs[s[7]], secs[s[6]]
        for r in range(s[5] // 12):
            o = s[4] + r * 12
            off, info, _add = struct.unpack_from('>IIi', d, o)
            if (info & 0xff) != 1:   # R_SH_DIR32
                continue
            _nm, st_value, _sz, st_info, _ot, st_shndx = struct.unpack_from('>IIIBBH', d, symtab[4] + (info >> 8) * 16)
            if st_shndx == 0 or st_shndx >= len(secs) or st_value != 0 or (st_info & 0xf) not in (0, 3):
                continue
            vma = secs[st_shndx][3]
            if vma == 0 or secs[st_shndx][1] not in (1, 8):
                continue
            p = tgt[4] + off
            v = struct.unpack_from('>I', d, p)[0]
            struct.pack_into('>I', d, p, (v - vma) & 0xffffffff)
            struct.pack_into('>i', d, o + 8, 0)
            n += 1
    pathlib.Path(path).write_bytes(bytes(d))
    return n


def fix_archive(ar, src, dst):
    """Patched copy of an archive; returns the number of relocations fixed."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="libfix_"))
    try:
        names = subprocess.run([ar, "t", str(src)], capture_output=True, text=True, check=True).stdout.split()
        subprocess.run([ar, "x", str(src)], cwd=tmp, check=True)
        total = sum(patch_object(tmp / n) for n in names)
        out = pathlib.Path(dst)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            out.unlink()
        subprocess.run([ar, "rcs", str(out)] + names, cwd=tmp, check=True)
        # ar rcs wrote relative to tmp when dst is relative; keep absolute
        return total
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print(fix_archive(sys.argv[1], sys.argv[2], sys.argv[3]))
