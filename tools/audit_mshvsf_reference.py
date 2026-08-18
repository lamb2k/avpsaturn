#!/usr/bin/env python3
"""Audit the local MSHvSF CPS-2/Saturn reference set without extracting ROMs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile


EXPECTED_MAME_MEMBERS = {
    "mshvsf.key": (20, "448eb440494c971800370f103b4d1f21a7266c6c"),
    "dl-1425.bin": (24576, "555f50fe5cdf127619da7d854c03f4a244a0c501"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_files(reference_root: Path) -> list[dict[str, object]]:
    files = []
    for path in sorted(reference_root.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": path.relative_to(reference_root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return files


def audit_cue(cue_path: Path) -> dict[str, object]:
    tracks: list[dict[str, object]] = []
    missing_files: list[str] = []
    current_file: str | None = None
    track_pattern = re.compile(r"^\s*TRACK\s+(\d+)\s+(\S+)", re.IGNORECASE)
    file_pattern = re.compile(r'^\s*FILE\s+"([^"]+)"\s+(.+)$', re.IGNORECASE)
    for line in cue_path.read_text(encoding="ascii", errors="replace").splitlines():
        file_match = file_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            if not (cue_path.parent / current_file).exists():
                missing_files.append(current_file)
            continue
        track_match = track_pattern.match(line)
        if track_match:
            tracks.append(
                {
                    "number": int(track_match.group(1)),
                    "type": track_match.group(2),
                    "file": current_file,
                }
            )
    return {
        "cue": cue_path.relative_to(cue_path.parents[1]).as_posix(),
        "tracks": tracks,
        "missing_referenced_files": sorted(set(missing_files)),
        "cue_consistent": not missing_files,
    }


def audit_saturn_bin(bin_path: Path) -> dict[str, object]:
    raw_sector_size = 2352
    with bin_path.open("rb") as handle:
        handle.seek(16 * raw_sector_size + 16)
        pvd = handle.read(2048)
    return {
        "path": bin_path.relative_to(bin_path.parents[1]).as_posix(),
        "bytes": bin_path.stat().st_size,
        "raw2352_sectors": bin_path.stat().st_size // raw_sector_size,
        "raw2352_remainder": bin_path.stat().st_size % raw_sector_size,
        "iso_primary_volume_descriptor": {
            "signature": pvd[1:6].decode("ascii", "replace"),
            "system_id": pvd[8:40].rstrip(b" ").decode("ascii", "replace"),
            "volume_id": pvd[40:72].rstrip(b" ").decode("ascii", "replace"),
            "volume_space_size_le": int.from_bytes(pvd[80:84], "little")
            if len(pvd) >= 84
            else None,
        },
    }


def audit_mame_archive(zip_path: Path) -> dict[str, object]:
    with ZipFile(zip_path) as archive:
        members = [
            {"name": info.filename, "bytes": info.file_size}
            for info in sorted(archive.infolist(), key=lambda item: item.filename)
        ]
    names = {str(member["name"]) for member in members}
    loose_files = {}
    for name, (expected_bytes, expected_sha1) in EXPECTED_MAME_MEMBERS.items():
        path = zip_path.parent / name
        loose_files[name] = {
            "path": path.relative_to(zip_path.parents[2]).as_posix(),
            "present": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else None,
            "sha1": sha1(path) if path.is_file() else None,
            "expected_bytes": expected_bytes,
            "expected_sha1": expected_sha1,
            "matches_mame_manifest": path.is_file()
            and path.stat().st_size == expected_bytes
            and sha1(path) == expected_sha1,
        }
    return {
        "archive": zip_path.relative_to(zip_path.parents[2]).as_posix(),
        "members": members,
        "archive_members_present": sorted(set(EXPECTED_MAME_MEMBERS) - names) == [],
        "missing_archive_members": sorted(set(EXPECTED_MAME_MEMBERS) - names),
        "loose_reference_files": loose_files,
        "loose_reference_files_match_mame_manifest": all(
            bool(item["matches_mame_manifest"]) for item in loose_files.values()
        ),
    }


def run_mame(mame_path: Path, rom_path: Path) -> dict[str, object]:
    command = [
        str(mame_path),
        "-rompath",
        str(rom_path),
        "-verifyroms",
        "mshvsf",
        "-video",
        "none",
        "-sound",
        "none",
        "-nothrottle",
        "-skip_gameinfo",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = (result.stdout + result.stderr).strip()
    return {
        "command": command,
        "returncode": result.returncode,
        "output": output.splitlines(),
        "status": "pass" if result.returncode == 0 and "is good" in output else "blocked",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("Marvel Super Heroes vs. Street Fighter"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mshvsf_reference_audit.json"),
    )
    parser.add_argument("--mame", type=Path)
    args = parser.parse_args()

    root = args.reference_root.resolve()
    cue = root / "Saturn" / "Marvel Super Heroes vs. Street Fighter.cue"
    saturn_bin = root / "Saturn" / "Marvel Super Heroes vs. Street Fighter.bin"
    archive = root / "Mame" / "mshvsf.zip"
    report: dict[str, object] = {
        "title": "Marvel Super Heroes vs. Street Fighter",
        "purpose": "Concurrent Capcom Saturn reference lane for the AvP conversion",
        "reference_root": str(args.reference_root),
        "files": audit_files(root),
        "saturn": {
            "cue": audit_cue(cue),
            "bin": audit_saturn_bin(saturn_bin),
        },
        "cps2_mame_archive": audit_mame_archive(archive),
        "rights_boundary": "Private research only; no ROM data or generated disc content is committed.",
    }
    if args.mame:
        report["mame_verifyroms"] = run_mame(args.mame.resolve(), archive.parent.resolve())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
