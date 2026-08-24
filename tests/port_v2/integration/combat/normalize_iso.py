#!/usr/bin/env python3
"""Normalize only diagnostic ISO metadata for the combat repeat."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


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
    raw_identity = sha(raw)
    normalized = bytearray(raw)
    descriptors, records, generators, changed = module.normalize(normalized)
    if changed == 0:
        prior_path = (ROOT / inventory["build_root"] /
                      f"run-{args.run}/iso-normalization.json")
        if not prior_path.is_file():
            raise ValueError("combat normalization found no container metadata")
        prior = json.loads(prior_path.read_text())
        if prior["normalized_iso_sha256"] != sha(raw):
            raise ValueError("combat ISO is neither raw nor the recorded normalization")
        descriptors = prior["volume_descriptor_count"]
        records = prior["directory_record_count"]
        generators = prior["generator_metadata_sector_count"]
        changed = prior["changed_byte_count"]
        raw_identity = prior["raw_iso_sha256"]
    else:
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
    output = ROOT / inventory["build_root"] / f"run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema": 1,
        "classification": "diagnostic-container-metadata-adapter",
        "raw_iso_sha256": raw_identity,
        "normalized_iso_sha256": normalized_hash,
        "changed_byte_count": changed,
        "volume_descriptor_count": descriptors,
        "directory_record_count": records,
        "generator_metadata_sector_count": generators,
        "production_payload_changed": False,
        "physical_saturn": "UNRUN"
    }, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"normalized combat ISO: {normalized_hash}")


if __name__ == "__main__":
    main()
