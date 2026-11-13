import sys; sys.path.insert(0,'E:/AvP/learning/lane-loading/ymir')
import an
for run in sys.argv[1:]:
    d=an.load(f'E:/AvP/learning/lane-loading/ymir/runs/{run}/trace.log'); rn,ck=an.runs(d)
    # boot loads: groups until the first gap of > 10 s after t=20
    g=[]
    for r in rn:
        if g and ck.t(r['c0'])-ck.t(g[-1]['c1'])<2.5: g[-1]['c1']=r['c1']
        else: g.append(dict(c0=r['c0'],c1=r['c1']))
    boot_end=None
    # last boot group: the front file: the last group that ends before first pad press
    t_press=ck.t(d['pad'][1][0]) if len(d['pad'])>1 else 1e9
    last=[x for x in g if ck.t(x['c1'])<t_press][-1]
    cd_end=ck.t(last['c1'])
    # first bright run >= 125 frames after cd_end
    run_start=None; cnt=0
    for c,h,nz,eq,n in d['fr']:
        t=ck.t(c)
        if t<cd_end: continue
        if nz>=25000:
            if cnt==0: run_start=t
            cnt+=1
            if cnt>=125: break
        else: cnt=0
    print(f'{run}: loader first read {ck.t(g[1]["c0"]):.2f}s, last boot CD sector {cd_end:.2f}s, title logo on screen (bright run) from {run_start:.2f}s')
