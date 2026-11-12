#!/usr/bin/env python3
"""Data alignment gate (build NO-GO). The SH-2 raises an address error on a 16 bit access at an odd address and a 32 bit access at an address that is not a multiple of 4;
the emulators allow both (11-11: the Wolverine talk-box face cells sat at 2 mod 4, vram_copy read them as longs, the slave died on the console and nowhere else).
Checks, all on the build's own outputs:
  symbols  every data object (an nm symbol inside an input .data/.rodata/.bss section of the link map) is aligned to what its size implies (size multiple of 4 -> 4, of 2 -> 2),
           unless it is in tools/align_allow.txt (byte-only data, with the reason).
  sites    every cast of a non-literal pointer to a 16/32 bit pointer type in the C sources is on the reviewed list tools/align_sites.txt (file:count:reason, or a byte path).
           A new or moved site fails until it is reviewed. This is the scan the symbol check cannot do: it finds WHO reads byte data as words.
  packs    (optional, --work DIR) the structures of the round packs that code reads as words: section offsets, spill tables, rowtrim bases, record starts.
Usage: align_gate.py --map MAP --elf ELF [--elf ELF2 ...] --nm NM [--repo REPO] [--work WORK] [--report FILE]
Exit 1 on any hit. Stdlib only."""
import argparse, pathlib, re, subprocess, sys

def nm_symbols(nm, elf):
    out = subprocess.run([nm, "-S", "-n", str(elf)], capture_output=True, text=True).stdout
    syms = []
    for l in out.splitlines():
        p = l.split()
        if len(p) == 4:
            syms.append((int(p[0], 16), int(p[1], 16), p[2], p[3].lstrip("_")))
    return syms

def map_data_sections(mp):
    """(start, size, objectfile, section) of every input .rodata/.data/.bss section with size > 0."""
    txt = mp.read_text(errors="replace").splitlines()
    res = []
    i = 0
    while i < len(txt):
        l = txt[i]
        m = re.match(r"^ (\.(?:rodata|data|bss|sdata)[\w.\$]*)\s*(?:0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(.*))?$", l)
        if m:
            name, a, s, f = m.groups()
            if a is None and i + 1 < len(txt):   # long names put the numbers on the next line
                m2 = re.match(r"^\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(.*)$", txt[i + 1])
                if m2: a, s, f = m2.groups(); i += 1
            if a and int(s, 16) > 0 and ".str" not in name:
                res.append((int(a, 16), int(s, 16), f.strip(), name))
        i += 1
    return res

def load_allow(p):
    allow = {}
    if p.exists():
        for l in p.read_text().splitlines():
            l = l.split("#", 1)[0].strip() if not l.strip().startswith("#") else ""
            if l:
                k, _, why = l.partition(" ")
                allow[k] = why.strip()
    return allow

TYPE_SIZE = {"u8": 1, "s8": 1, "char": 1, "uint8_t": 1, "Uint8": 1, "u16": 2, "s16": 2, "short": 2, "uint16_t": 2, "Uint16": 2,
             "u32": 4, "s32": 4, "int": 4, "long": 4, "uint32_t": 4, "Uint32": 4, "unsigned": 4, "float": 4}
_sources = None
MUST4 = {"RAMB", "ROMB", "OPX", "SAT_PACK", "SAT_OBJ", "SAT_SINK"}   # lift_target.h RAM32/ROM32 and the pack readers assume these bases

def decl_elem_size(args, name):
    """Element size of the object's declaration in the C sources or the generated includes: 1 for byte data, 2 or 4 for wide data, 0 if the declaration was not found
    or is a struct/typedef (the compiler aligns those by their members, and a struct of bytes is as safe as the byte data it holds)."""
    global _sources
    if _sources is None:
        _sources = []
        roots = [pathlib.Path(args.repo) / "saturn"] + ([pathlib.Path(args.work) / "gen"] if args.work else [])
        for r in roots:
            for path in r.rglob("*"):
                if path.suffix in (".c", ".h", ".inc") and path.stat().st_size < 4_000_000:
                    _sources.append(path.read_text(errors="replace"))
    rx = re.compile(r"((?:\b(?:static|extern|const|volatile|unsigned|signed|register)\s+)*)\b([A-Za-z_]\w*)\s+\**\b" + re.escape(name) + r"\b\s*(?:\[|=|;|,)")
    for t in _sources:
        for m in rx.finditer(t):
            mods, typ = m.group(1), m.group(2)
            if typ in ("return", "else", "case", "goto", "sizeof"):
                continue
            if typ in ("char", "short", "int", "long") and "unsigned" in mods:
                pass
            if typ in TYPE_SIZE:
                return TYPE_SIZE[typ]
            if typ in ("unsigned",):
                return 4
            return 0
    return 0

def check_symbols(args, hits):
    allow = load_allow(pathlib.Path(args.allow))
    import bisect
    n = unknown = 0
    seen = set()
    for spec in args.elf:
        elf, _, mp = spec.partition("::")   # ELF or ELF::MAP (the map says which symbols sit in data sections)
        secs = sorted(map_data_sections(pathlib.Path(mp or args.map))) if (mp or args.map) and pathlib.Path(mp or args.map).exists() else []
        starts = [x[0] for x in secs]
        for addr, size, typ, name in nm_symbols(args.nm, elf):
            if name in MUST4 and addr % 4:
                hits.append(f"symbol {name} at 0x{addr:08x}: the base of a table the lifted code reads as longs must be 4 aligned")
            if size == 0 or typ in "Aa" or (name, addr) in seen:
                continue
            seen.add((name, addr))
            j = bisect.bisect_right(starts, addr) - 1
            if j < 0 or not (secs[j][0] <= addr < secs[j][0] + secs[j][1]):
                if typ not in "BbCc":
                    continue
            n += 1
            if size < 2 or addr % 2 == 0 and addr % 4 == 0:
                continue
            es = decl_elem_size(args, name)
            if es == 0:
                unknown += 1
                if addr % 2:   # an odd address is wrong for anything wider than a byte; a struct or a typedef at an odd address is reported for review
                    if name not in allow:
                        hits.append(f"symbol {name} at 0x{addr:08x} size {size}: odd address, type not found: align it or allow it with a reason")
                continue
            need = 4 if es == 1 and size >= 4 else es   # byte data is held to 4 so a cast read of it is safe; wide data to its own width (the compiler does it)
            if addr % need and name not in allow:
                hits.append(f"symbol {name} at 0x{addr:08x} size {size} (elements of {es} byte{'s' if es > 1 else ''}): needs {need} byte alignment, is {addr % need} mod {need}")
    args.unknown = unknown
    return n

CAST = re.compile(r"\(\s*(?:const\s+)?(?:volatile\s+)?(?:au32|u16|u32|unsigned\s+short|unsigned\s+long|unsigned\s+int|uint16_t|uint32_t|int|long|short|s16|s32)\s*\*\s*\)")
LITERAL = re.compile(r"\(\s*(?:const\s+)?(?:volatile\s+)?[\w\s]+\*\s*\)\s*\(?\s*(?:\(void\s*\*\)\s*)?\(?\s*0x[0-9a-fA-F]+")

def site_lines(repo):
    """(relpath, line number, line text, key) of every non-literal cast to a 16/32 bit pointer in the C sources."""
    import hashlib
    out = []
    for path in sorted((repo / "saturn").rglob("*")):
        if path.suffix not in (".c", ".h", ".inc") or "host_test" in path.name or "standalone" in path.name:
            continue
        rel = path.relative_to(repo).as_posix()
        for ln, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            code = line.split("//", 1)[0]
            hit = False
            for m in CAST.finditer(code):
                rest = code[m.end():]
                if re.match(r"\s*\(?\s*(?:\(void\s*\*\)\s*)?\(?\s*0x[0-9a-fA-F]+", rest):   # a hardware or fixed RAM address
                    continue
                if re.match(r"\s*\(?\s*\(?\s*(?:unsigned long|u32)\s*\)\s*&", rest) or re.match(r"\s*&\s*[\w(]", rest):   # the address of a typed object, or its uncached alias
                    continue
                hit = True
            if hit:
                norm = " ".join(code.split())
                out.append((rel, ln, line.strip(), rel + " " + hashlib.sha1(norm.encode()).hexdigest()[:10]))
    return out

def check_sites(args, hits):
    repo = pathlib.Path(args.repo)
    allow = {}
    p = pathlib.Path(args.sites)
    if p.exists():
        for l in p.read_text().splitlines():
            l = l.strip()
            if l and not l.startswith("#"):
                parts = l.split(None, 2)
                allow[parts[0] + " " + parts[1]] = parts[2] if len(parts) > 2 else ""
    found = site_lines(repo)
    if getattr(args, "list_sites", False):
        for rel, ln, text, key in found:
            print(f"{key}  # {ln}: {text[:110]}")
    keys = set()
    for rel, ln, text, key in found:
        keys.add(key)
        if key not in allow or not allow[key]:
            hits.append(f"site {rel}:{ln}: {text[:140]}  (a 16/32 bit read or write through a cast pointer that is not reviewed: aligned source, or a byte path; then add `{key} reason` to tools/align_sites.txt)")
    for key in allow:
        if key not in keys:
            print(f"  note: reviewed site {key} no longer exists (stale entry in tools/align_sites.txt)")
    return len(found)

WIDE = {"be32": 4, "get32": 4, "put32": 4, "put32_ram": 4, "put32b": 4, "ld32": 4, "copy8": 4, "be16": 2, "put16": 2}
CALL = re.compile(r"\b(" + "|".join(WIDE) + r")\s*\(")

def first_arg(code, i):
    depth, j = 0, i
    while j < len(code):
        c = code[j]
        if c == "(": depth += 1
        elif c == ")":
            if depth == 0: break
            depth -= 1
        elif c == "," and depth == 0: break
        j += 1
    return code[i:j]

def check_offsets(args, hits):
    """A literal byte offset added to the pointer of a 16/32 bit accessor must be a multiple of its width (be32(p + 6) reads a long at 2 mod 4 whatever p is)."""
    repo = pathlib.Path(args.repo)
    n = 0
    for path in sorted((repo / "saturn").rglob("*")):
        if path.suffix not in (".c", ".h", ".inc") or "host_test" in path.name or "standalone" in path.name:
            continue
        for ln, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            code = line.split("//", 1)[0]
            for m in CALL.finditer(code):
                a = first_arg(code, m.end())
                n += 1
                flat = a
                while True:   # terms inside a nested parenthesis belong to a product or a cast, not to the byte offset
                    g = re.sub(r"\([^()]*\)", "()", flat)
                    if g == flat: break
                    flat = g
                a_full, a = a, flat
                for t in re.finditer(r"\+\s*(0x[0-9a-fA-F]+|\d+)\b(?!\s*[*/<(])", a):
                    v = int(t.group(1), 0)
                    if v % WIDE[m.group(1)]:
                        hits.append(f"offset {path.relative_to(repo).as_posix()}:{ln}: {m.group(1)}({a_full.strip()}) adds {v}, not a multiple of {WIDE[m.group(1)]}")
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map"); ap.add_argument("--elf", action="append", default=[]); ap.add_argument("--nm")
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--allow", default=str(pathlib.Path(__file__).with_name("align_allow.txt")))
    ap.add_argument("--sites", default=str(pathlib.Path(__file__).with_name("align_sites.txt")))
    ap.add_argument("--work"); ap.add_argument("--report"); ap.add_argument("--no-sites", action="store_true"); ap.add_argument("--list-sites", action="store_true")
    args = ap.parse_args()
    hits = []
    nsym = check_symbols(args, hits) if args.elf else 0
    nsite = 0 if args.no_sites else check_sites(args, hits)
    noff = 0 if args.no_sites else check_offsets(args, hits)
    if args.work:
        import align_packs
        align_packs.check(pathlib.Path(args.work), hits)
    msg = f"align gate: {nsym} data symbols ({getattr(args, 'unknown', 0)} of unknown type), {nsite} cast sites, {noff} accessor calls, {len(hits)} hits"
    print(msg)
    for h in hits: print("  HIT", h)
    if args.report: pathlib.Path(args.report).write_text(msg + "\n" + "\n".join(hits) + "\n")
    return 1 if hits else 0

if __name__ == "__main__":
    sys.exit(main())
