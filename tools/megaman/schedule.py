#!/usr/bin/env python
"""Lane avp-megaman: MvC input schedule for the full brawler capture (select from guest-analysis mseq3, then one move per window).
usage: schedule.py MSEQ3 OUT_SEQ OUT_WINDOWS_JSON"""
import json, sys
head = [l for l in open(sys.argv[1]).read().splitlines() if l.strip() and int(l.split()[0]) < 2100]
ev, W = [], {}
def hold(f, b, n=4): ev.extend([(f, b, 1), (f + n, b, 0)])
f = 2150; W['idle'] = (f, f + 59); f += 60
hold(f, 'P1 Right', 70); W['walk'] = (f, f + 79); f += 80
hold(f, 'P1 Left', 50); W['walkback'] = (f, f + 59); f += 60
hold(f, 'P1 Right', 3); hold(f + 6, 'P1 Right', 3); W['dash'] = (f, f + 59); f += 60
hold(f, 'P1 Down', 60); W['crouch'] = (f, f + 79); f += 80
hold(f, 'P1 Up'); W['jump'] = (f, f + 69); f += 70
hold(f, 'P1 Button 1'); W['lp'] = (f, f + 39); f += 40
hold(f, 'P1 Button 3'); W['hp'] = (f, f + 59); f += 60
hold(f, 'P1 Button 6'); W['hk'] = (f, f + 69); f += 70
hold(f, 'P1 Down', 12); hold(f + 2, 'P1 Button 5'); W['slide'] = (f, f + 59); f += 60
hold(f, 'P1 Down', 6); hold(f + 4, 'P1 Right', 6); hold(f + 9, 'P1 Button 1'); W['buster'] = (f, f + 89); f += 90
hold(f, 'P1 Down', 6); hold(f + 4, 'P1 Left', 6); hold(f + 9, 'P1 Button 4'); W['rush'] = (f, f + 119); f += 120
hold(f, 'P1 Right', 150)
for k in range(30, 150, 20): hold(f + k, 'P1 Button 3')
W['throw'] = (f, f + 179); f += 180
W['hit_etc'] = (f, f + 5000); f += 5000
open(sys.argv[2], 'w').write('\n'.join(head + [f'{a} {b} {c}' for a, b, c in sorted(ev)]) + '\n')
json.dump(W, open(sys.argv[3], 'w'))
print('last', f)
