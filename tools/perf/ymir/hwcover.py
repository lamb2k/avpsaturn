"""usage: hwcover.py PROF.txt ELF [out_heat.json] - coverage curve of master/slave code (bytes of functions needed per % of instructions), and the per-function heat file."""
import sys, collections, json
sys.path.insert(0, 'E:/AvP/learning/lane-perf-hw/ymir_hw')
import importlib.util
spec = importlib.util.spec_from_file_location('hwan_lib', 'E:/AvP/learning/lane-perf-hw/ymir_hw/hwan.py')
src = open('E:/AvP/learning/lane-perf-hw/ymir_hw/hwan.py').read().replace('\nmain()\n', '\n')
ns = {}
exec(compile(src, 'hwan', 'exec'), ns)
prof, elf = sys.argv[1], sys.argv[2]
sm = ns['SymMap'](ns['load_syms'](elf))
size = {s[2]: s[1] for s in sm.syms}
addr = {s[2]: s[0] for s in sm.syms}
reg = {s[2]: ns['region'](s[0]) for s in sm.syms}
E = collections.defaultdict(lambda: [0, 0, 0])   # (group, sym) -> exec, blocks
for l in open(prof):
    t = l.split()
    if t and t[0] == 'P':
        c = int(t[1]); a = int(t[2], 16); e = int(t[3])
        s = sm.find(a)
        g = 0 if c in (0, 2) else (1 if c == 1 else 2)   # 0 master tasks+irq, 1 slave, 2 master idle
        E[(g, s)][0] += e; E[(g, s)][1] += 1
    elif t and t[0] == 'IF':
        c = int(t[1]); a = int(t[2], 16); n = int(t[3])
        s = sm.find(a)
        g = 0 if c in (0, 2) else (1 if c == 1 else 2)
        E[(g, s)][2] += n
for g, name in ((0, 'master tasks+irq'), (1, 'slave')):
    rows = sorted(((v[0], s) for (gg, s), v in E.items() if gg == g and v[0] > 0), reverse=True)
    tot = sum(r[0] for r in rows); cum = 0; byt = 0; marks = [0.5, 0.8, 0.9, 0.95, 0.98, 0.99, 0.999]; mi = 0
    print(name, 'instr', tot, 'functions executed', len(rows), 'bytes of those', sum(size.get(s, 0) for _, s in rows))
    for i, (e, s) in enumerate(rows):
        cum += e; byt += size.get(s, 0)
        while mi < len(marks) and cum >= marks[mi] * tot:
            print('  %.1f%% of instructions covered by %d functions, %d bytes' % (marks[mi] * 100, i + 1, byt)); mi += 1
    rr = collections.Counter()
    for e, s in rows: rr[reg.get(s, '?')] += size.get(s, 0)
    print('  bytes of executed functions by region now:', dict(rr))
if len(sys.argv) > 3:
    out = {}
    for (g, s), v in E.items():
        if g == 2 and (0, s) not in E: continue
        if g == 2: continue
        d = out.setdefault(s, {'exec': 0, 'ifill': 0, 'size': size.get(s, 0)})
        d['exec'] += v[0]; d['ifill'] += v[2]
    json.dump(out, open(sys.argv[3], 'w'), indent=0)
    print('wrote', sys.argv[3], len(out))
