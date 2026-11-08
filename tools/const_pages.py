#!/usr/bin/env python
"""Pages of the program ROM that the lifted code reads at constant addresses (tables addressed by lea/move #imm, OP/RD of a literal).
usage: const_pages.py LIFT_FINAL_DIR OUT.json [LIMIT hex, default 200000 = the whole 2 MB ROM; c0000 drops 86 pages above the code and its tables]   Writes the sorted 1 KB page numbers, each with the page after (tables run forward). 4th argument "all": every immediate address in the lifted code, not only direct reads and lea (829 pages: also pointers loaded by move.l #imm, such as script pointers stored into records, and lea with an index).
Every stage file keeps them (rounds_config.py, env ROUNDS_CONST_PAGES): a read of such a table on a rare path (stage 0c, an alien's grab reads
the per-character table at 0x56632) otherwise finds tiles or zeros where a stage file did not keep the page, and the game faults (0xe2 at 0xa9cc4)."""
import glob, json, re, sys
PAT = [re.compile(r'\ba[0-6]=0x([0-9a-f]+)u;'), re.compile(r'(?:OP|RD)(?:8|16|32)\(\(?0x([0-9a-f]+)u')]
LIMIT = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x200000   # whole ROM, as c0cfe85 (636 pages); c0000 gives 550, which leaves pages 0xc0000-0x1fffff to the census only
ALL = len(sys.argv) > 4 and sys.argv[4] == 'all'
IMM = re.compile(r'(?<!P\()(?<!case )0x([0-9a-f]{3,6})u')   # P(pc) markers and case labels are not addresses
pages = set()
for f in glob.glob(sys.argv[1] + "/c*.c"):
    s = open(f).read()
    for p in ([IMM] if ALL else PAT):
        for m in p.finditer(s):
            a = int(m[1], 16)
            if 0x400 <= a < LIMIT:
                pages.update({a >> 10, min((a >> 10) + 1, 0x7ff)})
json.dump(sorted(pages), open(sys.argv[2], "w"))
print("const pages", len(pages))
