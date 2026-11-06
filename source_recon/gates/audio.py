"""Gate definitions for the sound command path. Adds the Z80 mailbox range and hides the helper register save area."""
import pathlib
SOURCES = ["avsrc_audio.c", "avsrc_fade.c"]
SHARED = (0x618000, 0x2000)
# 0xff0e88..0xff0e9b only shuttles caller registers (0x1a36/0x1a4c, no other reader); not behaviour.
IGNORE = (0xff0e88, 0xff0e9c)
OP = pathlib.Path("C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot/.deps/mame/actorprobe/decrypted_opcodes_2m.bin")


def setup(rom):
    """pc-relative word tables the merged image lacks: read them through opcode space, as the board does."""
    op = OP.read_bytes()
    for a, n in ((0x3aec, 96), (0x3c32, 44), (0x1acc, 4), (0x1af6, 4), (0x1b20, 4), (0x1b4a, 4), (0x1b74, 4)):
        rom.u.mem_write(a, op[a:a + n])
    rom.u.mem_map(SHARED[0], SHARED[1])
    rom.extra = [SHARED]
    rom.ignore = [IGNORE]
    rom.stack = 0xff7f00           # the default stack overlaps the ring end and music state


def ring(rng, s):
    head = rng.randrange(64) * 16
    tail = rng.choice([head, head, (head - 16) & 0x3f0, (head + 16) & 0x3f0, rng.randrange(64) * 16])
    s += [(0xff801e, head >> 8), (0xff801f, head & 255), (0xff8020, tail >> 8), (0xff8021, tail & 255)]
    for i in range(0, 0x400):
        if rng.random() < .3:
            s.append((0xff0a88 + i, rng.randrange(256)))
    s += [(0xff81ad, rng.choice([0, 1])), (0xff81b0, rng.choice([0, 0, 1])), (0xff81d2, rng.choice([0, 1, 0x80]))]
    w = rng.choice([0, 1, 2, 0x100, rng.randrange(0x10000)])
    s += [(0xff837c, w >> 8), (0xff837d, w & 255)]
    s.append((0x61801f, rng.choice([0xff, 0xff, 0, 0x55])))
    return s


def args(rng):
    return dict(d0=rng.randrange(1 << 32), d1=rng.randrange(1 << 32), d2=rng.randrange(1 << 32), d3=rng.randrange(1 << 32))


def gen_ring(rng):
    return args(rng), ring(rng, [])


def gen_actor(rng):
    s = ring(rng, [])
    a6 = 0xff9000 + rng.randrange(64) * 0x80
    x = rng.choice([rng.randrange(0x10000), rng.randrange(0x400)])
    c = rng.choice([0, rng.randrange(0x400), rng.randrange(0x10000)])
    s += [(a6 + 0x10, x >> 8), (a6 + 0x11, x & 255), (0xff8278, c >> 8), (0xff8279, c & 255)]
    for t in (0xff0ea4, 0xff0ea5, 0xff0ea6, 0xff0ea7, 0xff0ea8):
        s.append((t, rng.choice([0, 2])))
    r = args(rng)
    r["a6"] = a6
    return r, s


def gen_music(rng):
    s = ring(rng, [])
    for i in range(4):
        s.append((0xff0e9c + i, rng.randrange(256)))
    sel = rng.randrange(11) * 4
    req = rng.choice([rng.randrange(256), 0xffff, 0x100 | rng.randrange(256), 0x7f00 | rng.randrange(256), 0x8000 | rng.randrange(256)])
    if rng.random() < .3:
        s.append((0xff0e9f, req & 255))
    r = args(rng)
    r["d0"] = (sel << 16) | req
    return r, s


def alt(entry):
    return dict(entry=entry, gen=gen_actor)


UNITS = {
    "audio_ring_clear": dict(entry=0x195c, gen=gen_ring),
    "audio_enqueue_always": dict(entry=0x1922, gen=gen_ring),
    "audio_enqueue": dict(entry=0x1916, gen=gen_ring),
    "audio_send_pending": dict(entry=0x188a, gen=gen_ring),
    "audio_vblank_tick": dict(entry=0x1870, gen=gen_ring),
    "audio_stop_all": dict(entry=0x1972, gen=gen_ring),
    "audio_key_off_channel": dict(entry=0x1992, gen=gen_ring),
    "audio_stop_music": dict(entry=0x19c4, gen=gen_ring),
    "audio_control_6": dict(entry=0x19d2, gen=gen_ring),
    "audio_control_7": dict(entry=0x19de, gen=gen_ring),
    "audio_control_8": dict(entry=0x19ea, gen=gen_ring),
    "audio_control_9": dict(entry=0x19f6, gen=gen_ring),
    "audio_control_a": dict(entry=0x1a02, gen=gen_ring),
    "audio_control_b": dict(entry=0x1a0c, gen=gen_ring),
    "audio_control_c": dict(entry=0x1a16, gen=gen_ring),
    "audio_control_d": dict(entry=0x1a22, gen=gen_ring),
    "audio_alt_1aa6": alt(0x1aa6),
    "audio_alt_1ad0": alt(0x1ad0),
    "audio_alt_1afa": alt(0x1afa),
    "audio_alt_1b24": alt(0x1b24),
    "audio_alt_1b4e": alt(0x1b4e),
    "audio_music_request": dict(entry=0x3bdc, gen=gen_music),
}
