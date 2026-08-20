#!/usr/bin/env python3
"""Own the StreetTest launch, readiness and teardown as one instrument.

The RP4 candidate before this was recorded UNRUN rather than failed: two
600-second launches never reached a live renderer, and the run could not
say whether the candidate draw call was wrong or the guest never booted.
Three separable defects made that indistinguishable, and each is fixed
here rather than in another ad-hoc Start-Process line:

* **Quoting.** The cue path was passed through a string that
  Start-Process re-split on spaces. This module hands the emulator an
  argument *list*, so a path containing spaces is one argument by
  construction and cannot be flattened.
* **Stale disc state.** Every checkout staged its cue at the same fixed
  location under TEMP, and Yaba also remembers a recent disc in its own
  config. A launch could therefore boot a different worktree's ISO while
  every local hash looked right. The staged cue now lives in a directory
  keyed to the checkout, the built artifact hashes are recorded, and the
  disc is always named on the command line.
* **Undifferentiated readiness.** "Ready" was one boolean, so a loaded
  pre-init guest, an initialised runtime with no renderer, and a live
  fixture all looked alike. classify_readiness separates them, and a
  capture taken before the first completed render is refused.

Nothing here judges the RP4 result. It only decides whether the machine
is in a state where a capture means anything.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

READY_NO_GUEST = "no_guest"
READY_PRE_INIT = "loaded_pre_init"
READY_NO_RENDERER = "initialized_no_renderer"
READY_LIVE = "live_fixture"

READY_ORDER = (READY_NO_GUEST, READY_PRE_INIT, READY_NO_RENDERER, READY_LIVE)

BIOS_KEY = "General\\EnableEmulatedBios"

# Yaba Sanshiro settings this instrument requires. An empty BIOS path with
# EnableEmulatedBios=false is unbootable, and it is the configuration the
# UNRUN launches actually ran under.
REQUIRED_SETTINGS = {
    "General\\CdRom": "1",
    BIOS_KEY: "true",
    # 32 Mbit DRAM expansion cartridge, the target hardware configuration.
    "Cartridge\\Type": "7",
    # Never boot a remembered disc; the cue is always given on argv.
    "autostart": "false",
    "Debug\\McpServerEnabled": "true",
    "Debug\\McpServerPort": "9640",
}


def staged_cue_dir(checkout_root: Path) -> Path:
    """A staged-cue directory that cannot collide between checkouts.

    Keyed on the absolute checkout path so two worktrees building the
    same-named ISO never overwrite each other's staged cue.
    """
    key = hashlib.sha256(
        str(Path(checkout_root)).casefold().encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / "AvPSaturnCapabilityTest-launch" / key


def stage_cue_lines(iso: Path, wav: Path) -> list[str]:
    """Cue text whose track files are absolute, so no CWD is implied."""
    iso = Path(iso)
    wav = Path(wav)
    if not iso.is_absolute() or not wav.is_absolute():
        raise ValueError("staged cue tracks must be absolute paths")
    return [
        'FILE "' + str(iso) + '" BINARY',
        "  TRACK 01 MODE1/2048",
        "    INDEX 01 00:00:00",
        "    POSTGAP 00:02:00",
        'FILE "' + str(wav) + '" WAVE',
        "  TRACK 02 AUDIO",
        "    PREGAP 00:02:00",
        "    INDEX 01 00:00:00",
    ]


def emulator_arguments(cue: Path) -> list[str]:
    """Argument list for the pinned Yaba Sanshiro release.

    Returned as a list and never as a joined string: that is what keeps a
    space-containing cue path a single argument.
    """
    return ["-nb", "-a", "-i", str(cue)]


def stale_artifacts(expected: dict, actual: dict) -> list:
    """Names whose live hash is missing or differs from what was built."""
    return sorted(name for name, digest in expected.items()
                  if actual.get(name) != digest)


def classify_readiness(diagnostics) -> str:
    """Separate the four states a launch can actually be in.

    ``advanced`` is set by the poller once it has seen the fixture frame
    change. Objects alone are not enough: the first pass through the
    street loop sets street_objects before a frame has completed, and a
    capture there would read a half-built command table.
    """
    if diagnostics is None:
        return READY_NO_GUEST
    if int(diagnostics.get("runtime_ready", 0)) != 1:
        return READY_PRE_INIT
    if int(diagnostics.get("street_objects", 0)) <= 0:
        return READY_NO_RENDERER
    if diagnostics.get("advanced") or int(diagnostics.get("street_frame", 0)) > 0:
        return READY_LIVE
    return READY_NO_RENDERER


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_settings(ini: Path) -> dict:
    values = {}
    for line in ini.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.startswith("["):
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def required_setting_faults(values: dict) -> list:
    """Settings that make a launch meaningless, reported before spending 600s."""
    faults = [key + "=" + str(values.get(key, "<absent>")) + " (want " + want + ")"
              for key, want in REQUIRED_SETTINGS.items()
              if values.get(key) != want]
    if values.get(BIOS_KEY) != "true" and not values.get("General\\Bios"):
        faults.append("no BIOS image and emulated BIOS disabled: cannot boot")
    return faults


def repair_settings(ini: Path) -> list:
    """Write the required settings back, returning what was changed.

    The launcher owns this because a hand-edited config is exactly how the
    previous run spent 600 seconds on an unbootable machine.
    """
    text = ini.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    changed = []
    seen = set()
    for index, line in enumerate(lines):
        if "=" in line and not line.startswith("["):
            key = line.partition("=")[0].strip()
            if key in REQUIRED_SETTINGS:
                seen.add(key)
                want = REQUIRED_SETTINGS[key]
                if line.partition("=")[2].strip() != want:
                    changed.append(key)
                    lines[index] = key + "=" + want
    for key, want in REQUIRED_SETTINGS.items():
        if key not in seen:
            changed.append(key)
            lines.append(key + "=" + want)
    if changed:
        ini.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sorted(changed)


def stage_cue(checkout_root: Path, iso: Path, wav: Path) -> Path:
    directory = staged_cue_dir(checkout_root)
    directory.mkdir(parents=True, exist_ok=True)
    cue = directory / "game.yaba.cue"
    cue.write_text("\n".join(stage_cue_lines(iso.resolve(), wav.resolve())) + "\n",
                   encoding="ascii", newline="\r\n")
    return cue


def launch(emulator: Path, cue: Path) -> subprocess.Popen:
    arguments = emulator_arguments(cue)
    return subprocess.Popen([str(emulator)] + arguments,
                            cwd=str(Path(emulator).parent))


def poll_diagnostics(mcp, symbols: dict):
    """One paused sample of the StreetTest counters, or None if unreadable."""
    try:
        mcp.call("pause")
        try:
            sample = {
                "runtime_ready": mcp.u32(symbols["_avsp_diag_runtime_ready"]),
                "street_objects": mcp.u32(symbols["_avsp_diag_street_objects"]),
                "street_frame": mcp.u32(symbols["_avsp_diag_street_frame"]),
            }
        finally:
            mcp.call("resume")
    except Exception:
        return None
    return sample


def wait_for_live(mcp, symbols: dict, timeout: float = 600.0,
                  interval: float = 2.0):
    """Wait in stages and report the furthest state actually reached.

    Returns as soon as the fixture frame is seen to advance. On failure it
    returns the best state observed, so the caller can say which of the
    four failure modes happened instead of only "not ready".
    """
    deadline = time.time() + timeout
    best = READY_NO_GUEST
    best_sample = None
    seen_frames = set()
    while time.time() < deadline:
        sample = poll_diagnostics(mcp, symbols)
        if sample is not None:
            seen_frames.add(int(sample.get("street_frame", 0)))
            sample = dict(sample, advanced=len(seen_frames) > 1)
        state = classify_readiness(sample)
        if READY_ORDER.index(state) >= READY_ORDER.index(best):
            best, best_sample = state, sample
        if state == READY_LIVE:
            return state, sample
        time.sleep(interval)
    return best, best_sample


def terminate(process: subprocess.Popen) -> None:
    """Kill only this launcher's process, never every emulator by name."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=15)


def _cpu_state(mcp) -> dict:
    state = {}
    for cpu in ("master", "slave"):
        try:
            state[cpu] = mcp.call("cpu_registers", cpu=cpu)
        except Exception as error:      # diagnostics must never mask the result
            state[cpu] = "unavailable: " + str(error)
    return state


def _emit(report: dict, path) -> None:
    text = json.dumps(report, indent=1, sort_keys=True) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="ascii", newline="\n")
    print(text)


def main() -> int:
    import argparse

    sys.path.insert(0, str(ROOT / "tools"))
    from capture_frontend_cram import Mcp
    from capture_street_command_order import symbols as elf_symbols

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emulator", type=Path, required=True)
    parser.add_argument("--iso", type=Path, default=ROOT / "game.iso")
    parser.add_argument("--wav", type=Path, default=ROOT / "stage1_audio.wav")
    parser.add_argument("--elf", type=Path, default=ROOT / "game.elf")
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--expect-live", action="store_true",
                        help="exit non-zero unless a live fixture is reached; "
                             "the invalid-disc control omits this")
    parser.add_argument("--expect-not-live", action="store_true",
                        help="the invalid-disc negative control: exit non-zero "
                             "if readiness IS somehow satisfied")
    parser.add_argument("--repair-config", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--keep-running", action="store_true")
    parser.add_argument("--capture-label",
                        help="once live, capture the final VDP1 command "
                             "sequence under this label before teardown")
    parser.add_argument("--capture-output", type=Path)
    parser.add_argument("--capture-rel", type=int, default=0)
    parser.add_argument("--capture-frame-lag", type=int, default=0,
                        help="fixture frames the committed VDP1 table trails "
                             "the draw loop: 0 immediate, 1 sorted")
    args = parser.parse_args()

    ini = Path.home() / "AppData/Roaming/YabaSanshiro/yabause.ini"
    report = {"schema": "rp4-street-launch-v0"}
    if ini.exists():
        if args.repair_config:
            report["config_repaired"] = repair_settings(ini)
        report["config_sha256"] = sha256_file(ini)
        report["config_faults"] = required_setting_faults(read_settings(ini))
    else:
        report["config_faults"] = ["yabause.ini absent"]

    report["artifacts"] = {}
    for name, path in (("game.iso", args.iso), ("game.elf", args.elf),
                       ("stage1_audio.wav", args.wav)):
        report["artifacts"][name] = sha256_file(path) if path.exists() else None

    if not args.iso.exists() or not args.wav.exists():
        # The invalid-disc control reaches here: nothing bootable to stage.
        report["state"] = READY_NO_GUEST
        report["note"] = "ISO or audio track absent; nothing was launched"
        _emit(report, args.report)
        if args.expect_live:
            return 1
        return 0

    cue = stage_cue(ROOT, args.iso, args.wav)
    report["staged_cue"] = str(cue)
    report["staged_cue_sha256"] = sha256_file(cue)

    process = launch(args.emulator, cue)
    report["pid"] = process.pid
    report["command_line"] = [str(args.emulator)] + emulator_arguments(cue)
    try:
        mcp = Mcp("http://127.0.0.1:9640/mcp")
        for _ in range(30):             # the MCP server trails the process
            try:
                mcp.initialize()
                break
            except Exception:
                time.sleep(2.0)
        symbols = elf_symbols(args.elf)
        state, sample = wait_for_live(mcp, symbols, timeout=args.timeout)
        report["state"] = state
        report["diagnostics"] = sample
        if state != READY_LIVE:
            report["cpu"] = _cpu_state(mcp)
        elif args.capture_label:
            # Capturing inside the launcher keeps one owner of the PID from
            # boot through capture, so a capture can never be attributed to
            # a process this run did not start.
            from capture_street_vdp1 import capture_at

            report["capture"] = capture_at(
                mcp, symbols, args.capture_label, args.capture_rel,
                args.elf, args.iso, args.capture_output, args.timeout,
                frame_lag=args.capture_frame_lag)
    finally:
        if not args.keep_running or report.get("state") != READY_LIVE:
            terminate(process)
            report["terminated_pid"] = process.pid

    _emit(report, args.report)
    if args.expect_live and report.get("state") != READY_LIVE:
        return 1
    if args.expect_not_live and report.get("state") == READY_LIVE:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
