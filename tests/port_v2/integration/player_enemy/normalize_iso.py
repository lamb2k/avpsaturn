#!/usr/bin/env python3
"""Normalize only diagnostic ISO metadata for the integration repeat."""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    path = ROOT / "tests/port_v2/player/normalize_iso.py"
    spec = importlib.util.spec_from_file_location("player_iso_normalizer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image_path = ROOT / "game.iso"
    raw = image_path.read_bytes()
    before = {name: sha(read_iso_path(raw, name))
              for name in inventory["required_iso_members"]}
    normalized = bytearray(raw)
    descriptors, records, generators, changed = module.normalize(normalized)
    after = {name: sha(read_iso_path(normalized, name))
             for name in inventory["required_iso_members"]}
    if before != after or changed == 0:
        raise ValueError("normalization altered payloads or found no metadata")
    image_path.write_bytes(normalized)
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
        "schema": 1,
        "classification": "diagnostic-container-metadata-adapter",
        "raw_iso_sha256": sha(raw),
        "normalized_iso_sha256": normalized_hash,
        "changed_byte_count": changed,
        "volume_descriptor_count": descriptors,
        "directory_record_count": records,
        "generator_metadata_sector_count": generators,
        "required_payload_sha256": after,
        "production_payload_changed": False,
        "physical_saturn": "UNRUN"
    }
    output = ROOT / inventory["build_root"] / f"run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"normalized integration ISO: {normalized_hash}")


if __name__ == "__main__":
    main()
