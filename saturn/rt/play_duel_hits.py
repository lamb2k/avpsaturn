# Duel: both pads on the real path. Two players walk together and attack; logs health and hit counts. Stills at each hit.
import time
n=0; hits=(0,0); shots=0; t0=None; pick=0; lastp=0
def step(v,s):
    global n,hits,shots,t0,pick,lastp
    n+=1
    a=s.ram(0x8000,0x800)
    u16=lambda o:int.from_bytes(a[o:o+2],"big")
    sc=s.word("sat_home_screen"); on=s.word("sat_duel_on")
    now=time.time()
    if n%40==0: s.log("scr",sc,"cur",s.word("sat_home_cursor"),"duel",on,"mode",a[1],"att",a[0x1b0],"st",hex(u16(0x1e8)),"p",a[0x380],a[0x384],a[0x480],a[0x484],"hp",u16(0x3c0),u16(0x4c0),"xy",u16(0x390),u16(0x394),u16(0x490),u16(0x494),"z",u16(0x398),u16(0x498),"cam",u16(0x278),"result",s.word("sat_duel_result"),"hits",s.word("sat_duel_stats",0),s.word("sat_duel_stats",4))
    if getattr(s,"res",0) and sc==1: s.log("BACK AT TITLE after",now-s.res); s.shot("duel_title"); s.stop(); return
    if sc==1:
        if s.word("sat_home_cursor")!=2:
            if now-lastp>.5: lastp=now; s.pulse("up",.12)
        elif now-lastp>.5: lastp=now; s.shot("home_duel"); s.pulse("start",.12)
        return
    r=s.word("sat_duel_result")
    if r and not getattr(s,"res",0): s.res=now; s.log("RESULT",r,"hp",u16(0x3c0),u16(0x4c0)); time.sleep(.5); s.shot(f"duel_result{r}")
    if getattr(s,"res",0):
        if sc==1: s.log("BACK AT TITLE after",now-s.res); s.shot("duel_title"); s.stop()
        return
    if a[0x1b0]: return
    if a[0x380]==0 or a[0x480]==0 or a[1]!=2 or a[0x384]==4 or a[0x484]==4:
        if now-lastp>.6:
            lastp=now; pick+=1
            s.pulse("start" if pick%2 else "p2start",.1)
            if pick%6==0: s.pulse("c",.08); s.pulse("p2c",.08)
        s.set([]); return
    if t0 is None: t0=now; s.shot("duel_begin")
    h=(s.word("sat_duel_stats",0),s.word("sat_duel_stats",4))
    if h!=hits:
        hits=h; shots+=1
        s.log("HIT",h,"hp",u16(0x3c0),u16(0x4c0),"state",a[0x384:0x388].hex(),a[0x484:0x488].hex())
        if shots<=8: s.shot(f"duel_hit{shots}_hp{u16(0x3c0)}_{u16(0x4c0)}")
    px,py,qx,qy=u16(0x390),u16(0x394),u16(0x490),u16(0x494)
    k=[]
    if qx<px-24: k.append("p2right")
    elif qx>px+24: k.append("p2left")
    if qy<py-3: k.append("p2up")
    elif qy>py+3: k.append("p2down")
    if n%8<3: k.append("a")
    if abs(qx-px)<70 and n%8>=5 and abs(qy-py)<=8: k.append("p2a")
    s.set(k)
    if now-t0>150: s.shot("duel_end"); s.stop()
