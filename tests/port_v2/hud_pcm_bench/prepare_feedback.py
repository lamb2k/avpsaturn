#!/usr/bin/env python3
"""Create the ignored USER-05 visual/audio review package."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from verify_iso_file import read_iso_path  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    contract = json.loads((HERE / "hud_pcm_contract.json").read_text(
        encoding="utf-8"))
    run_root = ROOT / "build/port_v2/hud_pcm_bench/run-2"
    readback = json.loads((run_root / "readback.json").read_text(
        encoding="ascii"))
    package = ROOT / "build/feedback/USER-05-HUD-PCM-REVIEW"
    package.mkdir(parents=True, exist_ok=True)
    source_image = ROOT / readback["final_scanout"]["screenshot"]["path"]
    screenshot = package / "hud-pcm-together.png"
    shutil.copy2(source_image, screenshot)

    pcm = read_iso_path((ROOT / "game.iso").read_bytes(),
                        "/AUDIO/MELEE.PCM")
    if hashlib.sha256(pcm).hexdigest() != \
            contract["payload_sha256"]["/AUDIO/MELEE.PCM"]:
        raise ValueError("review PCM does not match the accepted cue payload")
    if len(pcm) % 2:
        raise ValueError("16-bit PCM payload has an odd byte count")
    little = bytearray(len(pcm))
    little[0::2] = pcm[1::2]
    little[1::2] = pcm[0::2]
    wav_path = package / "predator-melee-cue.wav"
    with wave.open(str(wav_path), "wb") as output:
        output.setnchannels(contract["pcm"]["channels"])
        output.setsampwidth(contract["pcm"]["sample_bits"] // 8)
        output.setframerate(contract["pcm"]["sample_rate"])
        output.writeframes(little)

    for name in ("build.json", "iso-normalization.json", "readback.json"):
        shutil.copy2(run_root / name, package / name)
    manifest = {
        "schema": 1,
        "task_id": "USER-05-HUD-PCM-REVIEW",
        "source_task": contract["task_id"],
        "files": {
            screenshot.name: {"sha256": sha256(screenshot),
                              "purpose": "corrected HUD colors with PCM together checkpoint"},
            wav_path.name: {"sha256": sha256(wav_path),
                            "purpose": "capture-exact short melee cue"},
        },
        "physical_saturn": "UNRUN",
    }
    (package / "package.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    (package / "README.md").write_text(
        "# USER-05 HUD/PCM review\n\n"
        "Open `hud-pcm-together.png` to inspect the corrected-color, mid-value "
        "HUD state. "
        "Play `predator-melee-cue.wav` to review the one short PCM cue.\n\n"
        "This is pinned-emulator evidence only. Physical Saturn remains "
        "`UNRUN`. Camera movement, stage expansion, combat, and CDDA are "
        "outside this review.\n",
        encoding="ascii", newline="\n")
    print(f"prepared ignored feedback package: {package}")


if __name__ == "__main__":
    main()
