"""Gate definitions for the fade and command ring units."""
SOURCES = ["avsrc_fade.c"]
def pal(rng, n=None):
    s = []
    for b in range(4):
        for p in range(32):
            if rng.random() < 0.6:
                base = 0x90c000 + b * 0x400 + p * 0x20
                top = rng.choice([0, 0, 1, 0xf, rng.randrange(16)])
                s.append((base, (top << 4) | rng.randrange(16)))
                for i in range(1, 32):
                    if rng.random() < .3:
                        s.append((base + i, rng.randrange(256)))
    return s
def gen_ring(rng):
    head = rng.randrange(64) * 4
    tail = rng.choice([head, (head + 4) & 0xfc, rng.randrange(64) * 4])
    s = [(0xff801a, 0), (0xff801b, head), (0xff801c, 0), (0xff801d, tail)]
    return dict(d0=rng.randrange(0x10000), d1=rng.randrange(0x10000)), s
def gen_all(rng):
    s = pal(rng)
    for i in range(16):
        s.append((0xff8368 + i, rng.choice([0, 0xff, rng.randrange(256)])))
    return dict(d2=rng.choice([0xf000, 0x1000])), s
def gen_step(rng):
    s = pal(rng)
    for i in range(16):
        s.append((0xff8368 + i, rng.randrange(256)))
    b, p = rng.randrange(4), rng.randrange(32)
    # d7 holds the bit number; a1 the mask slot; the unit keeps them consistent with the address
    return dict(d2=rng.choice([0xf000, 0x1000]), d7=31 - p, a0=0x90c000 + b * 0x400 + p * 0x20,
                a1=0xff8368 + b * 4), s
UNITS = {
    "cmd_ring_push": dict(entry=0x1620a, gen=gen_ring),
    "palette_fade_step": dict(entry=0x1840e, gen=gen_step),
    "palette_fade_all": dict(entry=0x183b6, gen=gen_all),
}
