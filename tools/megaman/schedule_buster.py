#!/usr/bin/env python
"""Lane avp-megaman: clean Mega Buster capture - QCF+LP from a standstill every 100 frames, motions held 8 frames each.
usage: schedule_buster.py MSEQ3 OUT_SEQ"""
import sys
head = [l for l in open(sys.argv[1]).read().splitlines() if l.strip() and int(l.split()[0]) < 2100]
ev = []
for f in range(2200, 3200, 100):
    ev += [(f, 'P1 Down', 1), (f + 8, 'P1 Right', 1), (f + 12, 'P1 Down', 0), (f + 16, 'P1 Button 1', 1), (f + 20, 'P1 Right', 0), (f + 22, 'P1 Button 1', 0)]
open(sys.argv[2], 'w').write('\n'.join(head + [f'{a} {b} {c}' for a, b, c in sorted(ev)]) + '\n')
