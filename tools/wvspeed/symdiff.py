"""usage: symdiff.py A.prof A.elf B.prof B.elf [role=0,2] [N] : per-symbol master (roles) cycles per 1000 vblanks: instr, penalty, region, difference B - A sorted by |diff|. region from the ELF."""
import sys, collections
sys.path.insert(0, 'E:/AvP/learning/lane-wv-speed/ymir_wv')
import importlib.util
src = open('E:/AvP/learning/lane-wv-speed/ymir_wv/hwan.py').read().replace('\nmain()\n', '\n')
ns = {}; exec(compile(src, 'hwan', 'exec'), ns)
def load(prof, elf, roles):
    sm = ns['SymMap'](ns['load_syms'](elf)); reg = ns['region']
    P = collections.defaultdict(lambda: [0, 0]); v = None
    for l in open(prof):
        t = l.split()
        if not t: continue
        if t[0] == 'WINDOW': v = int(t[4]) - int(t[2])
        if t[0] == 'P' and int(t[1]) in roles:
            a = int(t[2], 16); s = sm.find(a); P[s][0] += int(t[3]); P[s][1] += int(t[4])
    sizes = {x[2]: (reg(x[0]), x[1]) for x in sm.syms}
    return {k: (a * 1000.0 / v, b * 1000.0 / v) for k, (a, b) in P.items()}, sizes
roles = [int(x) for x in (sys.argv[5] if len(sys.argv) > 5 else '0,2').split(',')]
A, sa = load(sys.argv[1], sys.argv[2], roles); B, sb = load(sys.argv[3], sys.argv[4], roles)
n = int(sys.argv[6]) if len(sys.argv) > 6 else 40
keys = set(A) | set(B)
rows = []
for k in keys:
    a = A.get(k, (0, 0)); b = B.get(k, (0, 0))
    rows.append((b[0] + b[1] - a[0] - a[1], k, a, b))
rows.sort(key=lambda r: -abs(r[0]))
ta = sum(x[0] + x[1] for x in A.values()); tb = sum(x[0] + x[1] for x in B.values())
print('total cycles per 1000 vblanks (instr+penalty): A %.1fM  B %.1fM' % (ta / 1e6, tb / 1e6))
for d, k, a, b in rows[:n]:
    print('%-30s %-5s diff %9.0f | A instr %9.0f pen %9.0f | B instr %9.0f pen %9.0f | %s' % (k, (sb.get(k) or sa.get(k) or ('?', 0))[0], d, a[0], a[1], b[0], b[1], (sb.get(k) or sa.get(k) or ('?', 0))[1]))
