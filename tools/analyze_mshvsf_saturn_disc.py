#!/usr/bin/env python3
"""Produce a metadata-only manifest for the authorized MSHvSF Saturn disc."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


RAW_SECTOR_BYTES = 2352
USER_DATA_OFFSET = 16
USER_DATA_BYTES = 2048


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ascii_field(data: bytes) -> str:
    return data.decode("ascii", "replace").rstrip(" \x00")


@dataclass(frozen=True)
class RawMode1Image:
    path: Path

    def read_sector(self, lba: int) -> bytes:
        with self.path.open("rb") as handle:
            handle.seek(lba * RAW_SECTOR_BYTES + USER_DATA_OFFSET)
            data = handle.read(USER_DATA_BYTES)
        if len(data) != USER_DATA_BYTES:
            raise RuntimeError(f"Short sector read at LBA {lba}")
        return data

    def read_extent(self, extent: int, size: int) -> bytes:
        output = bytearray()
        sector_count = (size + USER_DATA_BYTES - 1) // USER_DATA_BYTES
        with self.path.open("rb") as handle:
            for index in range(sector_count):
                handle.seek((extent + index) * RAW_SECTOR_BYTES + USER_DATA_OFFSET)
                output.extend(handle.read(USER_DATA_BYTES))
        return bytes(output[:size])


def parse_msf(value: str) -> int:
    minute, second, frame = (int(part) for part in value.split(":"))
    return minute * 60 * 75 + second * 75 + frame


def parse_cue(path: Path) -> list[dict[str, object]]:
    tracks: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        track_match = re.match(r"\s*TRACK\s+(\d+)\s+(\S+)", line, re.IGNORECASE)
        if track_match:
            current = {
                "number": int(track_match.group(1)),
                "type": track_match.group(2),
                "indexes": {},
            }
            tracks.append(current)
            continue
        if current is None:
            continue
        index_match = re.match(r"\s*INDEX\s+(\d+)\s+(\d+:\d+:\d+)", line, re.IGNORECASE)
        if index_match:
            current["indexes"][index_match.group(1)] = {
                "msf": index_match.group(2),
                "absolute_sector": parse_msf(index_match.group(2)),
            }
        pregap_match = re.match(r"\s*PREGAP\s+(\d+:\d+:\d+)", line, re.IGNORECASE)
        if pregap_match:
            current["pregap"] = {
                "msf": pregap_match.group(1),
                "sectors": parse_msf(pregap_match.group(1)),
            }

    for index, track in enumerate(tracks):
        start = track["indexes"].get("01", {}).get("absolute_sector")
        next_start = None
        if index + 1 < len(tracks):
            next_track = tracks[index + 1]
            next_start = next_track["indexes"].get("00", next_track["indexes"].get("01", {})).get(
                "absolute_sector"
            )
        if start is not None and next_start is not None:
            track["program_sectors_until_next_track"] = next_start - start
    return tracks


def parse_directory_record(record: bytes) -> dict[str, object]:
    name_length = record[32]
    raw_name = record[33 : 33 + name_length]
    if raw_name == b"\x00":
        name = "."
    elif raw_name == b"\x01":
        name = ".."
    else:
        name = raw_name.decode("ascii", "replace").split(";", 1)[0]
    return {
        "name": name,
        "extent": int.from_bytes(record[2:6], "little"),
        "bytes": int.from_bytes(record[10:14], "little"),
        "flags": record[25],
        "is_directory": bool(record[25] & 0x02),
    }


def walk_iso(image: RawMode1Image, root_record: dict[str, object]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    visited: set[tuple[int, int]] = set()

    def visit(prefix: str, extent: int, size: int) -> None:
        key = (extent, size)
        if key in visited:
            return
        visited.add(key)
        directory = image.read_extent(extent, size)
        position = 0
        while position < len(directory):
            record_length = directory[position]
            if record_length == 0:
                position = ((position // USER_DATA_BYTES) + 1) * USER_DATA_BYTES
                continue
            record = directory[position : position + record_length]
            parsed = parse_directory_record(record)
            position += record_length
            if parsed["name"] in {".", ".."}:
                continue
            path = f"{prefix}/{parsed['name']}" if prefix else str(parsed["name"])
            if parsed["is_directory"]:
                entries.append({"path": path, **parsed})
                visit(path, int(parsed["extent"]), int(parsed["bytes"]))
            else:
                data = image.read_extent(int(parsed["extent"]), int(parsed["bytes"]))
                entries.append(
                    {
                        "path": path,
                        **parsed,
                        "sha256": sha256_bytes(data),
                    }
                )

    visit("", int(root_record["extent"]), int(root_record["bytes"]))
    return sorted(entries, key=lambda item: str(item["path"]).lower())


def marker_hits(image: RawMode1Image, entries: list[dict[str, object]]) -> list[dict[str, object]]:
    markers = [b"4MB", b"4M RAM", b"RAM CART", b"DRAM", b"VDP1", b"VDP2", b"SGL"]
    hits: list[dict[str, object]] = []
    for entry in entries:
        if entry["is_directory"] or int(entry["bytes"]) > 8 * 1024 * 1024:
            continue
        data = image.read_extent(int(entry["extent"]), int(entry["bytes"]))
        upper = data.upper()
        for marker in markers:
            offset = upper.find(marker)
            if offset >= 0:
                hits.append(
                    {
                        "path": entry["path"],
                        "marker": marker.decode("ascii"),
                        "file_offset": offset,
                        "confidence": "LOW",
                        "warning": "ASCII marker only; confirm in disassembly before assigning runtime meaning.",
                    }
                )
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--saturn-root",
        type=Path,
        default=Path("Marvel Super Heroes vs. Street Fighter/Saturn"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mshvsf_saturn_disc_manifest.json"),
    )
    args = parser.parse_args()

    root = args.saturn_root.resolve()
    bin_path = root / "Marvel Super Heroes vs. Street Fighter.bin"
    cue_path = root / "Marvel Super Heroes vs. Street Fighter.cue"
    image = RawMode1Image(bin_path)
    pvd = image.read_sector(16)
    if pvd[1:6] != b"CD001":
        raise RuntimeError("Primary volume descriptor signature is not CD001")
    root_length = pvd[156]
    root_record = parse_directory_record(pvd[156 : 156 + root_length])
    entries = walk_iso(image, root_record)
    files = [entry for entry in entries if not entry["is_directory"]]
    directories = [entry for entry in entries if entry["is_directory"]]
    boot = image.read_sector(0)
    tracks = parse_cue(cue_path)

    report = {
        "title": "Marvel Super Heroes vs. Street Fighter official Saturn disc manifest",
        "source": {
            "bin_path": bin_path.relative_to(root.parents[1]).as_posix(),
            "bin_bytes": bin_path.stat().st_size,
            "bin_sha256": sha256_file(bin_path),
            "raw2352_sectors": bin_path.stat().st_size // RAW_SECTOR_BYTES,
            "cue_path": cue_path.relative_to(root.parents[1]).as_posix(),
            "cue_sha256": sha256_file(cue_path),
        },
        "boot_header": {
            "hardware_id": ascii_field(boot[0:16]),
            "maker_id": ascii_field(boot[16:32]),
            "product_number": ascii_field(boot[32:42]),
            "version": ascii_field(boot[42:48]),
            "release_date": ascii_field(boot[48:56]),
            "device_info": ascii_field(boot[56:64]),
            "compatible_area_symbols": ascii_field(boot[64:74]),
            "compatible_peripherals": ascii_field(boot[74:90]),
            "title": ascii_field(boot[96:208]),
            "sector0_sha256": sha256_bytes(boot),
        },
        "iso9660": {
            "system_id": ascii_field(pvd[8:40]),
            "volume_id": ascii_field(pvd[40:72]),
            "volume_space_size": int.from_bytes(pvd[80:84], "little"),
            "root_extent": root_record["extent"],
            "root_bytes": root_record["bytes"],
            "directory_count": len(directories),
            "file_count": len(files),
            "total_file_bytes": sum(int(entry["bytes"]) for entry in files),
        },
        "tracks": tracks,
        "filesystem": entries,
        "largest_files": sorted(
            (
                {"path": entry["path"], "bytes": entry["bytes"], "sha256": entry["sha256"]}
                for entry in files
            ),
            key=lambda item: int(item["bytes"]),
            reverse=True,
        )[:24],
        "ascii_marker_leads": marker_hits(image, entries),
        "verified_runtime_observation": {
            "emulator": "Yaba Sanshiro 2 v1.20.37",
            "cartridge": "32 Mbit (4 MB) DRAM, emulator type 7",
            "result": "Booted licensed legal screen, Marvel/Capcom intro, title, and attract gameplay from a temporary cue pointing at the unchanged BIN.",
            "status": "PASS",
            "remaining_gate": "Deterministic emulated-pad input capture for the Ryu gameplay slice is not yet established.",
        },
        "rights_boundary": "Metadata and hashes only; no disc file payload is written or committed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Mapped {len(files)} files in {len(directories)} directories and "
        f"{len(tracks)} cue tracks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
