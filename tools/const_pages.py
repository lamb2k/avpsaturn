#!/usr/bin/env python
"""Pages of the program ROM that the lifted code reads at constant addresses (tables addressed by lea/move #imm, OP/RD of a literal).
usage: const_pages.py LIFT_FINAL_DIR OUT.json   Writes the sorted 1 KB page numbers, each with the page after (tables run forward).
Every stage file keeps them (rounds_config.py, env ROUNDS_CONST_PAGES): a read of such a table on a rare path (stage 0c, an alien's grab reads
the per-character table at 0x56632) otherwise finds tiles or zeros where a stage file did not keep the page, and the game faults (0xe2 at 0xa9cc4)."""
import glob, json, re, sys
PAT = [re.compile(r'\ba[0-6]=0x([0-9a-f]+)u;'), re.compile(r'(?:OP|RD)(?:8|16|32)\(\(?0x([0-9a-f]+)u')]
pages = set()
for f in glob.glob(sys.argv[1] + "/c*.c"):
    s = open(f).read()
    for p in PAT:
        for m in p.finditer(s):
            a = int(m[1], 16)
            if 0x400 <= a < 0x200000:
                pages.update({a >> 10, min((a >> 10) + 1, 0x7ff)})
json.dump(sorted(pages), open(sys.argv[2], "w"))
print("const pages", len(pages))
