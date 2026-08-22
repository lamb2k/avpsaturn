#!/usr/bin/env python3
"""Normalize only diagnostic ISO metadata for the collision repeat."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    path = ROOT / "tests/port_v2/player/normalize_iso.py"
    spec = importlib.util.spec_from_file_location("player_iso_normalizer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image_path = ROOT / "game.iso"
    raw = image_path.read_bytes()
    normalized = bytearray(raw)
    descriptors, records, generators, changed = module.normalize(normalized)
    if changed == 0:
        raise ValueError("collision ISO contained no normalizable metadata")
    image_path.write_bytes(normalized)
    normalized_hash = digest(normalized)
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
        "schema": 1,
        "classification": "diagnostic-container-metadata-adapter",
        "raw_iso_sha256": digest(raw),
        "normalized_iso_sha256": normalized_hash,
        "changed_byte_count": changed,
        "volume_descriptor_count": descriptors,
        "directory_record_count": records,
        "generator_metadata_sector_count": generators,
        "production_payload_changed": False,
        "physical_saturn": "UNRUN"
    }
    output = ROOT / f"build/port_v2/collision_bench/run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"normalized collision ISO: {normalized_hash}")


if __name__ == "__main__":
    main()
