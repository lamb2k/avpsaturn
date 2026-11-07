#!/usr/bin/env python
"""Add referenced-but-unlifted even ROM addresses to roots.txt. Odd values come from data decoded as code and are left out."""
import re
import os
s = open(os.environ.get("LEARN_OUT", "E:/AvP/learning") + "/lift/run/dispatch.inc").read()
m = {int(x, 16) for x in re.findall(r"MISSING ([0-9a-f]+)", s)}
p = str(__import__("pathlib").Path(__file__).parents[1] / "roots.txt")
have = open(p).read().split()
new = [f"{a:x}" for a in sorted(m) if a % 2 == 0 and f"{a:x}" not in have and a < 0x200000]
open(p, "a").write("\n" + "\n".join(new) + "\n")
print("added", len(new), "skipped odd", sum(a % 2 for a in m))
