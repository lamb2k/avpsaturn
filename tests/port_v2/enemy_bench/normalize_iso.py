#!/usr/bin/env python3
"""Normalize ISO-9660 metadata for deterministic EnemySalvageBench repeats."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path  # noqa: E402


def sha(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    normalizer_path = ROOT / "tests/port_v2/stage_bench/normalize_iso.py"
    spec = importlib.util.spec_from_file_location("stage_iso_normalizer", normalizer_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("stage ISO normalizer unavailable")
    normalizer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(normalizer)
    image_path = ROOT / "game.iso"
    raw = image_path.read_bytes()
    before = {name: sha(read_iso_path(raw, name)) for name in inventory["required_iso_members"]}
    normalized = bytearray(raw)
    descriptors, records, generators, changed = normalizer.normalize(normalized)
    after = {name: sha(read_iso_path(normalized, name)) for name in inventory["required_iso_members"]}
    if before != after or changed == 0:
        raise ValueError("normalization changed payloads or found no metadata")
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
        "raw_iso_sha256": sha(raw),
        "normalized_iso_sha256": normalized_hash,
        "changed_byte_count": changed,
        "volume_descriptor_count": descriptors,
        "directory_record_count": records,
        "generator_metadata_sector_count": generators,
        "required_payload_sha256": after,
        "production_payload_changed": False,
        "physical_saturn": "UNRUN",
    }
    output = ROOT / f"build/port_v2/enemy_bench/run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"normalized enemy ISO: {normalized_hash}")


if __name__ == "__main__":
    main()
