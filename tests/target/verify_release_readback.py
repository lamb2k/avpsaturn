#!/usr/bin/env python3
"""Validate one exact normal-release emulator readback across four domains.

The profile-specific collector supplied to ``verify.ps1 -EmulatorCheck`` owns
the live emulator interaction and writes the ignored report at
``build/target/release_readback.json``. This checked-in verifier prevents an
arbitrary passing collector from satisfying Saturn acceptance: it binds the
report to the current release artifacts, accepted oracle, emulator identity,
and explicit semantic/resource/render/final-scanout measurements.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "build/target/release_readback.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    require(path.is_file(), f"missing release artifact: {path.relative_to(ROOT)}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state_scalar(name: str) -> str:
    text = (ROOT / "project_state.yaml").read_text(encoding="utf-8")
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+?)\s*$", text)
    require(match is not None, f"project_state missing {name}")
    return match.group(1).strip()


def manifest() -> dict[str, str]:
    values: dict[str, str] = {}
    path = ROOT / "build/hardware_release_manifest.txt"
    require(path.is_file(), "hardware release manifest is missing")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        require(key not in values, f"duplicate manifest key: {key}")
        values[key] = value
    return values


def exact_keys(value: dict, expected: set[str], where: str) -> None:
    require(isinstance(value, dict), f"{where} must be an object")
    require(set(value) == expected,
            f"{where} keys differ: expected {sorted(expected)}, got {sorted(value)}")


def nonnegative(value: object, where: str) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value >= 0,
            f"{where} must be a nonnegative integer")
    return value


def percentage(value: object, where: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{where} must be numeric")
    result = float(value)
    require(15.0 <= result <= 100.0, f"{where} must retain at least 15%")
    return result


def main() -> None:
    require(REPORT.is_file(),
            "release readback collector did not produce build/target/release_readback.json")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    exact_keys(report, {"schema", "classification", "profile", "artifacts",
                        "emulator", "domains", "result"}, "report")
    require(report["schema"] == 1, "release readback schema drifted")
    require(report["classification"] == "emulator-release-readback",
            "readback classification drifted")
    require(report["profile"] == "release-normal-release",
            "readback is not from release-normal-release")
    require(report["result"] == "PASS", "collector did not report PASS")

    compile_profile = (ROOT / "build/last_compile_profile.txt").read_text(
        encoding="utf-8").strip()
    require(compile_profile == "release-normal-release",
            f"compile profile is {compile_profile!r}")
    release_manifest = manifest()
    require(release_manifest.get("profile") == "normal-release",
            "hardware manifest is not normal-release")

    artifacts = report["artifacts"]
    artifact_paths = {
        "game_iso_sha256": ROOT / "game.iso",
        "game_cue_sha256": ROOT / "game.cue",
        "hardware_manifest_sha256": ROOT / "build/hardware_release_manifest.txt",
        "game_elf_sha256": ROOT / "game.elf",
    }
    exact_keys(artifacts, set(artifact_paths), "artifacts")
    for name, path in artifact_paths.items():
        require(artifacts[name] == sha256(path),
                f"readback artifact binding failed: {name}")
    require(release_manifest.get("iso_sha256") == artifacts["game_iso_sha256"],
            "manifest ISO identity disagrees with readback")
    require(release_manifest.get("cue_sha256") == artifacts["game_cue_sha256"],
            "manifest cue identity disagrees with readback")

    emulator = report["emulator"]
    exact_keys(emulator, {"identity", "executable_sha256", "settings_sha256",
                          "evidence_tier", "run_started_utc",
                          "report_created_utc"}, "emulator")
    require(isinstance(emulator["identity"], str) and emulator["identity"].strip(),
            "emulator identity is empty")
    for name in ("executable_sha256", "settings_sha256"):
        require(bool(re.fullmatch(r"[0-9a-f]{64}", emulator[name])),
                f"emulator.{name} is not SHA-256")
    require(emulator["evidence_tier"] == "ONE_EMULATOR",
            "emulator evidence tier is not ONE_EMULATOR")
    for name in ("run_started_utc", "report_created_utc"):
        require(isinstance(emulator[name], str) and emulator[name].endswith("Z"),
                f"emulator.{name} is not an explicit UTC time")

    domains = report["domains"]
    exact_keys(domains, {"semantic", "resource", "render", "final_scanout"},
               "domains")

    semantic = domains["semantic"]
    exact_keys(semantic, {"oracle_manifest_sha256", "sample_count",
                          "first_world_frame", "last_world_frame",
                          "state_mismatch_count", "fallback_count",
                          "hit_frame", "ko_frame"}, "domains.semantic")
    require(semantic["oracle_manifest_sha256"] ==
            state_scalar("oracle_manifest_sha256"),
            "semantic readback is bound to the wrong oracle")
    require(nonnegative(semantic["sample_count"], "semantic.sample_count") > 1,
            "semantic readback needs multiple samples")
    first = nonnegative(semantic["first_world_frame"], "semantic.first_world_frame")
    last = nonnegative(semantic["last_world_frame"], "semantic.last_world_frame")
    require(last > first, "world frame did not advance")
    require(nonnegative(semantic["state_mismatch_count"],
                        "semantic.state_mismatch_count") == 0,
            "semantic mismatch recorded")
    require(nonnegative(semantic["fallback_count"], "semantic.fallback_count") == 0,
            "fallback activation recorded")
    hit = nonnegative(semantic["hit_frame"], "semantic.hit_frame")
    ko = nonnegative(semantic["ko_frame"], "semantic.ko_frame")
    require(first <= hit < ko <= last, "HIT/KO frames fall outside readback window")

    resource = domains["resource"]
    exact_keys(resource, {"sample_count", "canary_damage_count",
                          "late_data_read_count", "minimum_headroom_percent",
                          "arenas"}, "domains.resource")
    require(nonnegative(resource["sample_count"], "resource.sample_count") > 0,
            "resource readback has no samples")
    require(nonnegative(resource["canary_damage_count"],
                        "resource.canary_damage_count") == 0,
            "resource canary damage recorded")
    require(nonnegative(resource["late_data_read_count"],
                        "resource.late_data_read_count") == 0,
            "late data read recorded")
    percentage(resource["minimum_headroom_percent"],
               "resource.minimum_headroom_percent")
    arenas = resource["arenas"]
    exact_keys(arenas, {"cartridge", "work_ram", "vdp1_vram", "vdp2_vram",
                        "scsp_ram"}, "domains.resource.arenas")
    for name, arena in arenas.items():
        exact_keys(arena, {"capacity_bytes", "high_water_bytes",
                           "headroom_percent"}, f"resource.arenas.{name}")
        capacity = nonnegative(arena["capacity_bytes"], f"{name}.capacity_bytes")
        high_water = nonnegative(arena["high_water_bytes"],
                                 f"{name}.high_water_bytes")
        require(capacity > 0 and high_water <= capacity,
                f"{name} high-water exceeds capacity")
        percentage(arena["headroom_percent"], f"{name}.headroom_percent")

    render = domains["render"]
    exact_keys(render, {"sample_count", "vdp1_command_sample_count",
                        "vdp1_draw_late_count", "vdp1_draw_margin_percent",
                        "vdp2_register_sample_count", "render_mismatch_count"},
               "domains.render")
    require(nonnegative(render["sample_count"], "render.sample_count") > 0,
            "render readback has no samples")
    require(nonnegative(render["vdp1_command_sample_count"],
                        "render.vdp1_command_sample_count") > 0,
            "no VDP1 command table was sampled")
    require(nonnegative(render["vdp1_draw_late_count"],
                        "render.vdp1_draw_late_count") == 0,
            "late VDP1 draw recorded")
    percentage(render["vdp1_draw_margin_percent"],
               "render.vdp1_draw_margin_percent")
    require(nonnegative(render["vdp2_register_sample_count"],
                        "render.vdp2_register_sample_count") > 0,
            "no VDP2 register state was sampled")
    require(nonnegative(render["render_mismatch_count"],
                        "render.render_mismatch_count") == 0,
            "render mismatch recorded")

    scanout = domains["final_scanout"]
    exact_keys(scanout, {"sample_count", "width", "height", "capture_chain",
                         "output_sha256_samples", "mismatch_count"},
               "domains.final_scanout")
    count = nonnegative(scanout["sample_count"], "final_scanout.sample_count")
    require(count > 0, "final scanout has no samples")
    require(scanout["width"] == 352 and scanout["height"] == 224,
            "final scanout is not 352x224")
    require(isinstance(scanout["capture_chain"], str) and
            scanout["capture_chain"].strip(), "capture chain is missing")
    hashes = scanout["output_sha256_samples"]
    require(isinstance(hashes, list) and len(hashes) == count,
            "final scanout hash count disagrees with samples")
    require(all(isinstance(value, str) and
                re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes),
            "final scanout contains an invalid hash")
    require(nonnegative(scanout["mismatch_count"],
                        "final_scanout.mismatch_count") == 0,
            "final scanout mismatch recorded")

    forbidden = {"SKIP", "UNRUN", "VISUALLY_PLAUSIBLE", "ADAPTED"}
    report_text = json.dumps(report, sort_keys=True)
    require(not any(value in report_text for value in forbidden),
            "release readback contains an incomplete or adapted claim")
    print("canonical release readback: PASS")


if __name__ == "__main__":
    main()
