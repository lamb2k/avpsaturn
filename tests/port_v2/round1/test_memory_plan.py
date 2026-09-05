#!/usr/bin/env python3
"""Focused controls for the census-sized Round 1 memory program."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MAIN = (ROOT / "main.c").read_text(encoding="ascii")
BUILD = (ROOT / "build.ps1").read_text(encoding="utf-8-sig")
ROUND1 = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text(
    encoding="ascii")
HEADER = (ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h").read_text(
    encoding="ascii")
ARCHIVE = ROOT / "build/avsp_cd/R1/R1SPEC.BIN"
PLAN = json.loads((ROOT / "data/reimplement13_round1_memory_plan.json").read_text(
    encoding="ascii"))


REQUIRED_MAIN = (
    "#define AVSP_ROUND1_CONTENT_REGION_BYTES 0x40000",
    "#define AVSP_COMPOSITE_SCRATCH_REGION_BYTES 0x3000",
    "#define AVSP_ROUND1_CONTENT_BASE \\",
    "#define AVSP_ROUND1_CART_ALLOCATOR_BASE \\",
    "AVSP_ROUND1_CONTENT_ARCHIVE_EXPECTED_BYTES <=",
    "0x3A924UL <= AVSP_ROUND1_CONTENT_REGION_BYTES",
    "AVSP_COMPOSITE_MAX_TEXTURE_BYTES <=",
    "static int load_round1_content_archive(void)",
    "const int read_bytes = avsp_fs_read_into(\n"
    "        AVSP_ROUND1_CONTENT_ARCHIVE_FILE",
    "runtime_ready = load_round1_content_archive();",
    "avsp_diag_round1_spec_bound =\n"
    "        avsp_diag_round1_content_loaded &&",
    "AVSP_ROUND1_CONTENT_REGION_BYTES -",
)
REQUIRED_BUILD = (
    "tools\\build_round1_content_archive.py",
    "'/R1/R1SPEC.BIN' '--equals'",
)
REQUIRED_ROUND1 = (
    "const AvspRound1ContentArchive *avsp_round1_content;",
    "bytes != AVSP_ROUND1_CONTENT_ARCHIVE_BYTES",
    "content->magic != AVSP_ROUND1_CONTENT_ARCHIVE_MAGIC",
    "content->version != AVSP_ROUND1_CONTENT_ARCHIVE_VERSION",
)


def accepts(main: str, build: str, round1: str) -> bool:
    return (all(token in main for token in REQUIRED_MAIN) and
            all(token in build for token in REQUIRED_BUILD) and
            all(token in round1 for token in REQUIRED_ROUND1))


assert accepts(MAIN, BUILD, ROUND1)
mutations = 0
for token in REQUIRED_MAIN:
    assert not accepts(MAIN.replace(token, "/* removed memory rule */", 1),
                       BUILD, ROUND1), token
    mutations += 1
for token in REQUIRED_BUILD:
    assert not accepts(MAIN, BUILD.replace(token, "removed"), ROUND1), token
    mutations += 1
for token in REQUIRED_ROUND1:
    assert not accepts(MAIN, BUILD,
                       ROUND1.replace(token, "/* removed bind rule */")), token
    mutations += 1

payload = ARCHIVE.read_bytes()
archive = PLAN["content_archive"]
assert len(payload) == archive["bytes"]
assert hashlib.sha256(payload).hexdigest() == archive["sha256"]
assert struct.unpack(">III", payload[:12]) == (0x52314341, 1, len(payload))
assert HEADER.count("#define avsp_round1_") == archive["table_count"] == 178
assert archive["deterministic_double_build"] is True

regions = PLAN["cartridge_dram1"]["regions"]
cursor = int(PLAN["cartridge_dram1"]["base"], 16)
for region in regions:
    assert int(region["base"], 16) == cursor, region["id"]
    assert region.get("required_bytes", 0) <= region["size"]
    cursor += region["size"]
assert cursor == 0x22800000
assert PLAN["source_inputs"]["route_segments"] == 94
assert PLAN["source_inputs"]["authoritative_writer_pcs"] == 1517
assert PLAN["physical_saturn"] == "UNRUN"
assert PLAN["legal_load_seams"][0]["active"] is True
assert all(not seam["active"] for seam in PLAN["legal_load_seams"][1:])
assert "no SCU DMA transfer with an A-bus endpoint" in \
    PLAN["placement_rule"]["scu_dma"]

print("REIMPLEMENT-13 complete-Round-1 memory plan: PASS "
      f"({mutations} real ownership/capacity/load mutations rejected; "
      f"archive {len(payload)} bytes / 0x40000 census carve)")
