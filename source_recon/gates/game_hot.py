"""Gate for saturn/game/game_hot.c. Registers and flags the bind leaves are compared through a pseudo block at 0xffe000, because the lifted game reads them.
Flags are compared only where a caller reads them (the lifter's CCOUT set); other units report 0."""
import ctypes
from unicorn import UC_PROT_ALL
from unicorn.m68k_const import UC_M68K_REG_A0, UC_M68K_REG_D0, UC_M68K_REG_SR
SOURCES = ["../saturn/game/game_hot.c"]
BLOCK = 0xffe000
_ram = None


def setup(rom):
    """The game's word pointers sign-extend to 0xffffxxxx; the board has a 24-bit bus, Unicorn doesn't. Same buffer at both addresses."""
    global _ram
    _ram = ctypes.create_string_buffer(0x10000)
    rom.u.mem_unmap(0xff0000, 0x10000)
    rom.u.mem_map_ptr(0xff0000, 0x10000, UC_PROT_ALL, _ram)
    rom.u.mem_map_ptr(0xffff0000, 0x10000, UC_PROT_ALL, _ram)


def after_run(rom, regs, out, calls):
    u = rom.u
    for i in range(15):
        v = u.reg_read((UC_M68K_REG_D0 + i) if i < 8 else (UC_M68K_REG_A0 + i - 8)) & 0xffffffff
        for k in range(4):
            b = (v >> (24 - 8 * k)) & 0xff
            if b:
                out[BLOCK + i * 4 + k] = b
    if regs.get("flags"):
        keep = u.reg_read(UC_M68K_REG_SR) & 0xd   # N, Z, C; V is always clear on these exits
        if keep:
            out[BLOCK + 60] = keep
    return out, calls


def noise(rng):
    r = {f"d{i}": rng.randrange(1 << 32) for i in range(8)}
    r.update({f"a{i}": rng.randrange(1 << 24) for i in range(7)})
    r["a5"] = 0xff8000
    return r


def word(s, a, v):
    s += [(a, (v >> 8) & 0xff), (a + 1, v & 0xff)]


def gen_prune(rng):
    # Flags not compared: this exit is moveq, and Unicorn's SR read at the stop point does not show its Z. Host check covers the callers.
    r, s = noise(rng), []
    density = rng.choice([0, .1, .5])
    for i in range(128):
        if rng.random() < density:
            p = rng.randrange(0x9000, 0xd000, 2)
            word(s, 0xff18fe + i * 2, p)
            s += [(0xff0000 + p, rng.choice([0, 1, 2])), (0xff0004 + p, rng.randrange(8))]
        elif rng.random() < .02:
            word(s, 0xff18fe + i * 2, rng.randrange(0x100, 0x7000, 2))   # a word pointer that reaches ROM
    return r, s


def gen_sort(rng):
    r, s = noise(rng), []
    n = rng.choice([0, 1, 2, 3, 5, 8, 16, 40])
    base = rng.randrange(0xa000, 0xb000, 2)
    s.append((0xffee91, n))
    word(s, 0xffee7a, base)
    for i in range(n):
        p = rng.randrange(0xc000, 0xdf00, 2)
        word(s, 0xff0000 + base + i * 2, p)
        word(s, 0xff0018 + p, rng.choice([0x40, 0x41, rng.randrange(0x10000)]))
    return r, s


def gen_origin(rng):
    r, s = noise(rng), []
    r["flags"] = 1
    a4, a0 = rng.randrange(0xc000, 0xd000, 2), rng.randrange(0xa000, 0xb000, 2)
    r["a4"], r["a0"] = 0xff0000 + a4, 0xff0000 + a0
    s.append((0xff0000 + a4 + 0xf, rng.randrange(256)))
    for a in (a4 + 0x10, a4 + 0x11, a4 + 0x14, a4 + 0x15, 0x8278, 0x8279, 0x827c, 0x827d, a0, a0 + 1, a0 + 2, a0 + 3):
        s.append((0xff0000 + a, rng.randrange(256)))
    return r, s


def gen_melee(rng):
    r, s = noise(rng), []
    a6, a1, a0, anim, boxes = 0xc000, 0xc200, 0xc400, 0xc600, 0xc800
    r["a6"], r["a1"], r["a0"] = 0xff0000 + a6, 0xff0000 + a1, 0xff0000 + a0
    at = lambda a: 0xff0000 + a
    s += [(at(a6 + 0x4c), rng.choice([0, 0, 0, 1])), (at(a1 + 0x93), rng.choice([0, 0, 0, 1])), (at(a1), rng.choice([1, 1, 1, 0])),
          (at(a1 + 0xd2), rng.choice([3, 1])), (at(a6 + 0xf), rng.choice([0, 1])), (at(a1 + 0xf), rng.choice([0, 1]))]
    y = rng.randrange(0x10000)
    word(s, at(a6 + 0x18), y)
    word(s, at(a1 + 0x18), (y + rng.randrange(-12, 12)) & 0xffff)
    word(s, at(a6 + 0x1c), 0xff)
    word(s, at(a6 + 0x1e), anim)
    word(s, at(a6 + 0x50), 0xff)
    word(s, at(a6 + 0x52), boxes)
    idx, head = rng.randrange(1, 8), rng.randrange(0, 0x40, 2)   # idx 0 with head 0 would seed over the head word
    s.append((at(anim + 8), idx))
    word(s, at(boxes), head)
    box = boxes + head + idx * 8
    s += [(at(box), rng.randrange(256)), (at(box + 2), rng.randrange(256))]
    word(s, at(a1 + 0x84), rng.randrange(0x10000) if rng.random() < .3 else rng.randrange(64))
    x = rng.randrange(0x10000)
    word(s, at(a6 + 0x10), x)
    word(s, at(a1 + 0x10), (x + rng.randrange(-200, 200)) & 0xffff)
    word(s, at(a0 + 6), rng.choice([0xffff, rng.randrange(0x200)]))
    return r, s


UNITS = {
    "target_list_prune": dict(entry=0x209d4, gen=gen_prune),
    "draw_list_sort": dict(entry=0xaa840, gen=gen_sort),
    "sprite_origin_compute": dict(entry=0xaa59a, gen=gen_origin),
    "melee_candidate_check": dict(entry=0x1689a, gen=gen_melee),
}
