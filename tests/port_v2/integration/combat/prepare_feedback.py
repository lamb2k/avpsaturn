#!/usr/bin/env python3
"""Create the ignored USER-03 combat-feel review package."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RUN = ROOT / "build/port_v2/integration/combat/run-1"
PACKAGE = ROOT / "build/feedback/USER-03-COMBAT-FEEL-REVIEW"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    readback = json.loads((RUN / "readback.json").read_text(encoding="ascii"))
    contract = json.loads((HERE / "alignment_contract.json").read_text())
    if readback["result"] != "PASS" or readback["physical_saturn"] != "UNRUN":
        raise ValueError("combat readback is not reviewable at its declared tier")
    PACKAGE.mkdir(parents=True, exist_ok=True)
    files = {}
    for source_name, output_name in (
            ("hit.png", "combat-hit.png"),
            ("ko.png", "combat-ko.png"),
            ("readback.json", "readback.json"),
            ("build.json", "build.json"),
            ("iso-normalization.json", "iso-normalization.json")):
        source = RUN / source_name
        output = PACKAGE / output_name
        shutil.copy2(source, output)
        files[output_name] = {"sha256": sha256(output), "bytes": output.stat().st_size}
    manifest = {
        "schema": 1,
        "task_id": "USER-03-COMBAT-FEEL-REVIEW",
        "source_task": contract["task_id"],
        "implementation_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "normalized_iso_sha256": readback["iso_sha256"],
        "files": files,
        "review_scope": [
            "player attack presentation",
            "alien HIT presentation",
            "alien terminal KO presentation",
            "source-relative position, facing, shared lane baseline, scale, "
            "palette, and readability"
        ],
        "excluded": [
            "general enemy AI",
            "second and third HIT reaction timing",
            "general attack and damage rules",
            "combat audio",
            "physical Saturn proof"
        ],
        "physical_saturn": "UNRUN"
    }
    (PACKAGE / "package.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="ascii", newline="\n")
    (PACKAGE / "README.md").write_text(
        "# USER-03 combat-feel review\n\n"
        "Open `combat-hit.png` and `combat-ko.png`. Review the attack/HIT/KO "
        "presentation, source-relative actor position and facing, shared lane "
        "baseline, scale, palette, and visual readability. The package is "
        "pinned Yaba Sanshiro evidence from one "
        "emulator only. Physical Saturn remains `UNRUN`.\n\n"
        "The second and third source damage events do not yet promote their "
        "reaction timing. General attack rules, damage rules, enemy AI, and "
        "combat audio are outside this review.\n",
        encoding="ascii", newline="\n")
    print(f"prepared ignored feedback package: {PACKAGE}")


if __name__ == "__main__":
    main()
