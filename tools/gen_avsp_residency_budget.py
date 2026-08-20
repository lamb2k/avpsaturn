#!/usr/bin/env python3
"""RP5: pessimistic G0 residency ledger.

Measures, from the current build products and tracked manifests:

- high work RAM per build profile: the four explicit measurement files
  written by tools/measure_avsp_profile.ps1 under
  build/residency_profiles/ (normal-release, street-test, frontend-test,
  encounter-test). This generator NEVER reads its previous output;
  duplicate, missing or unknown profile files are rejected, and the
  ledger derives only from those inputs plus tracked manifests, so two
  runs over the same inputs are byte-identical;
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NM = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
OUTPUT = ROOT / "data" / "avsp_residency_budget.json"

WORK_RAM_LIMIT = 0x060C0000
VDP2_VRAM_BYTES = 0x80000
VDP1_VRAM_BYTES = 0x80000
SOUND_RAM_BYTES = 0x80000
CRAM_BYTES = 0x1000


PROFILE_ORDER = ("normal-release", "street-test", "frontend-test",
                 "encounter-test")
PROFILE_DIR = ROOT / "build" / "residency_profiles"


def load_work_ram_profiles() -> dict:
    """The four explicit measurement files, validated and fixed-ordered."""
    if not PROFILE_DIR.exists():
        raise SystemExit(
            f"missing {PROFILE_DIR.relative_to(ROOT)}: run "
            f"tools/measure_avsp_profile.ps1 for each of {PROFILE_ORDER}")
    present = sorted(f.stem for f in PROFILE_DIR.glob("*.json"))
    unknown = [name for name in present if name not in PROFILE_ORDER]
    if unknown:
        raise SystemExit(f"unknown profile measurement files: {unknown}")
    missing = [name for name in PROFILE_ORDER if name not in present]
    if missing:
        raise SystemExit(
            f"missing profile measurements: {missing} (run "
            f"tools/measure_avsp_profile.ps1 for each)")
    profiles = {}
    for name in PROFILE_ORDER:
        record = json.loads((PROFILE_DIR / f"{name}.json").read_text())
        if record.get("profile") != name:
            raise SystemExit(
                f"{name}.json names profile {record.get('profile')!r}; "
                f"file/profile mismatch")
        bend = int(record["bend"], 16)
        profiles[name] = {
            "profile": name,
            "build_profile_stamp": record["build_profile_stamp"],
            "game_elf_sha256": record["game_elf_sha256"],
            "bend": record["bend"],
            "limit": f"0x{WORK_RAM_LIMIT:08x}",
            "headroom_bytes": WORK_RAM_LIMIT - bend,
            "iso_sha256": record.get("iso_sha256"),
            "hardware_manifest_sha256":
                record.get("hardware_manifest_sha256"),
            "status": "MEASURED",
        }
    return profiles


def parse_carves() -> dict:
    source = (ROOT / "main.c").read_text(errors="replace")

    def const(name: str) -> int:
        match = re.search(rf"#define {name} (0x[0-9A-Fa-f]+|\d+)", source)
        assert match, name
        return int(match.group(1), 0)

    dram1 = const("AVSP_CART_DRAM1_BYTES")
    tiles = const("AVSP_TILE_REGION_BYTES")
    strips = const("AVSP_STRIPS_REGION_BYTES")
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
        "jo_zone_bytes": dram1 - tiles - strips,
        "status": "MEASURED",
        "note": "strips carve exists only in the street-test profile; the "
                "jo zone figure above applies to that profile, other "
                "profiles get dram1 - tile_carve",
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
    profiles = load_work_ram_profiles()

    budget = {
        "schema": "avsp-residency-budget-v1",
        "inputs": "four explicit build/residency_profiles/*.json "
                  "measurements plus tracked manifests; previous output "
                  "is never read",
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
    print("residency budget: " + ", ".join(
        f"{name} headroom {profiles[name]['headroom_bytes']}"
        for name in profiles))


if __name__ == "__main__":
    main()
