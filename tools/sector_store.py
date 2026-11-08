#!/usr/bin/env python
"""Shared sector store: every unique 2 KB sector of the round files R*.BIN once, in one disc file STORE.BIN, so the full game fits an 80-minute CD-R.
Layout (boot.c load_regions reads it):
  sector 0      u32 'SST1', u32 rounds, then per round u32 first run, u32 runs (round i at byte 8 + 8 i)
  sectors 1..   runs, u32 each: store sector << 14 | sectors (1..16383), all rounds' runs back to back
  then          data sectors, in first-use order (round 0, 1, ...), so a round's reads stay mostly sequential.
Reading a round's runs in order gives back its R*.BIN byte for byte; the loader then walks that stream exactly as it walks the file.
usage: sector_store.py DISC_DIR [--keep DIR]   writes STORE.BIN, verifies all rounds, moves R*.BIN to DIR (default: removed)."""
import hashlib, pathlib, shutil, struct, sys

SEC = 2048
MAGIC = 0x53535431
CMAX = (1 << 14) - 1


def build(files):
    """files: list of bytes (round files). Returns STORE.BIN bytes and per-round run lists."""
    where, data, rounds = {}, [], []
    for b in files:
        assert len(b) % SEC == 0
        runs = []
        for o in range(0, len(b), SEC):
            s = b[o:o + SEC]
            k = hashlib.blake2b(s, digest_size=16).digest()
            if k not in where:
                where[k] = len(data); data.append(s)
            q = where[k]
            if runs and runs[-1][0] + runs[-1][1] == q and runs[-1][1] < CMAX:
                runs[-1][1] += 1
            else:
                runs.append([q, 1])
        rounds.append(runs)
    nruns = sum(len(r) for r in rounds)
    if 8 + 8 * len(rounds) > SEC:
        raise SystemExit("sector store: too many rounds")
    run_secs = -(-nruns * 4 // SEC)
    base = 1 + run_secs
    if base + len(data) >= 1 << 18:
        raise SystemExit("sector store: too large")
    head = struct.pack(">II", MAGIC, len(rounds))
    tab, first = bytearray(), 0
    for r in rounds:
        head += struct.pack(">II", first, len(r)); first += len(r)
        for q, n in r:
            tab += struct.pack(">I", (base + q) << 14 | n)
    out = head + bytes(SEC - len(head)) + tab + bytes(run_secs * SEC - len(tab)) + b"".join(data)
    return out, rounds


def rebuild(store, i):
    """The round file as the loader's reads give it, from STORE.BIN alone."""
    magic, n = struct.unpack_from(">II", store)
    assert magic == MAGIC and i < n
    first, cnt = struct.unpack_from(">II", store, 8 + 8 * i)
    out = bytearray()
    for j in range(first, first + cnt):
        w = struct.unpack_from(">I", store, SEC + 4 * j)[0]
        q, c = w >> 14, w & CMAX
        out += store[q * SEC:(q + c) * SEC]
    return bytes(out)


def main():
    disc = pathlib.Path(sys.argv[1])
    keep = pathlib.Path(sys.argv[sys.argv.index("--keep") + 1]) if "--keep" in sys.argv else None
    names = sorted(disc.glob("R[0-9][0-9][0-9].BIN"))
    nums = [int(p.stem[1:]) for p in names]
    if nums != list(range(len(nums))):
        raise SystemExit("sector store: round files not numbered 0..n-1")
    files = [p.read_bytes() for p in names]
    store, rounds = build(files)
    bad = [i for i, b in enumerate(files) if rebuild(store, i) != b]
    if bad:
        raise SystemExit(f"sector store: rounds differ {bad}")
    (disc / "STORE.BIN").write_bytes(store)
    if keep:
        keep.mkdir(parents=True, exist_ok=True)
        for p in keep.glob("R[0-9][0-9][0-9].BIN"):
            p.unlink()
    for p in names:
        shutil.move(str(p), keep / p.name) if keep else p.unlink()
    old = sum(len(b) for b in files) // SEC
    print("sector store", dict(rounds=len(files), round_sectors=old, store_sectors=len(store) // SEC,
                               runs=sum(len(r) for r in rounds), max_runs=max(len(r) for r in rounds), identical=len(files) - len(bad)))


if __name__ == "__main__":
    main()
