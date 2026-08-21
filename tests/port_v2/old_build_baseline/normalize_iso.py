#!/usr/bin/env python3
"""Normalize only ISO-9660 timestamps for a deterministic diagnostic disc."""

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


def normalize(image: bytearray) -> tuple[int, int, int]:
    before = bytes(image)
    descriptor_count = 0
    root_directories: list[tuple[int, int]] = []
    sector = 16
    while True:
        base = sector * SECTOR
        kind = image[base]
        if image[base + 1:base + 6] != b"CD001":
            raise ValueError(f"invalid volume descriptor at sector {sector}")
        if kind in (1, 2):
            descriptor_count += 1
            image[base + 813:base + 830] = VOLUME_TIME
            image[base + 830:base + 847] = VOLUME_TIME
            image[base + 847:base + 864] = UNSPECIFIED_TIME
            image[base + 864:base + 881] = UNSPECIFIED_TIME
            extent, size, _, _ = directory_record(image, base + 156)
            image[base + 156 + 18:base + 156 + 25] = RECORD_TIME
            root_directories.append((extent, size))
        if kind == 255:
            break
        sector += 1

    visited: set[tuple[int, int]] = set()
    record_count = 0

    def walk(extent: int, size: int) -> None:
        nonlocal record_count
        identity = (extent, size)
        if identity in visited:
            return
        visited.add(identity)
        base = extent * SECTOR
        offset = 0
        children: list[tuple[int, int]] = []
        while offset < size:
            absolute = base + offset
            length = image[absolute]
            if length == 0:
                offset = ((offset // SECTOR) + 1) * SECTOR
                continue
            child_extent, child_size, flags, name = directory_record(image, absolute)
            image[absolute + 18:absolute + 25] = RECORD_TIME
            record_count += 1
            if flags & 2 and name not in (".", ".."):
                children.append((child_extent, child_size))
            offset += length
        for child in children:
            walk(*child)

    for root in root_directories:
        walk(*root)
    changed = sum(a != b for a, b in zip(before, image))
    return descriptor_count, record_count, changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    image_path = ROOT / "game.iso"
    raw = image_path.read_bytes()
    payloads_before = {
        name: sha(read_iso_path(raw, name))
        for name in inventory["required_iso_members"]
    }
    normalized = bytearray(raw)
    descriptors, records, changed = normalize(normalized)
    payloads_after = {
        name: sha(read_iso_path(normalized, name))
        for name in inventory["required_iso_members"]
    }
    if payloads_before != payloads_after:
        raise ValueError("ISO timestamp normalization changed a required payload")
    if changed == 0:
        raise ValueError("ISO timestamp normalizer changed no metadata")
    temporary = image_path.with_suffix(".iso.normalized")
    temporary.write_bytes(normalized)
    temporary.replace(image_path)

    normalized_hash = sha(normalized)
    manifest_path = ROOT / "build/hardware_release_manifest.txt"
    lines = manifest_path.read_text(encoding="ascii").splitlines()
    found = False
    for index, line in enumerate(lines):
        if line.startswith("iso_sha256="):
            lines[index] = f"iso_sha256={normalized_hash}"
            found = True
    if not found:
        raise ValueError("hardware manifest has no iso_sha256 field")
    manifest_path.write_text("\r\n".join(lines) + "\r\n", encoding="ascii")

    report = {
        "schema": 1,
        "classification": "diagnostic-container-metadata-adapter",
        "raw_iso_sha256": sha(raw),
        "normalized_iso_sha256": normalized_hash,
        "changed_byte_count": changed,
        "volume_descriptor_count": descriptors,
        "directory_record_count": records,
        "required_payload_sha256": payloads_after,
        "production_payload_changed": False,
        "physical_saturn": "UNRUN",
    }
    output = ROOT / f"build/port_v2/old_build_baseline/run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"normalized ISO metadata: changed={changed}, sha256={normalized_hash}")


if __name__ == "__main__":
    main()
