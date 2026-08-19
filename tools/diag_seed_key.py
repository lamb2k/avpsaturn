"""Which actor field, added to (type, action), predicts the anim record?

(type, action) alone is falsified: type 12 / action 0x0000 shows 65
distinct records over 194 action-change observations. This scans every
byte and word offset in the 0xC0 actor record, asking: if the key were
(type, action, THIS field), how unanimous would the seed table become?

Prints the offsets that most improve unanimity, weighted by observation
count, so a real second key field is separated from noise (a field that
merely varies per instance will also split the keys - it is disqualified
by exploding the key count without raising coverage of repeated keys).

Untracked one-off diagnostic (tools/diag_*), kept per project convention.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")
WORKRAM_BASE = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_ANCHOR = 0xFF8380
ACTOR_STRIDE = 0xC0
PROGRAM_FIRST = 0x100000
PROGRAM_LAST = 0x200000


def u16(b, o):
    return (b[o] << 8) | b[o + 1]


def u32(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def collect():
    """All action-change observations as (record, full actor record)."""
    out = []
    for route in ROUTES:
        root = ROOT / ".deps" / "mame" / route
        if not root.is_dir():
            continue
        previous = {}
        for path in sorted(root.glob("workram_*.bin")):
            work = path.read_bytes()
            if len(work) != WORKRAM_SIZE:
                continue
            n = 0
            while True:
                off = (ACTOR_ANCHOR - WORKRAM_BASE) + n * ACTOR_STRIDE
                if off + ACTOR_STRIDE > len(work):
                    break
                rec = work[off:off + ACTOR_STRIDE]
                n += 1
                if rec[0x00] != 1:
                    previous.pop((route, n), None)
                    continue
                record = u32(rec, 0x1C)
                if not (PROGRAM_FIRST <= record < PROGRAM_LAST):
                    continue
                key = (rec[0x08], u16(rec, 0x06))
                prev = previous.get((route, n))
                previous[(route, n)] = key
                if prev is None or prev == key:
                    continue
                out.append((record, bytes(rec)))
    return out


def score(observations, extra):
    """Unanimity of the seed table when the key includes `extra(rec)`."""
    groups = defaultdict(Counter)
    for record, rec in observations:
        key = (rec[0x08], u16(rec, 0x06), extra(rec))
        groups[key][record] += 1
    total = 0
    agreed = 0
    repeated_keys = 0
    for counter in groups.values():
        n = sum(counter.values())
        total += n
        agreed += counter.most_common(1)[0][1]
        if n > 1:
            repeated_keys += 1
    return agreed / total, len(groups), repeated_keys


def main() -> int:
    obs = collect()
    print("action-change observations: %d" % len(obs))
    base, nkeys, rep = score(obs, lambda rec: 0)
    print("baseline (type, action): unanimity %.3f over %d keys (%d repeated)"
          % (base, nkeys, rep))

    results = []
    for off in range(ACTOR_STRIDE):
        if off in (0x06, 0x07, 0x08, 0x1C, 0x1D, 0x1E, 0x1F):
            continue          # key fields and the answer itself
        u, nk, rp = score(obs, lambda rec, o=off: rec[o])
        results.append(("byte 0x%02X" % off, u, nk, rp))
    for off in range(0, ACTOR_STRIDE - 1, 2):
        if off in (0x06, 0x08, 0x1C, 0x1E):
            continue
        u, nk, rp = score(obs, lambda rec, o=off: u16(rec, o))
        results.append(("word 0x%02X" % off, u, nk, rp))

    # A useful field raises unanimity while keeping many keys REPEATED:
    # a per-instance nonce also reaches 1.0 but leaves every key singular.
    results.sort(key=lambda r: (-r[1], -r[3]))
    print("\ntop candidates (unanimity, keys, repeated keys):")
    for name, u, nk, rp in results[:18]:
        print("  %-10s unanimity %.3f  keys %4d  repeated %4d" %
              (name, u, nk, rp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
