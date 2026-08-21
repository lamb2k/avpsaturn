"""Focused controls for the translation-boundary completeness validator.

Runs the production validator's mutation controls (no private evidence needed)
and then loads and validates the committed boundary artifact.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
tool = ROOT / "tools" / "map_avsp_translation_boundary.py"

result = subprocess.run([sys.executable, str(tool), "--self-test"],
                        text=True, capture_output=True, check=False)
assert result.returncode == 0, result.stdout + result.stderr
assert "mutation controls" in result.stdout

sys.path.insert(0, str(ROOT / "tools"))
import map_avsp_translation_boundary as boundary  # noqa: E402

artifact = json.loads((ROOT / "data" / "avsp_translation_boundary.json").read_text(encoding="utf-8"))
boundary.validate_committed(artifact)
computed = artifact["target_validation"]["computed_transfers"]
assert artifact["coverage"]["unresolved_indirect_targets"] == []
assert computed["resolved_sites"] == computed["sites"]
assert artifact["target_validation"]["direct_transfers"]["contradictions"] == []
assert artifact["target_validation"]["instruction_space"]["violations"] == []
print("translation-boundary focused controls pass; committed artifact validated")
