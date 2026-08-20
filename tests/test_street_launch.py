#!/usr/bin/env python3
"""Failing-first checks for the RP4 StreetTest launch/capture helper.

The prior RP4 candidate was recorded UNRUN because the launch path had
three separable defects, and the run could not tell them apart:

* an unquoted cue path was flattened by `Start-Process`, so a path with
  spaces reached the emulator as several arguments;
* the staged cue lived at one fixed `%TEMP%` location shared by every
  worktree, so a launch could silently boot another checkout's ISO;
* "ready" was read as a single boolean, so a loaded-but-uninitialised
  guest and a live renderer were not distinguished, and 600 seconds were
  spent before the failure mode was known.

These are host-testable decisions, so they are tested here as pure
functions before the helper is changed.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from street_launch import (  # noqa: E402
    READY_LIVE,
    READY_NO_GUEST,
    READY_NO_RENDERER,
    READY_PRE_INIT,
    classify_readiness,
    emulator_arguments,
    stage_cue_lines,
    staged_cue_dir,
    stale_artifacts,
)


def check_quoting() -> None:
    """The cue must reach the emulator as exactly one argument."""
    spaced = Path(r"C:\Game Dev\Avp Saturn\game.yaba.cue")
    args = emulator_arguments(spaced)
    assert args == ["-nb", "-a", "-i", str(spaced)], args
    # One argv element, not three. This is the defect that flattened the
    # first recorded launch.
    assert sum(1 for a in args if "game.yaba.cue" in a) == 1, args
    assert not any(a.startswith('"') or a.endswith('"') for a in args), args
    assert not any(" " in a for a in args[:3]), args


def check_cue_is_absolute() -> None:
    iso = Path(r"C:\Game Dev\Avp Saturn\game.iso")
    wav = Path(r"C:\Game Dev\Avp Saturn\stage1_audio.wav")
    lines = stage_cue_lines(iso, wav)
    assert lines[0] == r'FILE "C:\Game Dev\Avp Saturn\game.iso" BINARY', lines
    assert any("stage1_audio.wav" in line for line in lines), lines
    for line in lines:
        if line.startswith("FILE "):
            inner = line.split('"')[1]
            assert Path(inner).is_absolute(), line


def check_cue_dir_is_per_checkout() -> None:
    """Two checkouts must never share one staged cue location."""
    a = staged_cue_dir(Path(r"C:\wt\AvPSaturnCapabilityTest"))
    b = staged_cue_dir(Path(r"C:\wt\AvPSaturnCapabilityTest-ClaudeRp4DirectOrder"))
    assert a != b, (a, b)
    assert staged_cue_dir(Path(r"C:\wt\AvPSaturnCapabilityTest")) == a
    # The old shared path is exactly what made a stale disc undetectable.
    assert a.name != "AvPSaturnCapabilityTest", a


def check_stale_artifacts() -> None:
    expected = {"game.iso": "aa", "game.elf": "bb"}
    assert stale_artifacts(expected, {"game.iso": "aa", "game.elf": "bb"}) == []
    assert stale_artifacts(expected, {"game.iso": "aa", "game.elf": "cc"}) == ["game.elf"]
    assert stale_artifacts(expected, {"game.iso": "aa"}) == ["game.elf"]


def check_readiness_states() -> None:
    assert classify_readiness(None) == READY_NO_GUEST
    assert classify_readiness({"runtime_ready": 0, "street_objects": 0,
                               "street_frame": 0}) == READY_PRE_INIT
    assert classify_readiness({"runtime_ready": 1, "street_objects": 0,
                               "street_frame": 0}) == READY_NO_RENDERER
    # Objects drawn but the fixture frame has never advanced is still not a
    # capturable state: a capture before the first completed render is
    # exactly what must be rejected.
    assert classify_readiness({"runtime_ready": 1, "street_objects": 464,
                               "street_frame": 0}) == READY_NO_RENDERER
    assert classify_readiness({"runtime_ready": 1, "street_objects": 464,
                               "street_frame": 0, "advanced": True}) == READY_LIVE
    assert classify_readiness({"runtime_ready": 1, "street_objects": 464,
                               "street_frame": 7}) == READY_LIVE


def main() -> None:
    check_quoting()
    check_cue_is_absolute()
    check_cue_dir_is_per_checkout()
    check_stale_artifacts()
    check_readiness_states()
    print("street launch helper: quoting, staging, staleness and readiness hold")


if __name__ == "__main__":
    main()
