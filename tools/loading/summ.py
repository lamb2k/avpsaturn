import sys; sys.path.insert(0,'E:/AvP/learning/lane-loading/ymir')
import an, subprocess
run=sys.argv[1]
d=an.load(f'E:/AvP/learning/lane-loading/ymir/runs/{run}/trace.log'); rn,ck=an.runs(d)
print('pads', [ (round(ck.t(c),2),hex(m)) for c,m in d['pad']])
sw=[ck.t(c) for c in d['swap']]
for a,b in zip(sw,sw[1:]):
    if b-a>=0.2: print(f'swap gap {a:8.2f} -> {b:8.2f}  {b-a:6.2f}')
print('frames', len(d['vb']), 'emulated s', round(ck.t(d['vb'][-1]),1))
