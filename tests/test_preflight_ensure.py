#!/usr/bin/env python3
"""Failing-first tests for the targeted generated-header ensure.

Chapter 0 of the priority-architecture book: test.ps1 exited before the
RP4 composite gate because generated/avsp_collision.h was missing and
nothing regenerated it before the first collision-dependent host
compilation. The correction adds `--ensure <header>` to
tools/preflight_generated_inputs.py.

Behaviours proven here:

1. a missing mapped header is generated when its inputs exist (real
   private inputs, real producer - runs only when .deps is present);
2. an existing header is not regenerated (producer not invoked);
3. an unknown header is rejected;
4. a missing private input yields an exact, actionable error naming it;
5. a failed producer propagates as failure;
6. determinism: ensuring twice leaves identical bytes.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import preflight_generated_inputs as preflight  # noqa: E402

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"ok   {name}")
    else:
        print(f"FAIL {name} {detail}")
        failures.append(name)


def main() -> None:
    check("module exposes ensure_header",
          hasattr(preflight, "ensure_header"))
    if failures:
        print("preflight ensure tests: ensure_header missing; the "
              "targeted ensure operation is not implemented")
        raise SystemExit(1)

    sandbox = ROOT / "build" / "preflight_ensure_test"
    sandbox.mkdir(parents=True, exist_ok=True)
    fake_out = sandbox / "fake_generated.h"
    fake_input = sandbox / "fake_input.bin"
    fake_input.write_bytes(b"input")
    if fake_out.exists():
        fake_out.unlink()

    saved = dict(preflight.PRODUCERS)
    try:
        rel = fake_out.relative_to(ROOT).as_posix()
        preflight.PRODUCERS["fake_generated.h"] = {
            "command": [sys.executable, "-c",
                        "import pathlib;"
                        f"pathlib.Path(r'{fake_out}')"
                        ".write_text('generated once')"],
            "inputs": [fake_input.relative_to(ROOT).as_posix()],
            "output_override": rel,
        }

        # 3: unknown header rejected.
        try:
            preflight.ensure_header("not_mapped.h")
            check("unknown header rejected", False, "no error raised")
        except SystemExit as error:
            check("unknown header rejected",
                  "no producer mapping" in str(error), str(error))

        # 4: missing private input gives an exact error.
        preflight.PRODUCERS["fake_generated.h"]["inputs"] = [
            "build/preflight_ensure_test/absent.bin"]
        try:
            preflight.ensure_header("fake_generated.h")
            check("missing input rejected", False, "no error raised")
        except SystemExit as error:
            check("missing input rejected",
                  "absent.bin" in str(error), str(error))
        preflight.PRODUCERS["fake_generated.h"]["inputs"] = [
            fake_input.relative_to(ROOT).as_posix()]

        # 1 (mechanism): missing header is produced.
        preflight.ensure_header("fake_generated.h")
        check("missing header generated",
              fake_out.exists() and
              fake_out.read_text() == "generated once")

        # 2: existing header is not regenerated.
        fake_out.write_text("do not touch")
        preflight.ensure_header("fake_generated.h")
        check("existing header untouched",
              fake_out.read_text() == "do not touch")

        # 5: failed producer propagates.
        fake_out.unlink()
        preflight.PRODUCERS["fake_generated.h"]["command"] = [
            sys.executable, "-c", "raise SystemExit(7)"]
        try:
            preflight.ensure_header("fake_generated.h")
            check("failed producer propagated", False, "no error raised")
        except SystemExit as error:
            check("failed producer propagated", True, str(error))

        # producer exits 0 but produces nothing -> rejected.
        preflight.PRODUCERS["fake_generated.h"]["command"] = [
            sys.executable, "-c", "pass"]
        try:
            preflight.ensure_header("fake_generated.h")
            check("empty producer rejected", False, "no error raised")
        except SystemExit as error:
            check("empty producer rejected", True, str(error))
    finally:
        preflight.PRODUCERS.clear()
        preflight.PRODUCERS.update(saved)

    # 1 + 6 (real header): only when the private inputs exist.
    real = ROOT / "generated" / "avsp_collision.h"
    inputs_exist = all(
        (ROOT / i).exists()
        for i in preflight.PRODUCERS["avsp_collision.h"]["inputs"])
    if inputs_exist:
        preflight.ensure_header("avsp_collision.h")
        check("real collision header ensured", real.exists())
        first = real.read_bytes()
        real.unlink()
        preflight.ensure_header("avsp_collision.h")
        check("real collision header deterministic",
              real.read_bytes() == first)
    else:
        print("skip real-header cases: private inputs absent")

    if failures:
        print(f"preflight ensure tests: {len(failures)} FAILURES")
        raise SystemExit(1)
    print("preflight ensure tests: all behaviours hold")


if __name__ == "__main__":
    main()
