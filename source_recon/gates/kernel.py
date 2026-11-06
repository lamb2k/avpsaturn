"""Gate definitions for the tick tail and fast-forward."""
SOURCES = ["avsrc_kernel.c", "avsrc_fade.c"]
def gen_tail(rng):
    t = 0xff0058 + rng.randrange(16) * 0x20
    s = [(0xff025c, 0), (0xff025d, 0xff), (0xff025e, (t >> 8) & 255), (0xff025f, t & 255),
         (t + 0x10, rng.choice([0, 1, 2, 3])), (0xff81bc, rng.choice([0, 0xff]))]
    return {}, s
def gen_ff(rng):
    s = [(0xff81b9, rng.choice([0, 1, 1]))]
    for i in range(16):
        t = 0xff0058 + i * 0x20
        s.append((t, rng.choice([0, 1, 1, 2, 4, 8, 0xc])))
        s.append((t + 1, rng.choice([0, 1, 1, 2, 5, 255])))
    return dict(d0=0), s
def gen_hold(rng):
    n = rng.choice([0, 0, 1, 2, 4, 5])
    s = [(0xff823a, rng.choice([0, 1])), (0xff1744, 0), (0xff1745, n), (0xff81bf, rng.randrange(8)), (0xff81b9, rng.choice([0, 1]))]
    for i in range(3):
        s.append((0xff8064 + 2 * i, rng.choice([0, 0, 0x80, 1, 0x10, rng.randrange(256)])))
    return {}, s
UNITS = {
    "hold_button_fast_forward": dict(entry=0x17080, gen=gen_hold),
    "tick_tail": dict(entry=0x8140, stubs=(0x1060,), gen=gen_tail),
    "idle_fast_forward": dict(entry=0x14b44, stubs=(0x14b70,), gen=gen_ff),
}
