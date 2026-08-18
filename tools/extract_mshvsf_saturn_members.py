#!/usr/bin/env python3
"""Extract selected authorized Saturn ISO members to ignored private storage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze_mshvsf_saturn_disc import RawMode1Image


DEFAULT_MEMBERS = (
    "SYS.BIN",
    "MM.BIN",
    "00LOAD.BIN",
    "CPK.BIN",
    "CR.BIN",
    "MVSOPEN.BIN",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/mshvsf_saturn_disc_manifest.json"),
    )
    parser.add_argument(
        "--disc",
        type=Path,
        default=Path(
            "Marvel Super Heroes vs. Street Fighter/Saturn/"
            "Marvel Super Heroes vs. Street Fighter.bin"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".deps/mshvsf_saturn_members"),
    )
    parser.add_argument("members", nargs="*", default=DEFAULT_MEMBERS)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = {
        str(item["path"]).upper(): item
        for item in manifest["filesystem"]
        if not bool(item["is_directory"])
    }
    requested = [member.upper() for member in args.members]
    missing = sorted(set(requested) - set(entries))
    if missing:
        raise RuntimeError(f"Members not found in manifest: {missing}")

    image = RawMode1Image(args.disc.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, object]] = []
    for name in requested:
        entry = entries[name]
        data = image.read_extent(int(entry["extent"]), int(entry["bytes"]))
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry["sha256"]:
            raise RuntimeError(f"Hash mismatch while extracting {name}")
        output = args.output_dir / name
        output.write_bytes(data)
        extracted.append(
            {
                "path": name,
                "bytes": len(data),
                "extent": entry["extent"],
                "sha256": digest,
            }
        )

    private_manifest = {
        "source_disc_sha256": manifest["source"]["bin_sha256"],
        "members": extracted,
        "rights_boundary": "Private extracted payload; directory remains ignored and must not be committed.",
    }
    (args.output_dir / "private_manifest.json").write_text(
        json.dumps(private_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Extracted and verified {len(extracted)} private members.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
