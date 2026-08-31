#!/usr/bin/env python3
"""Build and record the deterministic Target-endian Round 1 content archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/port_v2/gameplay/round1/spec02_round1_content_image.c"
IDENTITY = ROOT / "src/port_v2/gameplay/round1/spec02_round1_content_identity.h"
ARCHIVE = ROOT / "build/avsp_cd/R1/R1SPEC.BIN"
MANIFEST = ROOT / "data/reimplement13_round1_memory_plan.json"
CONTENT_CAPACITY = 0x40000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_archive(compiler: Path, objcopy: Path, output: Path) -> None:
    temp_root = ROOT / "build/round1_content"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="compile-", dir=temp_root) as name:
        obj = Path(name) / "content.o"
        environment = os.environ.copy()
        environment["PATH"] = str(compiler.resolve().parent) + os.pathsep + \
            environment.get("PATH", "")
        subprocess.run([
            str(compiler), "-m2", "-Os", "-I.",
            "-Isrc/port_v2/gameplay/round1", "-c",
            SOURCE.relative_to(ROOT).as_posix(),
            "-o", obj.relative_to(ROOT).as_posix(),
        ], cwd=ROOT, check=True, env=environment)
        subprocess.run([
            str(objcopy), "-O", "binary", "-j", ".round1content",
            obj.relative_to(ROOT).as_posix(),
            output.relative_to(ROOT).as_posix(),
        ], cwd=ROOT, check=True, env=environment)


def game_map_values() -> dict[str, int | None]:
    raw = ROOT / "game.raw"
    map_path = ROOT / "game.map"
    result: dict[str, int | None] = {
        "game_bin_bytes": raw.stat().st_size if raw.exists() else None,
        "bss_end": None,
        "linked_rodata_bytes": None,
    }
    if not map_path.exists():
        return result
    text = map_path.read_text(encoding="ascii", errors="replace")
    bend = re.search(r"0x([0-9a-fA-F]{8})\s+__bend\s*=", text)
    rodata = re.search(r"^\.rodata\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)",
                       text, re.MULTILINE)
    if bend:
        result["bss_end"] = int(bend.group(1), 16)
    if rodata:
        result["linked_rodata_bytes"] = int(rodata.group(1), 16)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--objcopy", type=Path, required=True)
    args = parser.parse_args()
    if not args.compiler.exists() or not args.objcopy.exists():
        raise SystemExit("missing pinned SH-2 compiler or objcopy")

    control_root = ROOT / "build/round1_content"
    control_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="control-", dir=control_root) as name:
        first = Path(name) / "first.bin"
        second = Path(name) / "second.bin"
        compile_archive(args.compiler, args.objcopy, first)
        compile_archive(args.compiler, args.objcopy, second)
        if first.read_bytes() != second.read_bytes():
            raise SystemExit("Round 1 content archive is nondeterministic")
        payload = first.read_bytes()
    if len(payload) > CONTENT_CAPACITY:
        raise SystemExit("Round 1 content archive exceeds census-sized carve")
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_bytes(payload)
    archive_sha = digest(ARCHIVE)

    identity = (
        "#ifndef AVSP_SPEC02_ROUND1_CONTENT_IDENTITY_H\n"
        "#define AVSP_SPEC02_ROUND1_CONTENT_IDENTITY_H\n\n"
        "#define AVSP_ROUND1_CONTENT_ARCHIVE_FILE \"R1SPEC.BIN\"\n"
        "#define AVSP_ROUND1_CONTENT_ARCHIVE_DIRECTORY \"R1\"\n"
        f"#define AVSP_ROUND1_CONTENT_ARCHIVE_EXPECTED_BYTES {len(payload)}UL\n"
        "#define AVSP_ROUND1_CONTENT_ARCHIVE_SHA256 \\\n"
        f"    \"{archive_sha}\"\n\n"
        "#endif\n"
    )
    IDENTITY.write_text(identity, encoding="ascii", newline="\n")

    coverage = json.loads((ROOT / "data/round1_system_coverage.yaml").read_text(
        encoding="ascii"))
    writers = json.loads((ROOT / "data/oracle11_round1_writer_reconciliation.json").read_text(
        encoding="ascii"))
    route_segments = coverage["counts"]["segments"]
    writer_count = writers["coverage"]["baseline_writer_pcs"]
    census_floor = len(payload) + route_segments * 1024 + writer_count * 64
    if route_segments != 94 or writer_count != 1517 or census_floor > CONTENT_CAPACITY:
        raise SystemExit("accepted Round 1 census sizing inputs drift")

    memory = game_map_values()
    bss_end = memory["bss_end"]
    manifest = {
        "schema": "reimplement13-round1-memory-plan-v1",
        "classification": "REIMPLEMENT-13 bounded memory-plan program",
        "source_inputs": {
            "route_segments": route_segments,
            "authoritative_writer_pcs": writer_count,
            "actor_lifetimes": coverage["counts"]["actor_instances"],
            "class_type_archetypes": coverage["counts"]["actor_archetypes"],
            "route_events": coverage["counts"]["route_events"],
            "coverage_sha256": digest(ROOT / "data/round1_system_coverage.yaml"),
            "writer_reconciliation_sha256": digest(
                ROOT / "data/oracle11_round1_writer_reconciliation.json"),
        },
        "placement_rule": {
            "mutable_per_frame": "work RAM or fixed cartridge runtime pool",
            "read_only_content": "cartridge content archive",
            "scu_dma": "no SCU DMA transfer with an A-bus endpoint; cart-sourced VDP1 uploads are CPU-mediated",
        },
        "work_ram": {
            "linked_image_base": "0x06004000",
            "jo_user_program_data_end_exclusive": "0x060c0000",
            "linked_capacity_bytes": 0xBC000,
            "loader_low_ram_file_staging_limit_bytes": 0x100000,
            "game_bin_bytes": memory["game_bin_bytes"],
            "bss_end": f"0x{bss_end:08x}" if bss_end is not None else None,
            "bss_headroom_bytes": 0x060C0000 - bss_end if bss_end is not None else None,
            "linked_rodata_bytes": memory["linked_rodata_bytes"],
        },
        "cartridge_dram0": {
            "base": "0x22400000", "size": 0x200000,
            "owner": "Jo general allocator", "load_phase": "boot and approved phase overlays",
        },
        "cartridge_dram1": {
            "base": "0x22600000", "size": 0x200000,
            "regions": [
                {"id": "round1-tile-archive", "base": "0x22600000", "size": 0x96000,
                 "owner": "complete four-route source tile union", "load_phase": "boot",
                 "required_bytes": 612720},
                {"id": "round1-stage-strips", "base": "0x22696000", "size": 0x48000,
                 "owner": "Round 1 VDP2 strip package", "load_phase": "boot",
                 "required_bytes": (ROOT / "build/rp4_fixture/STRIPS.BIN").stat().st_size},
                {"id": "round1-runtime", "base": "0x226de000", "size": 0x19000,
                 "owner": "complete fixed actor pools and mutable route state", "load_phase": "runtime",
                 "required_bytes": 0x18410},
                {"id": "live-diagnostic-window", "base": "0x226f7000", "size": 0x1A000,
                 "owner": "rolling 575-sample emulator evidence window", "load_phase": "runtime",
                 "required_bytes": 575 * 156},
                {"id": "round1-spec-content", "base": "0x22711000", "size": CONTENT_CAPACITY,
                 "owner": "all generated read-only SPEC fixture tables", "load_phase": "boot",
                 "required_bytes": len(payload), "sha256": archive_sha,
                 "census_capacity_floor_bytes": census_floor},
                {"id": "composite-scratch", "base": "0x22751000", "size": 0x3000,
                 "owner": "mutable CPU-mediated VDP1 composite staging", "load_phase": "per frame",
                 "required_bytes": 11648},
                {"id": "bank1-general-allocator", "base": "0x22754000", "size": 0xAC000,
                 "owner": "Jo allocator remainder", "load_phase": "boot and approved overlays"},
            ],
        },
        "content_archive": {
            "file": "build/avsp_cd/R1/R1SPEC.BIN",
            "bytes": len(payload),
            "sha256": archive_sha,
            "generated_source_sha256": digest(SOURCE),
            "table_count": 152,
            "categories": ["terrain", "timer-selector", "animation-record", "collision", "route-and-actor-contract"],
            "deterministic_double_build": True,
            "target_endian": "SH-2 big endian",
        },
        "legal_load_seams": [
            {"seam": "existing boot load", "classification": "SOURCE_BOUND_PLATFORM_ADAPTER", "active": True},
            {"seam": "Round 1 to Round 2 stage boundary", "classification": "ADAPTED_PRESENTATION_FOR_USER_10", "active": False},
            {"seam": "intra-round camera-locked transition", "classification": "CONDITIONAL", "active": False,
             "guard": "only if census math proves all-resident cannot fit; CDDA data-read-safe; never mid-combat"},
        ],
        "build_time_asserts": [
            "runtime measured bytes equal source-pool layout",
            "runtime fits runtime region",
            "diagnostic window fits diagnostic region",
            "content archive fits census-sized content region",
            "census capacity floor fits content region",
            "composite maximum fits scratch region",
            "all DRAM1 carves fit the 2 MiB bank",
            "GAME.BIN BSS ends before 0x060c0000",
        ],
        "physical_saturn": "UNRUN",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="ascii", newline="\n")
    print(f"Round 1 content archive: PASS ({len(payload)} bytes, {archive_sha})")


if __name__ == "__main__":
    main()
