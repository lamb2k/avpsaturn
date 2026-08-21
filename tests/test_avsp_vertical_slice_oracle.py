"""Focused no-private-input controls for the vertical-slice oracle.

Runs the verifier's schema/config/perturbation controls, then loads and
validates the committed manifest's downstream perturbation and config identity.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
tool = ROOT / "tools" / "verify_avsp_vertical_slice_oracle.py"
result = subprocess.run([sys.executable, str(tool), "--self-test"], check=False,
                        text=True, capture_output=True)
assert result.returncode == 0, result.stdout + result.stderr
assert "rejection controls pass" in result.stdout

manifest = json.loads(
    (ROOT / "data" / "avsp_vertical_slice_oracle_manifest.json").read_text(encoding="utf-8"))

nc = manifest["negative_control"]
assert nc["input_excluded_projection"] is True
assert nc["downstream_effect_confirmed"] is True
assert nc["first_downstream_different_source_frame"] > nc["frame"], \
    "perturbation effect must be strictly downstream of the injected frame"
assert nc["changed_field_classes"], "at least one downstream field class must change"

prov = manifest["input_provenance"]
configs = set(prov["per_run_config_sha256"].values())
assert configs == {prov["config_baseline_sha256"]}, "every run must share the pinned config"

assert "bank_writes" in manifest["schema_fields"]
assert manifest["cold_runs"]["byte_identical"] is True
assert manifest["cold_runs"]["summary"]["nonvacuous"]["object_bank_writes_advance"] is True
print("vertical-slice oracle focused controls pass; committed manifest validated")
