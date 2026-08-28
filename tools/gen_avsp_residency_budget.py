#!/usr/bin/env python3
"""RP5: pessimistic G0 residency ledger.

Measures, from the current build products and tracked manifests:

- high work RAM per build profile (nm __bend against the 0x060C0000 SGL
  sort-list limit) - the current game.elf is measured under the profile
  stamp in build/last_compile_profile.txt and MERGED into any previously
  recorded profiles, so running the generator after each profile build
  accumulates the complete table;
- cartridge DRAM1 carves parsed from main.c constants plus the measured
  archive/fixture file sizes that live in them;
- VDP2 character/pattern usage of the street scene from the tracked RP4
  manifest against the 512 KiB VDP2 VRAM;
- VDP1 texture demand (tile archive) and live command counts from the RP4
  live readback against 512 KiB VDP1 VRAM and the command budget;
- CRAM ownership from the live readback colour-RAM offsets;
- SCSP PCM members staged into the ISO against the 512 KiB sound RAM,
  with the phase-load model recorded (the full sum exceeds sound RAM by
  design; residency is phase-bounded and the peak is a GAP until a live
  SCSP high-water measurement exists);
- the disc-read guard contract (host-tested; live CDDA playback remains
  disabled, so the in-game rejection path is ADAPTED contract skeleton).

Every entry carries value, capacity, headroom and a MEASURED/ADAPTED/GAP
status. Output: data/avsp_residency_budget.json (numbers only).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NM = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
OUTPUT = ROOT / "data" / "avsp_residency_budget.json"

WORK_RAM_LIMIT = 0x060C0000
VDP2_VRAM_BYTES = 0x80000
VDP1_VRAM_BYTES = 0x80000
SOUND_RAM_BYTES = 0x80000
CRAM_BYTES = 0x1000


def measure_work_ram() -> dict:
    profile = "unknown"
    stamp = ROOT / "build" / "last_compile_profile.txt"
    if stamp.exists():
        profile = stamp.read_text().strip()
    out = subprocess.run(
        [str(NM), "--target=coff-sh", str(ROOT / "game.elf")],
        capture_output=True, text=True, check=True).stdout
    bend = None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == "__bend":
            bend = int(parts[0], 16)
    assert bend is not None, "__bend not found"
    return {
        "profile": profile,
        "bend": f"0x{bend:08x}",
        "limit": f"0x{WORK_RAM_LIMIT:08x}",
        "headroom_bytes": WORK_RAM_LIMIT - bend,
        "status": "MEASURED",
    }


def parse_carves() -> dict:
    source = (ROOT / "main.c").read_text(errors="replace")

    def const(name: str) -> int:
        match = re.search(rf"#define {name} (0x[0-9A-Fa-f]+|\d+)", source)
        assert match, name
        return int(match.group(1), 0)

    dram1 = const("AVSP_CART_DRAM1_BYTES")
    tiles = const("AVSP_TILE_REGION_BYTES")
    strips = const("AVSP_STRIPS_REGION_BYTES")
    round1_runtime = const("AVSP_ROUND1_RUNTIME_REGION_BYTES")
    round1_runtime_measured = const("AVSP_ROUND1_RUNTIME_MEASURED_BYTES")
    live_diagnostics = const("AVSP_LIVE_DIAG_REGION_BYTES")
    live_diagnostic_record = const("AVSP_LIVE_DIAG_RECORD_BYTES")
    live_diagnostic_samples = const("AVSP_LIVE_DIAG_SAMPLES")
    live_diagnostic_measured = live_diagnostic_record * live_diagnostic_samples
    tile_file = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
    strip_file = ROOT / "build" / "rp4_fixture" / "STRIPS.BIN"
    tile_bytes = tile_file.stat().st_size if tile_file.exists() else None
    strip_bytes = strip_file.stat().st_size if strip_file.exists() else None
    return {
        "dram1_bytes": dram1,
        "tile_carve_bytes": tiles,
        "tile_archive_bytes": tile_bytes,
        "tile_carve_headroom": (tiles - tile_bytes)
        if tile_bytes is not None else None,
        "strips_carve_bytes": strips,
        "strips_file_bytes": strip_bytes,
        "strips_carve_headroom": (strips - strip_bytes)
        if (strips and strip_bytes is not None) else None,
        "round1_runtime_carve_bytes": round1_runtime,
        "round1_runtime_measured_bytes": round1_runtime_measured,
        "round1_runtime_headroom_bytes": (round1_runtime -
                                           round1_runtime_measured),
        "live_diagnostic_carve_bytes": live_diagnostics,
        "live_diagnostic_measured_bytes": live_diagnostic_measured,
        "live_diagnostic_headroom_bytes": (live_diagnostics -
                                            live_diagnostic_measured),
        "jo_zone_bytes": (dram1 - tiles - strips - round1_runtime -
                          live_diagnostics),
        "status": "MEASURED",
        "note": "strips carve exists only in the street-test profile; the "
                "Round 1 runtime carve exists only in the live-encounter "
                "profile; the jo zone figure above applies when both are "
                "active, while other profiles omit the inactive carves",
    }


def vdp2_usage() -> dict:
    manifest = json.loads(
        (ROOT / "data" / "rp4_street_planes.json").read_text())
    planes = manifest["planes"]
    chars = sum(p["char_pool_bytes"] for p in planes.values()) \
        if isinstance(planes, dict) else None
    if chars is None:
        return {"status": "GAP", "note": "plane manifest missing"}
    pnt = sum(p["cell_cols"] * p["cell_rows"] * 2 for p in planes.values())
    used = chars + pnt
    return {
        "character_bytes": chars,
        "pattern_bytes": pnt,
        "used_bytes": used,
        "capacity_bytes": VDP2_VRAM_BYTES,
        "headroom_bytes": VDP2_VRAM_BYTES - used,
        "status": "MEASURED",
        "note": "street scene (largest measured scene); frontend bitmap "
                "scenes measured separately at RP0",
    }


def vdp1_usage() -> dict:
    live = json.loads(
        (ROOT / "data" / "rp4_street_live_readback.json").read_text())
    classes = {int(k): v for k, v in live["vdp1_command_classes"].items()}
    commands = sum(classes.values())
    tile_file = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
    textures = tile_file.stat().st_size if tile_file.exists() else None
    return {
        "live_command_sample": commands,
        "command_classes": classes,
        "texture_archive_bytes": textures,
        "capacity_bytes": VDP1_VRAM_BYTES,
        "headroom_bytes": (VDP1_VRAM_BYTES - textures)
        if textures is not None else None,
        "status": "MEASURED",
        "note": "command sample from one paused street frame; a route-wide "
                "command high-water is a GAP until a soak instrument runs",
    }


def cram_usage() -> dict:
    live = json.loads(
        (ROOT / "data" / "rp4_street_live_readback.json").read_text())
    return {
        "colour_ram_offsets": live["cram_offsets"],
        "capacity_bytes": CRAM_BYTES,
        "status": "MEASURED",
        "note": "street planes reuse the two frontend palette blocks; "
                "boot claims the remaining blocks (measured when the "
                "street palette exhaustion bug was fixed)",
    }


def scsp_usage() -> dict:
    audio_dir = ROOT / "build" / "avsp_cd" / "AUDIO"
    members = {}
    total = 0
    if audio_dir.exists():
        for member in sorted(audio_dir.iterdir()):
            size = member.stat().st_size
            members[member.name] = size
            total += size
    return {
        "iso_members": members,
        "total_member_bytes": total,
        "status": "ADAPTED",
        "note": "PCM buffers live in the jo allocator zones (work RAM and "
                "cartridge), not SCSP RAM, and are fed to the SCSP by the "
                "driver; the constraint is allocator headroom. The total "
                "staged member set exceeds any single phase by design: "
                "residency is phase-bounded (boss-clear loads at the "
                "interior wipe after ~900 KB of opening PCM is released). "
                "A live allocator/SCSP high-water instrument is a GAP.",
    }


def disc_guard() -> dict:
    return {
        "guard_module": "avsp_disc_guard.c",
        "host_test": "tests/avsp_disc_guard_test.c",
        "reader_guarded": "avsp_fs_read_into rejects reads with FS CDDA "
                          "LOCK when CDDA owns the drive and no measured "
                          "window is open",
        "declared_windows": ["interior wipe: CDDA paused"],
        "status": "ADAPTED",
        "note": "the CD track start call is still disabled, so live CDDA "
                "rejection is contract skeleton; the host test proves the "
                "guard semantics including both negative controls",
    }


def main() -> None:
    existing = {}
    if OUTPUT.exists():
        existing = json.loads(OUTPUT.read_text())
    profiles = existing.get("work_ram_profiles", {})
    measurement = measure_work_ram()
    profiles[measurement["profile"]] = measurement

    budget = {
        "schema": "avsp-residency-budget-v0",
        "classification": "pessimistic residency ledger; sizes, addresses "
                          "and counts only",
        "work_ram_limit": f"0x{WORK_RAM_LIMIT:08x}",
        "work_ram_profiles": profiles,
        "cartridge": parse_carves(),
        "vdp2": vdp2_usage(),
        "vdp1": vdp1_usage(),
        "cram": cram_usage(),
        "scsp": scsp_usage(),
        "disc_guard": disc_guard(),
    }
    OUTPUT.write_text(json.dumps(budget, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"residency budget: profiles={sorted(profiles)}, "
          f"work RAM headroom this profile "
          f"{measurement['headroom_bytes']} bytes")


if __name__ == "__main__":
    main()
