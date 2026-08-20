#!/usr/bin/env python3
"""Build and verify the Saturn IP header for the staged AvP loader."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


IP_SIZE_OFFSET = 0xE0
LOAD_ADDRESS_OFFSET = 0xF0
READ_SIZE_OFFSET = 0xF4
EMBEDDED_LOAD_ADDRESS_OFFSET = 0x1014
EXPECTED_IP_SIZE = 0x1800
JO_ENGINE_LOAD_ADDRESS = 0x06004000
LOADER_LOAD_ADDRESS = JO_ENGINE_LOAD_ADDRESS
# Jo Engine's proven boot header leaves this field zero, causing the BIOS/IP
# path to use the first ISO member's actual length.
LOADER_READ_SIZE = 0x00000000


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source = args.source.read_bytes()
    if len(source) < 0xF8:
        raise SystemExit("IP.BIN is too short to contain Saturn boot fields")
    if be32(source, IP_SIZE_OFFSET) != EXPECTED_IP_SIZE:
        raise SystemExit(
            f"unexpected IP size 0x{be32(source, IP_SIZE_OFFSET):x}; "
            f"expected 0x{EXPECTED_IP_SIZE:x}"
        )
    if be32(source, LOAD_ADDRESS_OFFSET) != JO_ENGINE_LOAD_ADDRESS:
        raise SystemExit("unexpected source IP header load address")
    if be32(source, EMBEDDED_LOAD_ADDRESS_OFFSET) != JO_ENGINE_LOAD_ADDRESS:
        raise SystemExit("unexpected source IP embedded load address")
    occurrences = [
        index
        for index in range(len(source) - 3)
        if source[index : index + 4] == JO_ENGINE_LOAD_ADDRESS.to_bytes(4, "big")
    ]
    if occurrences != [LOAD_ADDRESS_OFFSET, EMBEDDED_LOAD_ADDRESS_OFFSET]:
        raise SystemExit(
            "source IP load-address occurrences changed: "
            + ",".join(f"0x{offset:x}" for offset in occurrences)
        )

    patched = bytearray(source)
    for offset in (LOAD_ADDRESS_OFFSET, EMBEDDED_LOAD_ADDRESS_OFFSET):
        patched[offset : offset + 4] = LOADER_LOAD_ADDRESS.to_bytes(4, "big")
    patched[READ_SIZE_OFFSET : READ_SIZE_OFFSET + 4] = (
        LOADER_READ_SIZE.to_bytes(4, "big")
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)

    emitted = args.output.read_bytes()
    if be32(emitted, LOAD_ADDRESS_OFFSET) != LOADER_LOAD_ADDRESS:
        raise SystemExit("loader IP load-address verification failed")
    if be32(emitted, EMBEDDED_LOAD_ADDRESS_OFFSET) != LOADER_LOAD_ADDRESS:
        raise SystemExit("loader IP embedded-address verification failed")
    if be32(emitted, READ_SIZE_OFFSET) != LOADER_READ_SIZE:
        raise SystemExit("loader IP read-size verification failed")
    print(
        "loader IP: "
        f"bytes={len(emitted)} load=0x{LOADER_LOAD_ADDRESS:08x} "
        f"read={LOADER_READ_SIZE} sha256={hashlib.sha256(emitted).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
