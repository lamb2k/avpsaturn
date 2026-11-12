"""usage: hwan.py PROF.txt ELF [topN]  - maps a hwprof dump (PC blocks, fills, data misses) to symbols and prints the hot-path tables."""
import sys, subprocess, bisect, collections
NM = 'E:/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe'

def load_syms(elf):
    out = subprocess.run([NM, '-S', '-n', elf], capture_output=True, text=True).stdout
    syms = []
    for l in out.splitlines():
        p = l.split()
        if len(p) == 4:
            try: syms.append((int(p[0], 16), int(p[1], 16), p[3], p[2]))
            except ValueError: pass
        elif len(p) == 3:
            try: syms.append((int(p[0], 16), 0, p[2], p[1]))
            except ValueError: pass
    syms.sort()
    return syms

class SymMap:
    def __init__(self, syms):
        self.syms = syms; self.addrs = [s[0] for s in syms]
    def find(self, a):
        i = bisect.bisect_right(self.addrs, a) - 1
        if i < 0: return '?'
        s = self.syms[i]
        if s[1] and a >= s[0] + s[1]:
            # beyond size: attribute to the symbol anyway if within 64 bytes (padding) else unknown
            if a >= s[0] + s[1] + 64: return '?%08x' % a
        return s[2]

def region(a):
    a &= 0x1FFFFFFF
    if a >= 0x06000000: return 'HW'
    if 0x00200000 <= a < 0x00300000: return 'LW'
    if 0x02000000 <= a < 0x05000000: return 'CART'
    return 'OTH'

def main():
    prof, elf = sys.argv[1], sys.argv[2]
    topn = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    sm = SymMap(load_syms(elf)); REG = {x[2]: (region(x[0]), x[1]) for x in sm.syms}
    cpu_tot = {}; K = collections.defaultdict(lambda: [0, 0])
    P = collections.defaultdict(lambda: [0, 0, 0])   # (cpu, sym) -> exec, pen, blocks
    PR = collections.defaultdict(lambda: [0, 0])     # (cpu, region of pc) -> exec, pen
    DF = collections.defaultdict(int); DT = collections.defaultdict(int); DW = collections.defaultdict(int); IF = collections.defaultdict(int)
    win = ''
    for l in open(prof):
        t = l.split()
        if not t: continue
        if t[0] == 'WINDOW': win = l.strip()
        elif t[0] == 'CPU': cpu_tot[int(t[1])] = (int(t[3]), int(t[5]))
        elif t[0] == 'K': K[(int(t[1]), t[2], t[3])] = [int(t[5]), int(t[7])]
        elif t[0] == 'P':
            c = int(t[1]); a = int(t[2], 16); e = int(t[3]); p = int(t[4])
            s = sm.find(a); P[(c, s)][0] += e; P[(c, s)][1] += p; P[(c, s)][2] += 1
            PR[(c, region(a))][0] += e; PR[(c, region(a))][1] += p
        elif t[0] in ('DF', 'DT', 'DW', 'IF'):
            c = int(t[1]); a = int(t[2], 16); n = int(t[3])
            {'DF': DF, 'DT': DT, 'DW': DW, 'IF': IF}[t[0]][(c, sm.find(a) if (a & 0x1FFFFFFF) >= 0x00200000 and not (0x05000000 <= (a & 0x1FFFFFFF) < 0x06000000) else 'IO%08x' % (a & ~0xfff))] += n
    print(win)
    for c in (0, 2, 3, 1):
        if c not in cpu_tot: continue
        ins, cyc = cpu_tot[c]
        print('\n=== CPU %d (%s): %d instructions, %d cycles charged in window' % (c, ['master-tasks','slave','master-irq','master-idle'][c], ins, cyc))
        for (cc, k, r), (n, cy) in sorted(K.items()):
            if cc == c: print('   %-7s %-5s n %-10d cycles %-10d (%.1f%% of window)' % (k, r, n, cy, 100.0 * cy / max(cyc, 1)))
        print('  executed by PC region:')
        for (cc, r), (e, p) in sorted(PR.items()):
            if cc == c: print('   %-5s instr %-10d (%.1f%%) fill/stall cycles on them %d' % (r, e, 100.0 * e / max(ins, 1), p))
        rows = sorted(((v[0] + v[1], k[1], v) for k, v in P.items() if k[0] == c), reverse=True)[:topn]
        print('  top symbols by exec+penalty (instr, penalty cycles, 32B blocks touched):')
        for tot, s, v in rows: print('   %-34s instr %-9d pen %-9d blk %d %s size %s' % (s, v[0], v[1], v[2], REG.get(s, ('',0))[0], REG.get(s, ('',0))[1]))
        for name, D in (('instruction line fills', IF), ('data line fills (dcache misses)', DF), ('cache-through reads (64B buckets)', DT), ('writes (64B buckets)', DW)):
            rows = sorted(((n, k[1]) for k, n in D.items() if k[0] == c), reverse=True)
            print('  %s: total %d; top:' % (name, sum(n for n, _ in rows)))
            for n, s in rows[:12]: print('   %-34s %-9d %s size %s' % (s, n, REG.get(s, ('',0))[0], REG.get(s, ('',0))[1]))

main()
