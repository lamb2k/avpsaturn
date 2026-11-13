import struct, sys, json
iso = sys.argv[1]; store_lba = int(sys.argv[2])
f = open(iso, 'rb')
def sec(n): f.seek((store_lba + n) * 2048); return f.read(2048)
h = sec(0); magic, nr = struct.unpack('>II', h[:8])
print(hex(magic), nr)
hs = 2 if nr > 255 else 1
d = struct.unpack('>%dI' % (512 * hs), b''.join(sec(i) for i in range(hs)))
runs_tab = {}
def run(i):
    s = hs + i // 512
    if s not in runs_tab: runs_tab[s] = struct.unpack('>512I', sec(s))
    v = runs_tab[s][i % 512]; return v >> 14, v & 0x3fff
out = {}
for r in range(nr):
    first, n = d[2 + r * 2], d[3 + r * 2]
    rr = [run(first + k) for k in range(n)]
    out[r] = rr
json.dump({str(k): v for k, v in out.items()}, open('store_runs.json', 'w'))
tot = [(r, len(v), sum(x[1] for x in v)) for r, v in out.items()]
print('rounds', nr, 'max runs', max(t[1] for t in tot), 'avg runs', sum(t[1] for t in tot) / nr, 'avg sectors', sum(t[2] for t in tot) / nr)
for r in (0, 1, 2, 20, 21, 30, 35, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 214):
    if r in out: print(r, 'runs', len(out[r]), 'sectors', sum(x[1] for x in out[r]), 'first', out[r][0], 'span', min(x[0] for x in out[r]), max(x[0] + x[1] for x in out[r]))
