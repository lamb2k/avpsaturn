"""Focused committed-artifact contract for the class 0x1F HIT/KO writer set."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "map_avsp_hit_ko_writer_set.py"
REPORT = ROOT / "data" / "avsp_hit_ko_writer_set.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("hit_ko_writer_set", TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load production mapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def must_reject(module, report, mutate, name):
    candidate = copy.deepcopy(report)
    mutate(candidate)
    try:
        module.validate_committed(candidate)
    except (AssertionError, KeyError, TypeError, ValueError):
        return
    raise AssertionError("production validator accepted mutation: " + name)


def main() -> int:
    module = load_tool()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    module.validate_committed(report)

    controls = [
        ("remove HIT anim writer", lambda d: d["correlations"]["hit"]["anim_record_writer_pcs"].pop()),
        ("remove KO anim writer", lambda d: d["correlations"]["ko"]["anim_record_writer_pcs"].pop()),
        ("remove selected edge", lambda d: d["closure"]["selected_edges"].pop()),
        ("unresolved computed target", lambda d: d["closure"]["unresolved_computed_targets"].append("0x000002")),
        ("PC outside boundary", lambda d: d["closure"]["selected_pcs"].__setitem__(0, "0xfffffe")),
        ("ROM dependency relabel", lambda d: d["dependencies"]["rom_data"][0].__setitem__("address_space", "opcodes")),
        ("remove actor field", lambda d: d["coverage"]["actor_fields"].remove("health")),
        ("shift HIT frame", lambda d: d["correlations"]["hit"].__setitem__("source_frame", 5192)),
        ("forbidden raw field", lambda d: d.__setitem__("disassembly_text", "forbidden")),
    ]
    for name, mutate in controls:
        must_reject(module, report, mutate, name)
    print("HIT/KO writer-set committed artifact and 9 mutations passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
