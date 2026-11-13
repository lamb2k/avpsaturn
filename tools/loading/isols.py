import struct, sys
f = open(sys.argv[1], 'rb')
def rd(lba, n=1):
    f.seek(lba * 2048); return f.read(2048 * n)
pvd = rd(16)
assert pvd[1:6] == b'CD001', pvd[:8]
root = pvd[156:190]
rlba, rlen = struct.unpack('<I', root[2:6])[0], struct.unpack('<I', root[10:14])[0]
def walk(lba, ln, path=''):
    d = rd(lba, (ln + 2047) // 2048)
    o = 0; out = []
    while o < len(d):
        l = d[o]
        if l == 0:
            o = (o // 2048 + 1) * 2048; continue
        elba = struct.unpack('<I', d[o+2:o+6])[0]; esz = struct.unpack('<I', d[o+10:o+14])[0]
        fl = d[o+25]; nl = d[o+32]; nm = d[o+33:o+33+nl]
        if nm not in (b'\x00', b'\x01'):
            name = nm.decode('latin1').split(';')[0]
            out.append((path + name, elba, esz, fl & 2))
            if fl & 2: out += walk(elba, esz, path + name + '/')
        o += l
    return out
ents = walk(rlba, rlen)
for n, l, s, dr in sorted(ents, key=lambda e: e[1]):
    print(f'{l:8d} {s:10d} {(s+2047)//2048:6d} {"D" if dr else " "} {n}')
