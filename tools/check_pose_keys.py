#!/usr/bin/env python
"""Host check (lane avp-vanish): every stage round file's tile pack holds every sprite key of WORK/pose_keys.txt (tools/pose_keys.py: player poses of the button-fuzz census).
Catches a pose drawing blank (the player's body gone in a fight). Same reader as tools/check_screen_keys.py.
Reads the round files as boot.c does: head sector, then destination/size pairs; the second region at SAT_PACK is the tile pack (SGP1).
usage: check_pose_keys.py WORK   exit 1 on any file missing a key."""
import json, pathlib, struct, sys
SAT_PACK = 0x02654000


def pack_keys(blob):
    n, at, packs = struct.unpack_from(">I", blob)[0], 2048, 0
    for i in range(n):
        dest, size = struct.unpack_from(">II", blob, 4 + i * 8)
        if dest == 1:
            continue
        if dest == SAT_PACK:
            packs += 1
            if packs == 2:
                m = blob[at:at + size]
                assert m[:4] in (b"SGP1", b"SGP2"), "not a tile pack"
                out = []
                for sec in range(4):   # sprite words key << 16 | index, scroll words key << 14 | index
                    count, keyoff = struct.unpack_from(">II", m, 4 + sec * 12)
                    out.append({struct.unpack_from(">I", m, keyoff + 4 * k)[0] >> (16 if sec == 0 else 14) for k in range(count)})
                return out
        at += size
    raise SystemExit("no tile pack in round file")


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


def main():
    work = pathlib.Path(sys.argv[1])
    want = [set(), set(), set(), set()]
    want[0] = {int(l, 16) for l in (work / "pose_keys.txt").read_text().split()}
    names = [f["name"] for f in json.loads((work / "rounds.json").read_text())["files"]]
    bad = 0
    for i, blob in round_files(work).items():
        if names[i] == "front":
            continue
        have = pack_keys(blob)
        miss = [w - h for w, h in zip(want, have)]
        if any(miss):
            bad += 1
            print(f"FAIL R{i:03d} {names[i]}: missing per section (sprite, scroll 1, 2, 3) {[len(x) for x in miss]}, first {[hex(k) for x in miss for k in sorted(x)[:2]]}")
    print(f"{'FAIL' if bad else 'PASS'}: {bad} of {len(names) - 1} stage files miss pose keys (wanted per section {[len(w) for w in want]})")
    sys.exit(1 if bad else 0)


main()
