#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

IP_SIZE_OFFSET = 0xE0
LOAD_ADDRESS_OFFSET = 0xF0
READ_SIZE_OFFSET = 0xF4
EMBEDDED_LOAD_ADDRESS_OFFSET = 0x1014
EXPECTED_IP_SIZE = 0x1800
LOAD_ADDRESS = 0x06004000


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    if len(source) < 0x1018:
        raise SystemExit("IP.BIN is too short")
    if be32(source, IP_SIZE_OFFSET) != EXPECTED_IP_SIZE:
        raise SystemExit("unexpected IP size")
    if be32(source, LOAD_ADDRESS_OFFSET) != LOAD_ADDRESS:
        raise SystemExit("unexpected header load address")
    if be32(source, EMBEDDED_LOAD_ADDRESS_OFFSET) != LOAD_ADDRESS:
        raise SystemExit("unexpected embedded load address")
    patched = bytearray(source)
    patched[READ_SIZE_OFFSET:READ_SIZE_OFFSET + 4] = (0).to_bytes(4, "big")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    emitted = args.output.read_bytes()
    if be32(emitted, READ_SIZE_OFFSET) != 0:
        raise SystemExit("loader IP read-size verification failed")
    print("prototype loader IP: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
