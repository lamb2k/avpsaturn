"""usage: ldparse.py DIR RUN... : loader log reads (d: steps of sat_ld_n, sat_ld_log[4][4], sat_ld_t0) from run.log -> one line per load: n, file, sectors, D seconds, B seconds since boot; boot time from hwprof_boot.txt"""
import sys, re, os
base = 'E:/AvP/learning/lane-perf-hw/'
d = sys.argv[1]
for run in sys.argv[2:]:
    p = f'{base}{d}/runs/{run}/run.log'
    mem = []
    for l in open(p, errors='replace'):
        m = re.search(r'vb=(\d+) mem ([0-9a-f]+) (.*)', l)
        if m: mem.append((int(m.group(1)), m.group(2), [int(x, 16) for x in m.group(3).split()]))
    loads = {}
    i = 0
    while i + 2 < len(mem):
        a, b, c = mem[i], mem[i + 1], mem[i + 2]
        if len(a[2]) == 1 and len(b[2]) == 16 and len(c[2]) == 1:
            n, lg, t0 = a[2][0], b[2], c[2][0]
            for s in range(4):
                f, sec, ts, te = lg[s * 4:s * 4 + 4]
                if f or sec: loads[(f, sec, ts, te)] = (te - (t0 - 1)) % 3600
            i += 3
        else: i += 1
    print(run, 'loads logged:')
    for (f, sec, ts, te), B in sorted(loads.items(), key=lambda kv: kv[1]):
        print(f'   F{f} S{sec} D{(te - ts) % 3600}s  B{B}s')
    hp = f'{base}{d}/hwprof_boot.txt'
    if os.path.exists(hp):
        w = open(hp).readline().split(); c = open(hp).readlines()[1].split()
        print('   boot dump:', open(hp).readline().strip(), '|', open(hp).readlines()[1].strip())
