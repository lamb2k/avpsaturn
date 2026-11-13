"""usage: sumcmp.py DIR KIND : compare the SAT_LOAD_SUM words (load count, multiplicative sum) read after each shot in sum_PS0_KIND and sum_PS1_KIND"""
import sys, re
base = 'E:/AvP/learning/lane-perf-hw/'
def loads(run):
    seen = {}
    for l in open(f'{base}{sys.argv[1]}/runs/{run}/run.log', errors='replace'):
        m = re.search(r'mem 6013fb8 ([0-9a-f]+) ([0-9a-f]+)', l)
        if m: seen[int(m.group(1), 16)] = int(m.group(2), 16)
    return seen
a, b = loads('sum_PS0_' + sys.argv[2]), loads('sum_PS1_' + sys.argv[2])
ks = sorted(set(a) | set(b))
print(sys.argv[2], 'loads seen: PS0', sorted(a), 'PS1', sorted(b))
bad = 0
for k in ks:
    if k in a and k in b:
        ok = a[k] == b[k]; bad += not ok
        print(f'  load {k}: PS0 {a[k]:08x} PS1 {b[k]:08x} {"same" if ok else "DIFFERENT"}')
    else: print(f'  load {k}: only in', 'PS0' if k in a else 'PS1')
print('RESULT', 'identical' if not bad else f'{bad} differ', 'over', sum(1 for k in ks if k in a and k in b), 'loads')
