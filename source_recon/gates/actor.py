"""Gate definitions for pools, spawn table, damage, hit commit and the emitter.
A run can report a4 at scratch 0xff0e00 (Unicorn does not expose the live condition codes), and can ignore d0 at
stubbed calls where it is only scratch in the routine."""
import ctypes
import struct
import sys

from unicorn import UC_PROT_ALL
from unicorn.m68k_const import UC_M68K_REG_A4

SOURCES = ["avsrc_actor.c", "avsrc_fade.c"]
# pc-relative data these units read through opcode space, beyond what merged.bin carries (it stops at 64 bytes).
OP_READS = ((0x1be6a, 6), (0x1be82, 76), (0x1c14c, 24), (0x1b4bc, 16), (0x1d612, 16))
IMG = sys.modules["__main__"].overlay(OP_READS)


def setup(rom):
    """Word pointers sign-extend to 0xffffxxxx; the board's 24-bit bus folds them onto RAM."""
    rom._ram = ctypes.create_string_buffer(0x10000)
    rom.u.mem_unmap(0xff0000, 0x10000)
    rom.u.mem_map_ptr(0xff0000, 0x10000, UC_PROT_ALL, rom._ram)
    rom.u.mem_map_ptr(0xffff0000, 0x10000, UC_PROT_ALL, rom._ram)


def after_run(rom, regs, out, calls):
    if regs.get("_result"):
        a4 = rom.u.reg_read(UC_M68K_REG_A4) & 0xffff
        if a4 >> 8:
            out[0xff0e00] = a4 >> 8
        if a4 & 255:
            out[0xff0e01] = a4 & 255
    if regs.get("_nod0"):
        calls = [(a, 0) for a, _ in calls]
    if regs.get("_ncalls") and calls:
        out[0xff0e04] = len(calls) & 255   # traversal changes no memory itself; its calls are the behaviour
    return out, calls


PA = dict(p4=0x1773e, p8=0x17654, p12=0x1769e, p16=0x1778c, p20=0x176f0, p24=0x177da, p28=0x17828, p32=0x178a8, p36=0x17876, p40=0x178da)
PR = dict(p4=0x17754, p8=0x1766a, p12=0x176b4, p16=0x177a2, p20=0x17706, p24=0x177f0, p28=0x1783e, p32=0x178be, p36=0x1788c, p40=0x178f0)
POOLS = [  # name, first, n, stride, count, top, stack_end, dispatch, traverse entry, classes
    ("p4", 0xff8680, 24, 0x80, 0xffee7c, 0xffee50, 0xffee92, 0x1b878, 0x1b846, 17),
    ("p8", 0xff9280, 4, 0xc0, 0xffee7e, 0xffee54, 0xffeef2, 0x1b958, 0x1b916, 7),
    ("p12", 0xff9580, 20, 0xc0, 0xffee80, 0xffee58, 0xffeeea, 0x1b9b6, 0x1b974, 43),
    ("p16", 0xffa480, 20, 0x80, 0xffee83, 0xffee5e, 0xffef1a, 0x1b8ee, 0x1b8bc, 10),
    ("p20", 0xffae80, 16, 0x80, 0xffee85, 0xffee62, 0xffef3a, 0x1bc7a, 0x1bc38, 24),
    ("p24", 0xffb680, 32, 0x80, 0xffee89, 0xffee6a, 0xffef7a, 0x1ba94, 0x1ba62, 105),
    ("p28", 0xffc680, 16, 0x80, 0xffee8c, 0xffee70, 0xffef9a, 0x1bd0c, 0x1bcda, 15),
    ("p32", 0xffce80, 4, 0x100, 0xffee8e, 0xffee74, 0xffefa2, 0, 0, 0),
    ("p36", 0xffd280, 64, 0x40, 0xffee8f, 0xffee76, 0xfff022, 0x1bd7a, 0x1bd48, 17),
    ("p40", 0xffe280, 16, 0x80, 0xffee90, 0xffee78, 0xfff042, 0, 0, 0),
]


def w16(s, a, v):
    s += [(a, v >> 8 & 255), (a + 1, v & 255)]


def rand_bytes(rng, s, a, n, k):
    for _ in range(k):
        s.append((a + rng.randrange(n), rng.randrange(256)))


def seed_pool(rng, s, p):
    """Valid pool state: a count, a top inside the stack and real slots above it."""
    name, first, n, stride, count, top, end, *_ = p
    c = rng.choice([0, 1, 2, rng.randrange(n + 1)])
    s.append((count, c))
    t = (end + 2 * rng.randrange(n)) if name == "p4" else (end - 2 * rng.randrange(max(c, 1), n + 1))
    w16(s, top, t & 0xffff)
    for i in range(max(c, 1)):
        w16(s, t + i * 2, first + stride * rng.randrange(n))


def gen_alloc(p):
    def g(rng):
        s = []
        seed_pool(rng, s, p)
        return dict(_result=True), s
    return g


def gen_release(p):
    def g(rng):
        name, first, n, stride, count, top, end, *_ = p
        s = []
        slot = first + stride * rng.randrange(n)
        rand_bytes(rng, s, slot, stride, 60)
        s.append((count, rng.randrange(n)))
        t = end + 2 * rng.randrange(1, n) if name == "p4" else end - 2 * rng.randrange(1, n + 1)
        w16(s, top, t & 0xffff)
        return dict(a6=slot), s
    return g


def gen_traverse(p):
    first, n, stride, limit = p[1], p[2], p[3], p[9]

    def g(rng):
        s = []
        for i in range(n):
            slot = first + stride * i
            if rng.random() < 0.4:
                s.append((slot, rng.randrange(1, 4)))
                s.append((slot + 2, rng.randrange(limit)))
                s.append((slot + 0x48, rng.choice([0, 1, 2])))
                s.append((slot + 0x47, rng.randrange(256)))
        rand_bytes(rng, s, 0xff83f4, 2, 1)
        rand_bytes(rng, s, 0xff221c, 2, 1)
        return dict(_ncalls=True), s
    return g


def entries(p):
    base, n = p[7], p[9]
    return tuple(sorted({struct.unpack(">I", IMG[base + i * 4:base + i * 4 + 4])[0] for i in range(n)}))


def gen_reset(rng):
    s = []
    for b, n, k in ((0xff8680, 0x5c00, 400), (0xffe280, 0x800, 40), (0xffea80, 0x40, 16), (0xff8228, 0x40, 16),
                    (0xff1738, 0x10, 8), (0xff18fe, 0x100, 30), (0xff19fe, 0x80, 30), (0xff1b14, 6, 4), (0xff221c, 2, 2),
                    (0xffee50, 0x42, 30), (0xff1eaa, 2, 2)):
        rand_bytes(rng, s, b, n, k)
    return dict(_nod0=True), s


def walk_entry(stage, steps):
    e = struct.unpack(">I", IMG[0x1be82 + stage * 2:0x1be82 + stage * 2 + 4])[0]
    for _ in range(steps):
        if struct.unpack(">H", IMG[e:e + 2])[0] & 0x8000:
            break
        e += 16
    return e


NEG_ROWS = []
for _t in range(19):
    _e = struct.unpack(">I", IMG[0x1be82 + _t * 4:0x1be86 + _t * 4])[0]
    while not IMG[_e] & 0x80:
        if IMG[_e + 10] >= 0x80:
            NEG_ROWS.append(_e)
        _e += 16


def gen_spawn(rng):
    s = []
    stage = rng.randrange(19) * 2
    w16(s, 0xff81e8, stage)
    s.append((0xff820e, rng.randrange(4)))
    phase = rng.choice([0, 2, 2, 2, 4])
    s.append((0xff1816, phase))
    e = walk_entry(stage, rng.randrange(60))
    if rng.random() < 0.15 and NEG_ROWS:
        e = rng.choice(NEG_ROWS)   # only a few rows gate on "below this difficulty"
    for i, b in enumerate(struct.pack(">I", e)):
        s.append((0xff1812 + 0x1c + i, b))
    cam = struct.unpack(">H", IMG[e:e + 2])[0]
    w16(s, 0xff8278, rng.choice([0, 0x7fff, cam, cam, (cam + rng.randrange(0, 0x400)) & 0xffff, max(cam - 1, 0)]))
    # difficulty at the edge of this entry's gate, so both sides of the compare are exercised
    gate = IMG[e + 10]
    edge = (0x100 - gate) & 255 if gate & 0x80 else gate
    w16(s, 0xff81ea, rng.choice([rng.randrange(32), edge & 31, max(edge - 1, 0) & 31]))
    for p in POOLS:
        seed_pool(rng, s, p)
    return dict(a6=0xff1812), s


def gen_damage(rng):
    s = []
    a6, a1 = 0xff9580, 0xff9640
    if rng.random() < 0.5:
        a1 = 0xff8380
    s.append((a1 + 8, 0 if a1 == 0xff8380 else 0x0c))
    s.append((a6 + 8, rng.choice([0, 0x0c])))
    a3 = 0xff2000
    s.append((a3 + 9, rng.randrange(256)))
    w16(s, 0xff81ea, rng.randrange(32))
    s.append((a6 + 0x5e, rng.randrange(8)))
    s.append((a1 + 0x57, rng.randrange(16)))
    s.append((a1 + 0x73, rng.choice([0, 0, 1])))
    s.append((a1 + 2, rng.choice([0x11, 3])))
    s.append((0xff8244, rng.choice([0, 1])))
    s.append((a1 + 0xd1, rng.randrange(4)))
    w16(s, 0xff189e, rng.choice([0, 0, 0, 1]))
    w16(s, a1 + 0x40, rng.randrange(0x66))
    return dict(a6=a6, a1=a1, a3=a3), s


def gen_drain(rng):
    s = []
    a6 = 0xff8380
    s.append((a6 + 0x9f, rng.randrange(3)))
    w16(s, a6 + 0x40, rng.randrange(0x66))
    return dict(a6=a6), s


def gen_heal(rng):
    s = []
    a6, a4 = 0xff8380, 0xff8680
    s.append((a4 + 3, rng.randrange(8)))
    w16(s, a6 + 0x40, rng.choice([0, 0x65, rng.randrange(0x66)]))
    s.append((a6 + 0xd1, rng.randrange(2)))
    return dict(a6=a6, a4=a4), s


def gen_hit(rng):
    s = []
    a6, a1, a3 = 0xff9580, rng.choice([0xff9640, 0xff8380]), 0xff2000
    s.append((a1 + 8, 0 if a1 == 0xff8380 else 0x0c))
    s.append((a6 + 8, 0x0c))
    s.append((a3 + 0xe, rng.randrange(256)))
    s.append((a3 + 0xa, rng.choice([0, 1, 0x80, 0xff])))
    s.append((a6 + 0x2c, rng.choice([0, 0, 3])))
    s.append((a1 + 0x2c, rng.randrange(256)))
    s.append((a6 + 0x67, rng.randrange(256)))
    s.append((a6 + 0x0f, rng.choice([0, 1])))
    s.append((a6 + 0xd1, rng.randrange(4)))
    s.append((a6 + 0x65, rng.choice([0, 1, 2, 3, 0xff])))
    w16(s, a6 + 0x10, rng.randrange(0x10000))
    w16(s, a1 + 0x10, rng.randrange(0x10000))
    return dict(a6=a6, a1=a1, a3=a3, _nod0=True), s


def gen_emitter(rng):
    s = []
    a6 = 0xffc680
    w16(s, a6 + 0x2a, rng.choice([0, 0, 1, 0x30, rng.randrange(0x10000)]))
    for a in (0xff822a, 0xff81f3, 0xff8208):
        s.append((a, rng.choice([0, 0, 0, 0, 0, 1])))
    for f in (0x10, 0x14, 0x18):
        w16(s, a6 + f, rng.randrange(0x10000))
    seed_pool(rng, s, POOLS[5])
    return dict(a6=a6), s


UNITS = {}
for i, p in enumerate(POOLS):
    UNITS[f"pool_alloc_{i}"] = dict(entry=PA[p[0]], gen=gen_alloc(p))
    UNITS[f"pool_release_{i}"] = dict(entry=PR[p[0]], gen=gen_release(p))
    if p[7]:
        UNITS[f"pool_traverse_{i}"] = dict(entry=p[8], stubs=entries(p), gen=gen_traverse(p))
UNITS.update({
    "pools_reset": dict(entry=0x1729c, stubs=(0x1c164, 0xae2f4, 0x1d6fa), gen=gen_reset),
    "spawn_table_step": dict(entry=0x1be5e, stubs=(0x17a1e, 0xad580), gen=gen_spawn),
    "damage_apply": dict(entry=0x1d504, gen=gen_damage),
    "player_energy_drain": dict(entry=0x1b492, gen=gen_drain),
    "pickup_heal": dict(entry=0xbc60a, stubs=(0xabdd2,), gen=gen_heal),
    "hit_commit_single": dict(entry=0x1cfca, stubs=(0x1d73a, 0x1d314, 0x1d504, 0x1d492, 0x1d622, 0x1d6e2), gen=gen_hit),
    "hit_commit_player": dict(entry=0x1d0a8, stubs=(0x1d314, 0x1d504, 0x1d492, 0x1d622, 0x1d6e2), gen=gen_hit),
    "hit_commit_row65": dict(entry=0x1d186, stubs=(0x1d314, 0x1d504, 0x1d492, 0x1d622, 0x1d6e2), gen=gen_hit),
    "emitter_tick": dict(entry=0xa7394, stubs=(0x16536, 0x16518), gen=gen_emitter),
})
