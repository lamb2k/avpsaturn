#!/usr/bin/env python3
"""Verify the official Yaba Sanshiro 1.20.37 scanout patch inputs.

This deliberately validates an archive and an *unmodified* extraction before
allowing any patch/build action.  It does not accept the historical Tico tree.
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
MANIFEST_PATH = ROOT / "data" / "yabasanshiro_1_20_37_scanout_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(patch_path: Path | None = None) -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    patch = patch_path or ROOT / manifest["official_patch"]["path"]
    if sha256(patch) != manifest["official_patch"]["sha256"]:
        raise ValueError("official patch hash mismatch")
    return manifest


def verify_archive(archive: Path, manifest: dict) -> None:
    expected = manifest["official_source"]
    if not archive.is_file():
        raise ValueError(f"official archive missing: {archive}")
    if archive.stat().st_size != expected["bytes"]:
        raise ValueError("official archive length mismatch")
    if sha256(archive) != expected["sha256"]:
        raise ValueError("official archive hash mismatch")


def verify_source(source: Path, manifest: dict) -> None:
    if not source.is_dir():
        raise ValueError(f"source directory missing: {source}")
    version = source / "version.json"
    readme = source / "SOURCE_DISTRIBUTION_README.md"
    if not version.is_file() or not readme.is_file():
        raise ValueError("not the official source-distribution root")
    if sha256(version) != manifest["official_source"]["version_json_sha256"]:
        raise ValueError("version.json hash mismatch (wrong source/version)")
    if sha256(readme) != manifest["official_source"]["source_distribution_readme_sha256"]:
        raise ValueError("source-distribution README hash mismatch")
    parsed = json.loads(version.read_text(encoding="utf-8"))
    if (parsed.get("major"), parsed.get("minor"), parsed.get("patch"),
            parsed.get("code")) != (1, 20, 37, 354):
        raise ValueError("official source version identity mismatch")
    if manifest["official_source"]["correspondence_claim"] not in readme.read_text(encoding="utf-8"):
        raise ValueError("official correspondence claim missing")
    for relative, expected in manifest["official_patch"]["preimage_sha256"].items():
        candidate = source / relative
        if not candidate.is_file() or sha256(candidate) != expected:
            raise ValueError(f"preimage mismatch or already-patched source: {relative}")


def patch_applies(source: Path, manifest: dict, patch: Path) -> None:
    result = subprocess.run(["git", "apply", "--check", "--unsafe-paths",
                             f"--directory={source}", str(patch)], cwd=ROOT,
                            text=True, capture_output=True)
    if result.returncode:
        raise ValueError("official patch does not apply to verified source: " + result.stderr.strip())


def expect_rejected(label: str, action) -> None:
    try:
        action()
    except ValueError:
        print(f"negative control rejected: {label}")
        return
    raise AssertionError(f"negative control unexpectedly accepted: {label}")


def negative_controls(source: Path, archive: Path, manifest: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="yb-official-controls-") as temp:
        temp_root = Path(temp)
        corrupt_archive = temp_root / "source.zip"
        shutil.copy2(archive, corrupt_archive)
        with corrupt_archive.open("ab") as handle:
            handle.write(b"x")
        expect_rejected("corrupt archive", lambda: verify_archive(corrupt_archive, manifest))

        wrong_source = temp_root / "wrong-source"
        shutil.copytree(source, wrong_source, ignore=shutil.ignore_patterns(".git"))
        (wrong_source / "version.json").write_text('{"major":1}', encoding="utf-8")
        expect_rejected("wrong version", lambda: verify_source(wrong_source, manifest))

        dirty_source = temp_root / "dirty-source"
        shutil.copytree(source, dirty_source, ignore=shutil.ignore_patterns(".git"))
        watched = dirty_source / "yabause" / "src" / "vidsoft.c"
        watched.write_bytes(watched.read_bytes() + b"\n/* corruption */\n")
        expect_rejected("dirty/already-patched source", lambda: verify_source(dirty_source, manifest))

        original_patch = ROOT / manifest["official_patch"]["path"]
        mutated = temp_root / "mutated.patch"
        mutated.write_bytes(original_patch.read_bytes() + b"\n# mutation\n")
        expect_rejected("mutated patch", lambda: load_manifest(mutated))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--patch", type=Path,
                        help="test-only patch override; it must still match the pinned manifest hash")
    parser.add_argument("--negative-controls", action="store_true")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.patch)
        verify_archive(args.archive, manifest)
        verify_source(args.source, manifest)
        patch_applies(args.source, manifest, args.patch or ROOT / manifest["official_patch"]["path"])
        if args.negative_controls:
            negative_controls(args.source, args.archive, manifest)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"official scanout verifier: FAIL: {exc}", file=sys.stderr)
        return 1
    print("official scanout verifier: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
