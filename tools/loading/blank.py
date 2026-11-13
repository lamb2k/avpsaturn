import sys; sys.path.insert(0,'E:/AvP/learning/lane-loading/ymir')
import an
run=sys.argv[1]; minlen=float(sys.argv[2]) if len(sys.argv)>2 else 0.2; t0=float(sys.argv[3]) if len(sys.argv)>3 else 30
d=an.load(f'E:/AvP/learning/lane-loading/ymir/runs/{run}/trace.log'); rn,ck=an.runs(d)
print('blank (B: over 97 pct black) / one-colour (C) frame stretches of at least %.2f s after t=%.0f:'%(minlen,t0))
for s,a,b,n in an.segments(d,ck,minlen):
    if s in 'BC' and a>t0: print(f'  {s} {a:8.2f} -> {b:8.2f}  {b-a:6.2f}s  ({n} frames)')
