import json, struct, sys
runs=json.load(open('E:/AvP/learning/lane-loading/store_runs.json'))
def expected(iso, store_lba, r):
    f=open(iso,'rb')
    data=b''.join((f.seek((store_lba+a)*2048), f.read(n*2048))[1] for a,n in runs[str(r)])
    cnt=struct.unpack('>I',data[:4])[0]
    regs=[struct.unpack('>II',data[4+8*i:12+8*i]) for i in range(cnt)]
    pos=2048
    mem=bytearray(0x400000)  # 0x02400000..0x027fffff
    for d,b in regs:
        if d==1: continue
        assert 0x02400000<=d and d+b<=0x02800000, (hex(d),b)
        mem[d-0x02400000:d-0x02400000+b]=data[pos:pos+b]; pos+=b
    s=0
    for d,b in regs:
        if d==1: continue
        o=d-0x02400000
        for q in range(0,b,4):
            w=struct.unpack('>I',mem[o+q:o+q+4])[0]
            s=((s<<1|s>>31)&0xffffffff)^w
    return s, cnt, pos//2048
if __name__=='__main__':
    iso=sys.argv[1]; st=int(sys.argv[2])
    for r in map(int,sys.argv[3:]):
        s,c,p=expected(iso,st,r); print(r,'regions',c,'sectors',p,'sum %08x'%s)
