"""usage: table.py PAIRS...  each PAIR is BASE_NAME:NEW_NAME ; finds the hwprof of each in ymir_wv, ymir_wv2, ymir_wv3 and prints a markdown table: busy %, master cycles per vblank, TICK MISS PIC SKIP"""
import os, re, sys, glob
def find(name):
    for d in ('ymir_wv','ymir_wv2','ymir_wv3'):
        p=f'{d}/hwprof_{name}.txt'
        if os.path.exists(p) and os.path.getsize(p)>1000: return d,p
    return None,None
def stats(name):
    d,p=find(name)
    if not p: return None
    cyc={}; hp=None
    for l in open(p):
        t=l.split()
        if not t: continue
        if t[0]=='WINDOW': hp=(int(t[2]),int(t[4]))
        elif t[0]=='CPU': cyc[int(t[1])]=int(t[5])
    if len(cyc)<4: return None
    tot=cyc[0]+cyc[2]+cyc[3]; n=hp[1]-hp[0]
    V=[]
    for l in open(f'{d}/runs/{name}/gs.log',errors='replace'):
        if l.startswith('V '):
            x=dict(re.findall(r'(\w+)=(\S+)',l)); x['vb']=int(l.split()[1]); V.append(x)
    W=[r for r in V if hp[0]<=r['vb']<=hp[1]]; m=W[-1]['vb']-W[0]['vb']
    ticks=sum((int(b['t8'])-int(a['t8']))%256 for a,b in zip(W,W[1:]))
    df=lambda k:(int(W[-1][k])-int(W[0][k]))*60.0/m
    return dict(busy=100.0*(cyc[0]+cyc[2])/tot, cpv=(cyc[0]+cyc[2])/n, tick=ticks*60.0/m, miss=df('ovr'), pic=df('pics'), skip=df('skp'), n=m)
print('| scene | build | busy % | master kcycles / vblank | TICK | MISS | PIC | SKIP |'); print('|---|---|---|---|---|---|---|---|')
for pair in sys.argv[1:]:
    a,b=pair.split(':')
    for tag,nm in (('before',a),('after',b)):
        s=stats(nm)
        print('| %s | %s | %s |'%(nm.split('_',1)[1], tag, ('%.1f | %.0f | %.1f | %.1f | %.1f | %.1f'%(s['busy'],s['cpv']/1000,s['tick'],s['miss'],s['pic'],s['skip'])) if s else 'n/a | | | | |'))
