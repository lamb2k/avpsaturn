"""Keep known arcade sprite keys out of the generated Wolverine remap."""

import json
import shutil


TILE_BYTES = 128
BLANK = b"\xff" * TILE_BYTES


def prepare(assets, stock_gfx, output, protected, allocated):
    remap_path = assets / "remap.json"
    remap = json.loads(remap_path.read_bytes())
    guest_keys = set(remap["keys"])
    overlap = sorted(guest_keys & protected)
    if not overlap:
        return assets

    stock = stock_gfx.read_bytes()
    guest = bytearray((assets / "gfx_wolverine.bin").read_bytes())
    if len(stock) != len(guest) or len(stock) < 0x800000:
        raise ValueError("Incompatible arcade and Wolverine graphics regions")
    occupied = guest_keys | allocated | protected
    free = [key for key in range(1, 0xFFFF) if key not in occupied]
    free.sort(key=lambda key: (stock[key * TILE_BYTES:(key + 1) * TILE_BYTES] != BLANK, key))
    if len(free) < len(overlap):
        raise ValueError("Wolverine remap has too few free keys to preserve Warrior's grab tiles")

    moved = dict(zip(overlap, free))
    for old, new in moved.items():
        start, target = old * TILE_BYTES, new * TILE_BYTES
        guest[target:target + TILE_BYTES] = guest[start:start + TILE_BYTES]
        guest[start:start + TILE_BYTES] = stock[start:start + TILE_BYTES]
    remap["keys"] = [moved.get(key, key) for key in remap["keys"]]
    remap["stage_keys"] = {stage: sorted(moved.get(key, key) for key in keys)
                           for stage, keys in remap["stage_keys"].items()}
    if "wv_added" in remap:
        remap["wv_added"]["keys"] = [moved.get(key, key) for key in remap["wv_added"]["keys"]]

    output.mkdir(parents=True, exist_ok=True)
    if (assets / "boxes.json").exists():
        shutil.copyfile(assets / "boxes.json", output / "boxes.json")
    (output / "gfx_wolverine.bin").write_bytes(guest)
    (output / "remap.json").write_text(json.dumps(remap))
    print(f"Wolverine remap moved {len(moved)} tiles away from Warrior's grab")
    return output
