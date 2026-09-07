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
    "0x3BCBCUL <= AVSP_ROUND1_CONTENT_REGION_BYTES",
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
assert HEADER.count("#define avsp_round1_") == archive["table_count"] == 186
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

print("REIMPLEMENT-13 existing memory-map structural checks: PASS "
      f"({mutations} source-token omission controls rejected; "
      f"archive {len(payload)} bytes / 0x40000 census carve)")


def proposed_boot_allocations():
    """Conditional payload-order model; not a native execution or peak proof.

    Model the SH2 Jo block's8-byte header and4-byte alignment. Exclude the
    work-RAM heap entirely to avoid claiming unmeasured available space.
    Complete later content and engine allocations remain outside this model.
    """
    capacities = [524288, 614400, 704512]
    zones = [[] for _ in capacities]
    peaks = [0, 0, 0]

    def alloc(size, reuse=True):
        needed = (size + 8 + 3) & ~3
        for i, zone in enumerate(zones):
            if reuse:
                for block in zone:
                    if block[1] and block[0] >= needed:
                        block[1] = False
                        return i, block
            used = sum(b[0] for b in zone)
            if used + needed <= capacities[i]:
                block = [needed, False]
                zone.append(block)
                peaks[i] = max(peaks[i], used + needed)
                return i, block
        raise ValueError("conditional boot payload does not fit")

    def free(handle):
        i, block = handle
        if zones[i][-1] is block:
            zones[i].pop()
        else:
            block[1] = True

    def file(size):
        free(alloc(2048))  # jo_fs_open probe closes before destination
        return alloc(size)

    stream = alloc(131885)
    alloc(131072)
    free(stream)
    for size in (18432, 18432, 419280):
        file(size)
    for _ in range(3):
        alloc(18432, False)
    file(51850)
    alloc(18432, False)
    for size in (7040, 3328, 1920, 7040, 1920, 144752):
        file(size)
    for size in (512, 960):
        free(file(size))
    file(512)
    # Real allocator-specific controls: reused blocks retain their full size;
    # an unrelated surviving allocation prevents rollback across a free hole.
    large = file(4096)
    guard = alloc(64, False)
    old_size = large[1][0]
    free(large)
    small = alloc(32)
    assert small[1] is large[1] and small[1][0] == old_size
    free(small)
    free(guard)
    return {"capacities": capacities, "conditional_high_water_bytes": peaks,
            "tail_headroom_bytes": [c-p for c,p in zip(capacities, peaks)],
            "unmeasured_engine_and_later_content": True}


print("Conditional boot allocation model (NOT native/physical proof): " +
      json.dumps(proposed_boot_allocations(), sort_keys=True))


def recorded_audio_inventory():
    """Report metadata demand, not native cue acceptance or payload presence."""
    records = []
    for path in sorted((ROOT / "data").glob("qsound_*_capture.json")):
        report = json.loads(path.read_text(encoding="ascii"))
        pcm = report["saturn_pcm"]
        assert pcm["bytes"] == report["wave"]["event_sample_frames"] * 4
        records.append({"path": path.relative_to(ROOT).as_posix(),
                        "payload_bytes": pcm["bytes"],
                        "payload_sha256": pcm["sha256"]})
    return records


def check_recorded_audio_inventory(records):
    expected = PLAN["full_route_read_only_sizing_2026_09_07"][
        "audio_capacity_status"]["historical_capture_inventory"]
    fingerprint = hashlib.sha256(json.dumps(
        records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if (fingerprint != expected["manifest_sha256"] or
            len(records) != expected["distinct_recorded_payloads"] or
            sum(r["payload_bytes"] for r in records) !=
            expected["recorded_bytes_total"]):
        raise ValueError("recorded audio inventory identity/size drift")


audio_records = recorded_audio_inventory()
check_recorded_audio_inventory(audio_records)
for mutation in ("size", "omission"):
    changed = [dict(record) for record in audio_records]
    if mutation == "size":
        changed[0]["payload_bytes"] -= 4
    else:
        changed.pop()
    try:
        check_recorded_audio_inventory(changed)
    except ValueError as error:
        assert str(error) == "recorded audio inventory identity/size drift"
    else:
        raise AssertionError("audio sizing control survived: " + mutation)
print("Recorded audio sizing: PASS (15 payload reports,2727832 bytes; "
      "2 attributable metadata controls; NOT native behavioral kills or cue approval)")
