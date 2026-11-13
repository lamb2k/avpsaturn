"""usage: hooks.py ELF PROF... : cycles per vblank (instr + stall penalty, master tasks + irq) of Wolverine's and the guest layer's functions"""
import sys, collections, re
sys.path.insert(0,'E:/AvP/learning/lane-wv-speed/ymir_wv')
src=open('E:/AvP/learning/lane-wv-speed/ymir_wv/hwan.py').read().replace('\nmain()\n','\n'); ns={}; exec(compile(src,'hwan','exec'),ns)
sm=ns['SymMap'](ns['load_syms'](sys.argv[1])); reg=ns['region']; info={x[2]:(reg(x[0]),x[1]) for x in sm.syms}
vb=0; tot=collections.defaultdict(lambda:[0,0])
for p in sys.argv[2:]:
    for l in open(p):
        t=l.split()
        if t[0]=='WINDOW': vb+=int(t[4])-int(t[2])
        if t[0]=='P' and t[1] in ('0','2'):
            s=sm.find(int(t[2],16)); tot[s][0]+=int(t[3]); tot[s][1]+=int(t[4])
pat=re.compile(r'wv_|wolverine|guest|sat_wv|_names$|_is_w|_put32b|_wv|_ld32|_copy8')
rows=[(k,v) for k,v in tot.items() if pat.search(k)]
rows.sort(key=lambda kv:-(kv[1][0]+kv[1][1]))
S=0
for k,v in rows:
    c=(v[0]+v[1])/vb; S+=c
    print('%-32s %-5s size %5d cyc/vb %7.0f (instr %6.0f pen %6.0f)'%(k,info.get(k,('?',0))[0],info.get(k,('?',0))[1],c,v[0]/vb,v[1]/vb))
print('TOTAL guest+wv cycles/vb %.0f = %.2f%% of a 447K field'%(S,100*S/447000), 'vb',vb)
