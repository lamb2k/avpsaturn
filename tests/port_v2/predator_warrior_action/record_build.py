#!/usr/bin/env python3
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "predator_warrior_action_bench/record_build.py"
spec = importlib.util.spec_from_file_location("pw_record", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = Path(__file__).resolve().parent
module.main()
