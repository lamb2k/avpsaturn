"""usage: top.py ELF ROLES N PROF [PROF...]  top symbols by (instr+penalty) cycles per vblank for the master roles (0 tasks, 2 irq)"""
import sys, collections
sys.path.insert(0,'E:/AvP/learning/lane-wv-speed/ymir_wv')
src=open('E:/AvP/learning/lane-wv-speed/ymir_wv/hwan.py').read().replace('\nmain()\n','\n'); ns={}; exec(compile(src,'hwan','exec'),ns)
sm=ns['SymMap'](ns['load_syms'](sys.argv[1])); reg=ns['region']
info={x[2]:(reg(x[0]),x[1]) for x in sm.syms}
roles=sys.argv[2].split(','); n=int(sys.argv[3]); vb=0; tot=collections.defaultdict(lambda:[0,0]); allc=0
for p in sys.argv[4:]:
    for l in open(p):
        t=l.split()
        if t[0]=='WINDOW': vb+=int(t[4])-int(t[2])
        if t[0]=='P' and t[1] in roles:
            s=sm.find(int(t[2],16)); tot[s][0]+=int(t[3]); tot[s][1]+=int(t[4]); allc+=int(t[3])+int(t[4])
print('roles',roles,'vblanks',vb,'cycles/vb %.0f (%.1f%% of a 447K field)'%(allc/vb,100*allc/vb/447000))
rows=sorted(tot.items(), key=lambda kv:-(kv[1][0]+kv[1][1]))[:n]
for k,v in rows: print('%-30s %-5s size %5d  cyc/vb %8.0f (instr %8.0f pen %8.0f) %.2f%% field'%(k,info.get(k,('?',0))[0],info.get(k,('?',0))[1],(v[0]+v[1])/vb,v[0]/vb,v[1]/vb,100*(v[0]+v[1])/vb/447000))
