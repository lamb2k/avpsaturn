# Home build: menu Start, select, stage 02, stills and counters. CHECK: a play scene must draw a background layer; the host check cannot see this. Run through play_yaba.py; writes layer_check.txt in WORK, FAIL if scroll 2 and 3 stay off or the camera never moves 10 s after the load.
import time
n=0; t=0; lastp=0; cnt=0; t0=None; done=[]
def checked(): return bool(done)
def step(v,s):
    global n,t,lastp,cnt,t0
    n+=1; now=time.time(); a=s.ram(0x8000,0x400); sc=s.word("sat_home_screen")
    if n%60==0: s.log("v",v,"scr",sc,"mode",a[1],"att",a[0x1b0],"cred",a[0x18c],"p0",a[0x380],"stage",a[0x1e9],"loads",s.word("sat_rounds",4))
    if sc==1:
        if now-lastp>.7: lastp=now; s.pulse("start",.1)
        return
    if not (a[1]==2 and a[0x380] and a[0x1e9] and a[0x1b0]==0):
        if a[0x1b0]==0 and now-lastp>.7: lastp=now; s.pulse("start",.1)
        return
    if now>t:
        t=now+3; cnt+=1
        s.log("v",v,"stage",a[0x1e9],"loads",s.word("sat_rounds",4),"layers",a[0x4a:0x4c].hex(),"cam",a[0x278:0x27a].hex(),"pool",s.ram(0xee80,1).hex(),"cred",a[0x18c])
        s.shot(f"h{cnt:02d}_{v}")
        if s.word("sat_rounds",4) and now-(t0 or now)>10 and not checked():
            ok=(a[0x4b]&0xc)!=0 and a[0x278:0x27a]!=b"\x00\x00"
            (s.work/"layer_check.txt").write_text(("PASS" if ok else "FAIL")+f" v{v} layers {a[0x4a:0x4c].hex()} cam {a[0x278:0x27a].hex()} pool {s.ram(0xee80,1).hex()}\n"); s.log("LAYER CHECK","PASS" if ok else "FAIL"); done.append(1)
        if s.word("sat_rounds",4) and t0 is None: t0=now
        if cnt>=10: s.stop()
    s.set(["right"] + (["c"] if n%6==0 else []))
