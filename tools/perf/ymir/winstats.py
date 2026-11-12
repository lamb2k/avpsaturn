import re,sys
def stats(path,a,b):
    L=[l for l in open(path) if l.startswith('V ')]
    def g(l,k): return int(re.search(k+r'=(\d+)',l).group(1))
    rows=[(int(l.split()[1]),g(l,'t8'),g(l,'ovr'),g(l,'pics'),g(l,'skp'),g(l,'flip')) for l in L]
    w=[r for r in rows if a<=r[0]<=b]
    n=len(w)-1
    tt=sum((y[1]-x[1])%256 for x,y in zip(w,w[1:]))
    return dict(vb=n, tick=tt*60/n, miss=(w[-1][2]-w[0][2])*60/n, done=60-(w[-1][2]-w[0][2])*60/n, pic=(w[-1][3]-w[0][3])*60/n, skip=(w[-1][4]-w[0][4])*60/n)
if __name__=='__main__':
    p,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); print(p,{k:round(v,1) for k,v in stats(p,a,b).items()})
