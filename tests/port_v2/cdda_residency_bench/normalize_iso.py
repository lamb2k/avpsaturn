#!/usr/bin/env python3
"""Normalize ISO-9660 timestamps without changing the residency fixture."""

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


def normalizer():
    path = ROOT / "tests/port_v2/stage_bench/normalize_iso.py"
    spec = importlib.util.spec_from_file_location("stage_normalizer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("stage ISO normalizer unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--metadata-dir",
                        default="tests/port_v2/cdda_residency_bench")
    parser.add_argument("--output-root",
                        default="build/port_v2/cdda_residency_bench")
    args = parser.parse_args()
    metadata = ROOT / args.metadata_dir
    inventory = json.loads((metadata / "inventory.json").read_text(
        encoding="utf-8"))
    image_path = ROOT / "game.iso"
    raw = image_path.read_bytes()
    before = {name: sha(read_iso_path(raw, name))
              for name in inventory["required_iso_members"]}
    normalized = bytearray(raw)
    descriptors, records, generators, changed = normalizer().normalize(normalized)
    after = {name: sha(read_iso_path(normalized, name))
             for name in inventory["required_iso_members"]}
    if before != after or changed == 0:
        raise ValueError("ISO normalization changed payloads or no metadata")
    temporary = image_path.with_suffix(".iso.normalized")
    temporary.write_bytes(normalized)
    temporary.replace(image_path)
    normalized_hash = sha(normalized)
    release = ROOT / "build/hardware_release_manifest.txt"
    lines = release.read_text(encoding="ascii").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("iso_sha256="):
            lines[index] = f"iso_sha256={normalized_hash}"
            break
    else:
        raise ValueError("hardware manifest has no ISO identity")
    release.write_text("\r\n".join(lines) + "\r\n", encoding="ascii")
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
    output = ROOT / args.output_root / f"run-{args.run}/iso-normalization.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"normalized CDDA/residency ISO: {normalized_hash}")


if __name__ == "__main__":
    main()
