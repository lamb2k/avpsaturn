from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
result = subprocess.run([sys.executable, str(ROOT / "tools" / "map_avsp_translation_boundary.py"),
                         "--self-test"], text=True, capture_output=True, check=False)
assert result.returncode == 0, result.stdout + result.stderr
assert "negative control pass" in result.stdout
print(result.stdout.strip())
