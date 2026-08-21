"""Focused controls for the translation-boundary completeness validator.

Runs the production validator's mutation controls (no private evidence needed)
and then loads and validates the committed boundary artifact.

A dedicated negative-control battery then mutates exactly one field of the
*committed* artifact at a time and requires the production validate_committed
function to reject it.  The two separation controls bind the opcode/program
divergence proof to every executed PC, so a single-PC "proof" can no longer
pass validation.
"""
from pathlib import Path
import copy
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

ARTIFACT_PATH = ROOT / "data" / "avsp_translation_boundary.json"
artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
boundary.validate_committed(artifact)
computed = artifact["target_validation"]["computed_transfers"]
assert artifact["coverage"]["unresolved_indirect_targets"] == []
assert computed["resolved_sites"] == computed["sites"]
assert artifact["target_validation"]["direct_transfers"]["contradictions"] == []
assert artifact["target_validation"]["instruction_space"]["violations"] == []


# --- Negative-control battery over the *committed* artifact -----------------
# Each control deep-copies the real committed artifact, mutates exactly one
# field, and requires the production validate_committed to reject it for its
# intended invariant.  None of these needs private trace evidence.

def _sites_zero(r):
    r["target_validation"]["direct_transfers"]["sites"] = 0


def _direct_validated_zero(r):
    r["target_validation"]["direct_transfers"]["opcode_and_dynamic_validated"] = 0


def _observed_target_zero(r):
    r["target_validation"]["computed_transfers"]["observed_target_total"] = 0


def _program_bytes_zero(r):
    # Byte count zeroed while the correct program hash is retained: the control
    # must fail on the byte-count invariant alone, not on the hash.
    r["program_image_bytes"] = 0


def _program_sha_wrong(r):
    # Hash replaced while the correct byte count is retained: the control must
    # fail on the image-identity invariant alone.
    r["inputs"]["program_sha256"] = "0" * 64


def _drop_global_attribution(r):
    r["writer_boundary"]["rom_data_reference_counts"] = {}


def _drop_address_space(r):
    r["inputs"]["data_address_space"] = ""


def _compared_to_one(r):
    r["target_validation"]["opcode_program_separation"]["executed_pcs_compared"] = 1


def _divergent_to_one(r):
    r["target_validation"]["opcode_program_separation"]["divergent_pcs"] = 1


CONTROLS = [
    ("direct_sites_zero",
     "target_validation.direct_transfers.sites=0", _sites_zero),
    ("direct_validated_zero",
     "target_validation.direct_transfers.opcode_and_dynamic_validated=0",
     _direct_validated_zero),
    ("computed_observed_target_zero",
     "target_validation.computed_transfers.observed_target_total=0",
     _observed_target_zero),
    ("program_bytes_zero_hash_retained",
     "program_image_bytes=0 (correct hash retained)", _program_bytes_zero),
    ("program_sha_wrong_bytes_retained",
     "inputs.program_sha256='0'*64 (correct byte count retained)",
     _program_sha_wrong),
    ("global_attribution_removed",
     "writer_boundary.rom_data_reference_counts={}", _drop_global_attribution),
    ("data_address_space_removed",
     "inputs.data_address_space=''", _drop_address_space),
    ("separation_compared_reduced",
     "target_validation.opcode_program_separation.executed_pcs_compared=1",
     _compared_to_one),
    ("separation_divergent_reduced",
     "target_validation.opcode_program_separation.divergent_pcs=1",
     _divergent_to_one),
]

not_rejected = []
for name, field, mutate in CONTROLS:
    mutated = copy.deepcopy(artifact)
    mutate(mutated)
    try:
        boundary.validate_committed(mutated)
    except ValueError as exc:
        print("  %-34s REJECTED  %s :: %s" % (name, field, exc))
    else:
        print("  %-34s ACCEPTED  %s" % (name, field))
        not_rejected.append(name)

assert not not_rejected, (
    "committed-artifact controls not rejected by validate_committed: "
    + ", ".join(not_rejected))

print("translation-boundary focused controls pass; committed artifact validated")
