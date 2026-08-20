#!/usr/bin/env python3
"""Verify the reproducible, rejected Yaba Sanshiro scanout experiment.

This deliberately verifies only a clean source tree at the manifest-pinned
revision.  It does not make a claim about the pinned release and must never be
used as an RP4 acceptance check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "yabasanshiro_scanout_diagnostic_manifest.json"


class VerificationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True)


def run_bytes(command: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=cwd, capture_output=True)


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("classification") != "REPRODUCES_A_REJECTED_CUSTOM_DIAGNOSTIC_BUILD":
        raise VerificationError("diagnostic manifest classification changed")
    patch = ROOT / manifest["patch"]["path"]
    if sha256(patch) != manifest["patch"]["sha256"]:
        raise VerificationError("tracked diagnostic patch hash differs from manifest")
    return manifest


def verify_clean_base(source: Path, manifest: dict) -> None:
    source = source.resolve()
    revision = run(["git", "rev-parse", "HEAD"], source)
    if revision.returncode or revision.stdout.strip().lower() != manifest["source"]["revision"]:
        raise VerificationError("wrong source base (requires exact 71c973f revision)")
    for rel, expected in manifest["patch"]["prepatch_files"].items():
        actual_path = source / rel
        blob = run_bytes(["git", "show", f"HEAD:{rel}"], source)
        # The source checkout can use CRLF on Windows, so hash the Git blob
        # rather than its checkout conversion.  A separate diff check catches
        # a locally corrupted (or already patched) working file.
        dirty = run(["git", "diff", "--quiet", "--", rel], source)
        if (not actual_path.is_file() or blob.returncode or
                hashlib.sha256(blob.stdout).hexdigest() != expected or
                dirty.returncode != 0):
            raise VerificationError(f"corrupt or already-patched base: {rel}")
    patch = ROOT / manifest["patch"]["path"]
    # The upstream checkout advertises core.autocrlf=true.  Its patch is
    # content-clean but needs Git's EOL-insensitive application mode; the
    # manifest's Git-blob hashes above remain the byte-exact base check.
    check = run(["git", "apply", "--check", "--ignore-space-change",
                 str(patch)], source)
    if check.returncode:
        raise VerificationError("patch does not apply cleanly: " + check.stderr.strip())


def exercise_negative_controls(source: Path, manifest: dict) -> None:
    """Prove a clean base passes while wrong and corrupt bases are rejected."""
    with tempfile.TemporaryDirectory(prefix="yb-scanout-verify-") as temp:
        clone = Path(temp) / "source"
        clone_result = run(["git", "clone", "--quiet", "--no-hardlinks", str(source), str(clone)])
        if clone_result.returncode:
            raise VerificationError("could not create negative-control clone: " + clone_result.stderr)
        run(["git", "checkout", "--quiet", manifest["source"]["revision"]], clone)
        verify_clean_base(clone, manifest)

        wrong = run(["git", "checkout", "--quiet", "HEAD~1"], clone)
        if wrong.returncode:
            raise VerificationError("cannot construct wrong-base control")
        try:
            verify_clean_base(clone, manifest)
        except VerificationError:
            pass
        else:
            raise VerificationError("wrong-base negative control unexpectedly passed")

        run(["git", "checkout", "--quiet", manifest["source"]["revision"]], clone)
        corrupt_path = clone / "yabause/src/vidsoft.c"
        corrupt_path.write_bytes(corrupt_path.read_bytes() + b"\n/* corruption control */\n")
        try:
            verify_clean_base(clone, manifest)
        except VerificationError:
            pass
        else:
            raise VerificationError("corruption negative control unexpectedly passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="clean checkout at the exact manifest revision")
    parser.add_argument("--negative-controls", action="store_true")
    args = parser.parse_args()
    try:
        manifest = load_manifest()
        verify_clean_base(args.source, manifest)
        if args.negative_controls:
            exercise_negative_controls(args.source, manifest)
    except VerificationError as error:
        print(f"rejected diagnostic verification: {error}", file=sys.stderr)
        return 3
    print("rejected diagnostic verification: clean patch applies; classification preserved")
    if args.negative_controls:
        print("negative controls: wrong base and corrupt base rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
