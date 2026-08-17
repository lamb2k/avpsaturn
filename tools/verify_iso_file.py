#!/usr/bin/env python3
"""Verify one file in a level-1/2 ISO-9660 image against its source."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


SECTOR_SIZE = 2048


def directory_record(data: bytes, offset: int) -> tuple[int, int, int, str]:
    length = data[offset]
    if length == 0:
        return 0, 0, 0, ""
    record = data[offset : offset + length]
    extent = int.from_bytes(record[2:6], "little")
    size = int.from_bytes(record[10:14], "little")
    flags = record[25]
    name_length = record[32]
    raw_name = record[33 : 33 + name_length]
    if raw_name == b"\x00":
        name = "."
    elif raw_name == b"\x01":
        name = ".."
    else:
        name = raw_name.decode("ascii").split(";", 1)[0]
    return extent, size, flags, name


def entries(image: bytes, extent: int, size: int) -> dict[str, tuple[int, int, int]]:
    directory = image[extent * SECTOR_SIZE : extent * SECTOR_SIZE + size]
    result: dict[str, tuple[int, int, int]] = {}
    offset = 0
    while offset < len(directory):
        length = directory[offset]
        if length == 0:
            offset = ((offset // SECTOR_SIZE) + 1) * SECTOR_SIZE
            continue
        child_extent, child_size, flags, name = directory_record(directory, offset)
        result[name.upper()] = (child_extent, child_size, flags)
        offset += length
    return result


def read_iso_path(image: bytes, iso_path: str) -> bytes:
    pvd = image[16 * SECTOR_SIZE : 17 * SECTOR_SIZE]
    if pvd[0] != 1 or pvd[1:6] != b"CD001":
        raise ValueError("image has no ISO-9660 primary volume descriptor")
    extent, size, flags, _ = directory_record(pvd, 156)
    components = [part for part in iso_path.replace("\\", "/").split("/") if part]
    for index, component in enumerate(components):
        match = entries(image, extent, size).get(component.upper())
        if match is None:
            raise ValueError(f"ISO path component not found: {component}")
        extent, size, flags = match
        if index + 1 < len(components) and not (flags & 2):
            raise ValueError(f"ISO path component is not a directory: {component}")
    if flags & 2:
        raise ValueError(f"ISO path resolves to a directory: {iso_path}")
    return image[extent * SECTOR_SIZE : extent * SECTOR_SIZE + size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("iso_path")
    parser.add_argument("--equals", type=Path, required=True)
    args = parser.parse_args()

    payload = read_iso_path(args.image.read_bytes(), args.iso_path)
    expected = args.equals.read_bytes()
    if payload != expected:
        raise ValueError(
            f"{args.iso_path} differs from {args.equals} "
            f"({len(payload)} versus {len(expected)} bytes)"
        )
    digest = hashlib.sha256(payload).hexdigest()
    print(f"Verified ISO {args.iso_path}: {len(payload)} bytes, sha256={digest}")


if __name__ == "__main__":
    main()
