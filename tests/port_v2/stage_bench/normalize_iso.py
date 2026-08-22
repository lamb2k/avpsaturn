#!/usr/bin/env python3
"""Normalize only ISO-9660 timestamps for the stage salvage diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import directory_record, read_iso_path  # noqa: E402


SECTOR = 2048
VOLUME_TIME = b"2026082116000000\x00"
UNSPECIFIED_TIME = b"0000000000000000\x00"
RECORD_TIME = bytes((126, 8, 21, 16, 0, 0, 0))


def sha(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(image: bytearray) -> tuple[int, int, int, int]:
    before = bytes(image)
    descriptors = 0
    roots: list[tuple[int, int]] = []
    generator_sectors = 0
    sector = 16
    while True:
        base = sector * SECTOR
        kind = image[base]
        if image[base + 1:base + 6] != b"CD001":
            raise ValueError(f"invalid volume descriptor at sector {sector}")
        if kind in (1, 2):
            descriptors += 1
            image[base + 813:base + 830] = VOLUME_TIME
            image[base + 830:base + 847] = VOLUME_TIME
            image[base + 847:base + 864] = UNSPECIFIED_TIME
            image[base + 864:base + 881] = UNSPECIFIED_TIME
            extent, size, _, _ = directory_record(image, base + 156)
            image[base + 174:base + 181] = RECORD_TIME
            roots.append((extent, size))
        if kind == 255:
            generator = base + SECTOR
            if image[generator:generator + 4] == b"MKI ":
                image[generator:generator + SECTOR] = bytes(SECTOR)
                generator_sectors += 1
            break
        sector += 1
    visited: set[tuple[int, int]] = set()
    records = 0

    def walk(extent: int, size: int) -> None:
        nonlocal records
        if (extent, size) in visited:
            return
        visited.add((extent, size))
        base = extent * SECTOR
        offset = 0
        children: list[tuple[int, int]] = []
        while offset < size:
            absolute = base + offset
            length = image[absolute]
            if length == 0:
                offset = ((offset // SECTOR) + 1) * SECTOR
                continue
            child_extent, child_size, flags, name = directory_record(
                image, absolute)
            image[absolute + 18:absolute + 25] = RECORD_TIME
            records += 1
            if flags & 2 and name not in (".", ".."):
                children.append((child_extent, child_size))
            offset += length
        for child in children:
            walk(*child)

    for root in roots:
        walk(*root)
    changed = sum(a != b for a, b in zip(before, image))
    return descriptors, records, generator_sectors, changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(
        encoding="utf-8"))
    image_path = ROOT / "game.iso"
    raw = image_path.read_bytes()
    before = {name: sha(read_iso_path(raw, name))
              for name in inventory["required_iso_members"]}
    normalized = bytearray(raw)
    descriptors, records, generators, changed = normalize(normalized)
    after = {name: sha(read_iso_path(normalized, name))
             for name in inventory["required_iso_members"]}
    if before != after or changed == 0:
        raise ValueError("normalization changed payloads or no metadata")
    temporary = image_path.with_suffix(".iso.normalized")
    temporary.write_bytes(normalized)
    temporary.replace(image_path)
    normalized_hash = sha(normalized)
    manifest = ROOT / "build/hardware_release_manifest.txt"
    lines = manifest.read_text(encoding="ascii").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("iso_sha256="):
            lines[index] = f"iso_sha256={normalized_hash}"
            break
    else:
        raise ValueError("hardware manifest has no ISO identity")
    manifest.write_text("\r\n".join(lines) + "\r\n", encoding="ascii")
    report = {
        "schema": 1, "raw_iso_sha256": sha(raw),
        "normalized_iso_sha256": normalized_hash,
        "changed_byte_count": changed,
        "volume_descriptor_count": descriptors,
        "directory_record_count": records,
        "generator_metadata_sector_count": generators,
        "required_payload_sha256": after,
        "production_payload_changed": False,
        "physical_saturn": "UNRUN",
    }
    output = ROOT / f"build/port_v2/stage_bench/run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"normalized stage ISO: {normalized_hash}")


if __name__ == "__main__":
    main()
