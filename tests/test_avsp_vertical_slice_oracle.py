"""Focused no-private-input controls for the vertical-slice oracle."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
tool = ROOT / "tools" / "verify_avsp_vertical_slice_oracle.py"
result = subprocess.run([sys.executable, str(tool), "--self-test"], check=False,
                        text=True, capture_output=True)
assert result.returncode == 0, result.stdout + result.stderr
assert "rejection controls pass" in result.stdout
print(result.stdout.strip())
