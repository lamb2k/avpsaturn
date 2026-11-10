#!/usr/bin/env python
"""Host check: after any stage file loads, every ROM page it keeps holds the ROM's bytes, whatever stage file loaded before it.
Reads the built round files as the loader does (head sector, destination and size pairs; the second region at SAT_PACK is the tile pack, regions after it are tile
spill into ROM stretches, regions before it are ROM restores), WORK/round_keep.json (build.py: the pages each file keeps) and WORK/disc/ROM.BIN (the ROM as built).
A page that any file fills with tiles must be written back with the ROM's own bytes by every file that keeps it (a restore, or the ROM tail that pads a spill sector,
PACK_TAIL_FILL), and a file never puts tiles on a page it keeps.
usage: check_round_pages.py WORK   exit 1 on any violation. ROM-derived input: WORK only."""
import json, pathlib, struct, sys

SAT_PACK, ROMB, SEC = 0x02654000, 0x02400000, 2048


def round_files(work):
    """From the disc as built: STORE.BIN (SECTOR_STORE) rebuilt per round as the loader reads it, else the R*.BIN files."""
    disc = work / "disc"
    if (disc / "STORE.BIN").exists():
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import sector_store
        store = (disc / "STORE.BIN").read_bytes()
        n = struct.unpack_from(">II", store)[1]
        return {i: sector_store.rebuild(store, i) for i in range(n)}
    return {int(f.stem[1:]): f.read_bytes() for f in sorted(disc.glob("R[0-9][0-9][0-9].BIN"))}


def regions(blob):
    n = struct.unpack_from(">I", blob)[0]
    at, packs, pre, post = SEC, 0, [], []
    for i in range(n):
        dest, size = struct.unpack_from(">II", blob, 4 + i * 8)
        if dest == 1:
            continue
        data = blob[at:at + size]
        at += size
        if dest == SAT_PACK:
            packs += 1
        elif ROMB <= dest < ROMB + 0x200000:
            (pre if packs < 2 else post).append((dest - ROMB, data))
    return pre, post


def written(parts, page):
    """page -> its bytes, for pages a file's regions cover whole, later regions over earlier."""
    img = {}
    for a, d in parts:
        if a % page or len(d) % page:
            raise SystemExit("region not page aligned: %x +%x" % (a, len(d)))
        for q in range(a // page, (a + len(d)) // page):
            img[q] = d[(q - a // page) * page:(q - a // page + 1) * page]
    return img


def main():
    work = pathlib.Path(sys.argv[1])
    rom = (work / "disc" / "ROM.BIN").read_bytes()
    keep_list = json.loads((work / "round_keep.json").read_text())   # file order, guest files included
    page = json.loads((work / "rounds.json").read_text())["page"]
    names = [n for n, _ in keep_list]
    keep = dict(keep_list)
    files = {i: b for i, b in round_files(work).items() if i < len(names)}
    tile_pages, state = set(), {}
    for i, blob in files.items():
        pre, post = regions(blob)
        rom_ok = {q for q, b in written(pre + post, page).items() if b == rom[q * page:(q + 1) * page]}
        spilled = {q for q in written(post, page) if q not in rom_ok}
        state[i] = (rom_ok, spilled)
        tile_pages |= spilled
    bad = 0
    for i, (rom_ok, spilled) in state.items():
        kp = set(keep.get(names[i], ()))
        over = sorted(spilled & kp)
        miss = sorted(q for q in kp & tile_pages if q not in rom_ok)
        if over or miss:
            bad += 1
            print(f"FAIL R{i:03d} {names[i]}: tiles on kept pages {over[:6]} ({len(over)}); kept pages another file overwrites and this one does not rewrite {miss[:6]} ({len(miss)})")
    print(f"{'FAIL' if bad else 'PASS'}: {bad} of {len(files)} round files break the page rule; {len(tile_pages)} pages are tile spill somewhere")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
