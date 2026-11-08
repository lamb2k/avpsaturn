#!/usr/bin/env python
"""Lane avp-megaman: MvC schedule that walks in and presses heavy buttons until round 1 is won (win pose, charged Mega Buster shots).
usage: schedule_win.py MSEQ3 OUT_SEQ"""
import sys
head = [l for l in open(sys.argv[1]).read().splitlines() if l.strip() and int(l.split()[0]) < 2100]
ev, f = [], 2160
while f < 7600:
    ev.append((f, 'P1 Right', 1))
    for k, b in ((0, 'P1 Button 3'), (12, 'P1 Button 6'), (24, 'P1 Button 2'), (36, 'P1 Button 5')):
        ev += [(f + k, b, 1), (f + k + 3, b, 0)]
    ev.append((f + 46, 'P1 Right', 0))
    f += 48
open(sys.argv[2], 'w').write('\n'.join(head + [f'{a} {b} {c}' for a, b, c in sorted(ev)]) + '\n')
