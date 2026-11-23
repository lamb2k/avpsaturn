"""Sprite keys emitted by the Predator Warrior grab and its follow-up punch."""

from decode_avsp_object_stream import Rom, decode_group_entries


def sprite_keys(program):
    rom = Rom(program)
    assemblies = {rom.u32(record + 4) for record in range(0x15F520, 0x15F580, 16)}
    keys = set()
    for assembly in assemblies:
        for facing in (0, 1):
            parts = decode_group_entries(rom, assembly + 2, 0, 0, 0, facing,
                                         or_value=0, mode_positive=False)
            for part in parts:
                code = int(part["code"], 16) + ((int(part["y"], 16) & 0x6000) << 3)
                attr = int(part["attr"], 16)
                width, height = ((attr >> 8) & 15) + 1, ((attr >> 12) & 15) + 1
                if attr & 0x60:
                    keys.update(code + 16 * y + x for y in range(height) for x in range(width))
                else:
                    keys.update((code & ~15) + 16 * y + ((code + x) & 15)
                                for y in range(height) for x in range(width))
    return keys
