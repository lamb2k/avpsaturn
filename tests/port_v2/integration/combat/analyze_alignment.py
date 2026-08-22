#!/usr/bin/env python3
"""Validate REPAIR-03 actor fields from retained deterministic MAME RAM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def u16(data: bytes | bytearray, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def actor(data: bytes | bytearray, definition: dict) -> dict:
    base = int(definition["offset"], 16)
    return {
        "facing": data[base + int(definition["facing_offset"], 16)],
        "x": u16(data, base + int(definition["x_offset"], 16)),
        "y": u16(data, base + int(definition["y_offset"], 16)),
        "z": u16(data, base + int(definition["z_offset"], 16)),
    }


def validate_frame(payload: bytes | bytearray, frame: dict,
                   contract: dict) -> None:
    if hashlib.sha256(payload).hexdigest() != frame["workram_sha256"]:
        raise AssertionError(f"frame {frame['frame']} work RAM identity drifted")
    for name in ("player", "enemy"):
        observed = actor(payload, contract["actors"][name])
        if observed != frame[name]:
            raise AssertionError(
                f"frame {frame['frame']} {name} fields drifted: {observed}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    contract = json.loads((HERE / "alignment_contract.json").read_text())
    capture_root = ROOT / contract["capture_root"]
    for index, frame in enumerate(contract["frames"]):
        path = capture_root / f"workram_{frame['frame']:05}.bin"
        payload = bytearray(path.read_bytes())
        validate_frame(payload, frame, contract)
        if args.negative_control and index == 0:
            player = contract["actors"]["player"]
            facing = int(player["offset"], 16) + int(
                player["facing_offset"], 16)
            payload[facing] ^= 1
            try:
                validate_frame(payload, frame, contract)
            except AssertionError:
                print("REPAIR-03 retained-MAME facing mutation: REJECTED")
            else:
                raise AssertionError("mutated source facing was accepted")
    if contract["fresh_mame_capture"] != "NOT_REQUIRED" or \
            contract["physical_saturn"] != "UNRUN":
        raise AssertionError("evidence boundary drifted")
    print("REPAIR-03 retained-MAME actor alignment fields: PASS")


if __name__ == "__main__":
    main()
