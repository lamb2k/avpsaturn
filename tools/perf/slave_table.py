#!/usr/bin/env python
"""usage: slave_table.py PROF.txt ELF DRAWS [topN]   (lane perf-pic)  The slave SH-2's work in a profiled window, per slave draw, by function group: instructions and stall cycles (cache line fills, write buffer waits)
from the profiling Ymir's dump, MODELLED costs. The idle wait (sat_slave_main polling its timer flag) is split out. Cycles a draw ~ instructions + stalls (CPI is about 1 for these loops)."""
import collections, subprocess, sys, bisect
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
prof, elf, draws = sys.argv[1], sys.argv[2], int(sys.argv[3]); topn = int(sys.argv[4]) if len(sys.argv) > 4 else 14
NM = 'E:/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe'
syms = []
for l in subprocess.run([NM, '-n', elf], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) == 3:
        try: syms.append((int(p[0], 16), p[2]))
        except ValueError: pass
A = [a for a, _ in syms]
def sym(a):
    i = bisect.bisect_right(A, a) - 1
    return syms[i][1].lstrip('_').split('.')[0] if i >= 0 else '?'
GROUP = {
 'sat_gfx_draw': 'sprite build (draw_sprites inlined in sat_gfx_draw) and the rest of the draw',
 'cache_find': 'cache_find (tile lookups, sprites and scroll 1)',
 'sat_slave_main': 'idle wait', 'draw_scroll1': 'scroll 1: draw_scroll1', 'home_row_blank': 'scroll 1: home_row_blank (blank masks)',
 'home_row_map': 'scroll 1: home_row_map / home_map', 'home_map_calc': 'scroll 1: home_row_map / home_map', 's1_blank_row': 'scroll 1: blank rows, restamp, expand',
 's1_restamp': 'scroll 1: blank rows, restamp, expand', 's1_expand': 'scroll 1: blank rows, restamp, expand', 'home_maps_rows': 'scroll 1: draw_scroll1',
 '__lshrsi3_r0': 'compiler shifts', '__ashlsi3_r0': 'compiler shifts', '__ashrsi3': 'compiler shifts', 'sat_gfx_bank': 'scroll 1: name_of, sat_gfx_bank', 'name_of': 'scroll 1: name_of, sat_gfx_bank',
}
ex = collections.Counter(); pen = collections.Counter()
for l in open(prof):
    t = l.split()
    if len(t) >= 5 and t[0] == 'P' and t[1] == '1':
        g = GROUP.get(sym(int(t[2], 16)), 'other'); ex[g] += int(t[3]); pen[g] += int(t[4])
tot = sum(ex.values()) + sum(pen.values())
print('%-62s %10s %10s %9s' % ('slave, per draw (%d draws)' % draws, 'instr', 'stall cyc', 'share'))
busy = tot - ex['idle wait'] - pen['idle wait']
for g, _ in sorted(ex.items(), key=lambda kv: -(kv[1] + pen[kv[0]]))[:topn]:
    print('%-62s %10.0f %10.0f %8.1f%%' % (g, ex[g] / draws, pen[g] / draws, 100.0 * (ex[g] + pen[g]) / max(tot, 1)) + ('   (not work)' if g == 'idle wait' else ''))
print('%-62s %10.0f %10.0f' % ('total, idle wait left out', (sum(ex.values()) - ex['idle wait']) / draws, (sum(pen.values()) - pen['idle wait']) / draws))
