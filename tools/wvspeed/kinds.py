"""usage: kinds.py PROF [PROF...]: master (CPU 0 tasks + CPU 2 irq) cycle split: executing vs memory stalls by kind and region, % of master busy cycles; instruction share by PC region"""
import sys, collections
for p in sys.argv[1:]:
    K=collections.defaultdict(int); cyc=0; vb=0; pcr=collections.defaultdict(int)
    for l in open(p):
        t=l.split()
        if t[0]=='WINDOW': vb=int(t[4])-int(t[2])
        elif t[0]=='CPU' and t[1] in ('0','2'): cyc+=int(t[5])
        elif t[0]=='K' and t[1] in ('0','2'): K[(t[2],t[3])]+=int(t[7])
        elif t[0]=='P' and t[1] in ('0','2'):
            a=int(t[2],16)&0x1FFFFFFF; r='HW' if a>=0x06000000 else 'LW' if 0x200000<=a<0x300000 else 'CART' if 0x02000000<=a<0x05000000 else 'OTH'; pcr[r]+=int(t[3])
    stall=sum(K.values()); ti=sum(pcr.values())
    print('%s: master busy %.0f cyc/vb (%.1f%% field); executing %.0f%%, stalls %.0f%%'%(p.split('hwprof_')[-1][:-4],cyc/vb,100*cyc/vb/447000,100*(cyc-stall)/cyc,100*stall/cyc))
    print('   stalls by kind/region (% of busy): '+', '.join('%s %s %.1f'%(k[0],k[1],100*v/cyc) for k,v in sorted(K.items(),key=lambda kv:-kv[1])[:9]))
    print('   instructions by PC region: '+', '.join('%s %.1f%%'%(r,100*v/ti) for r,v in sorted(pcr.items(),key=lambda kv:-kv[1])))
