import json,re
d=json.load(open('E:/AvP/learning/cfg.json'));op=open('op.bin','rb').read()
funcs=set(d['funcs']);seen={int(k,16) for k in d['seen']};tab={int(k,16) for k in d['tables']}
print(len(funcs),len(seen),list(d['tables'].items())[0][0])
res=[];new=set()
for a in range(0,0x200000,2):
    w=op[a:a+2]
    if w==b'\x32\x3b' and op[a+4:a+6]==b'\x4e\xfb':
        disp=int.from_bytes(op[a+2:a+4],'big')&0xff
        base=a+2+disp if False else None
    if op[a:a+2]==b'\x4e\xfb' and op[a-4:a-2] in (b'\x32\x3b',b'\x30\x3b',b'\x34\x3b') :
        base=a+2+(op[a+3]-0 if op[a+3]<128 else op[a+3]-256)
        tgt=[];i=0;lim=None
        while i<64:
            v=int.from_bytes(op[base+i*2:base+i*2+2],'big')
            if v>=0x8000:
                if v==0xffff: i+=1; continue
                break
            t=base+v
            if lim is not None and base+i*2>=lim: break
            if v<i*2+2 or t&1: break
            lim=t if lim is None else min(lim,t); tgt.append(t); i+=1
        miss=[t for t in tgt if t not in funcs]
        insn=a in seen
        res.append((a,base,len(tgt),len(miss),insn,base in tab))
        if insn and base not in tab: new.update(miss)
print('tables',len(res),'in code',sum(r[4] for r in res),'unresolved in code',sum(r[4] and not r[5] for r in res),'targets new',len(new))
print([ (hex(r[0]),r[2],r[3]) for r in res if r[4] and not r[5]][:40])
open('new_roots.txt','w').write(' '.join(f'{x:x}' for x in sorted(new)))
