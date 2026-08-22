#!/usr/bin/env python3
"""Build the source-measured HIT/KO tile overlay for CombatIntegrationBench.

The approved street TILES.BIN remains byte-identical.  Its actor-state corpus
decoder deliberately skips jump-record assemblies, while the promoted class
0x1F HIT/KO records use that family.  The active CPS2 object lists are the
source of truth for the missing bank-0x12 tiles in the exact promoted windows.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

import extract_avspu_stage1 as avsp  # noqa: E402
from gen_avsp_gfx_tiles import entry_tile_codes, tile_texture  # noqa: E402


SOURCE_WINDOWS = ((5191, 5227), (5330, 5469))
SOURCE_BANK = 0x13
MAGIC = 0x4156544C
OUT = ROOT / "build/avsp_cd/SPR4/COMBAT.BIN"
CONTRACT = HERE / "tile_overlay_contract.json"


def read_words(path: Path) -> list[int]:
    return [int(line.split("\t")[1], 16)
            for line in path.read_text(encoding="ascii").splitlines()[1:]]


def base_codes(path: Path) -> set[int]:
    data = path.read_bytes()
    count = int.from_bytes(data[4:8], "big")
    offset = int.from_bytes(data[12:16], "big")
    return {int.from_bytes(data[offset + index * 4:offset + index * 4 + 4],
                           "big") for index in range(count)}


def source_tiles() -> tuple[list[int], str, int]:
    root = ROOT / ".deps/mame/enemy_actions"
    tiles: set[int] = set()
    digest = hashlib.sha256()
    entries = 0
    for first, last in SOURCE_WINDOWS:
        for frame in range(first, last + 1):
            path = root / f"objram_active_{frame:05}.tsv"
            payload = path.read_bytes()
            digest.update(path.name.encode("ascii") + b"\0" + payload)
            words = read_words(path)
            for offset in range(0, len(words) - 3, 4):
                _x, y, code, attr = words[offset:offset + 4]
                if y >= 0x8000 or attr >= 0xFF00:
                    break
                if (attr & 0x1F) == SOURCE_BANK:
                    tiles.update(entry_tile_codes(code, y, attr))
                    entries += 1
    return sorted(tiles), digest.hexdigest(), entries


def palette_block() -> tuple[bytes, str]:
    path = ROOT / ".deps/mame/enemy_actions/palette_05140.tsv"
    palette = avsp.load_palette_path(path)
    bank_map = bytearray([0xFF] * 32)
    bank_map[SOURCE_BANK] = 0
    cram = bytearray()
    for pen in range(16):
        r, g, b, _a = palette[SOURCE_BANK * 16 + pen]
        color = 0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)
        cram += color.to_bytes(2, "big")
    return bytes(bank_map + cram), hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    approved = json.loads(
        (ROOT / "tests/port_v2/enemy/approved_contract.json").read_text())
    base = ROOT / "build/avsp_cd/SPR4/TILES.BIN"
    base_sha = hashlib.sha256(base.read_bytes()).hexdigest()
    if base_sha != approved["tile_archive_sha256"]:
        raise SystemExit("approved street tile archive identity drifted")
    all_tiles, object_sha, entry_count = source_tiles()
    codes = sorted(set(all_tiles) - base_codes(base))
    palette, palette_sha = palette_block()
    gfx = avsp.load_gfx_region()
    codes_offset = 0x10 + len(palette)
    blob = bytearray()
    blob += MAGIC.to_bytes(4, "big")
    blob += len(codes).to_bytes(4, "big")
    blob += (1).to_bytes(4, "big")
    blob += codes_offset.to_bytes(4, "big")
    blob += palette
    for code in codes:
        blob += code.to_bytes(4, "big")
    for code in codes:
        blob += tile_texture(gfx, code)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(blob)
    return {
        "schema": 1,
        "task_id": "INTEGRATE-02-COMBAT",
        "classification": "source-measured combat-profile tile overlay",
        "source_windows": [list(window) for window in SOURCE_WINDOWS],
        "source_palette_bank": SOURCE_BANK,
        "source_object_entry_count": entry_count,
        "source_object_lists_sha256": object_sha,
        "source_palette_sha256": palette_sha,
        "approved_base_archive_sha256": base_sha,
        "tile_count": len(codes),
        "tile_codes_sha256": hashlib.sha256(
            ",".join(f"0x{code:04x}" for code in codes).encode("ascii")
        ).hexdigest(),
        "archive_bytes": len(blob),
        "archive_sha256": hashlib.sha256(blob).hexdigest(),
        "physical_saturn": "UNRUN",
    }


def main() -> None:
    result = build()
    expected = json.loads(CONTRACT.read_text(encoding="ascii"))
    if result != expected:
        raise SystemExit("combat tile overlay contract drifted")
    print("Combat tile overlay: %d tiles, %d bytes, sha256=%s" %
          (result["tile_count"], result["archive_bytes"],
           result["archive_sha256"]))


if __name__ == "__main__":
    main()
