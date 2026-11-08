# Party duel (SAT_DUEL_MENU): both pads on the real path, both attack. Logs percent, stocks, ring-outs, the knockback hit log; stills of the HUD, a launch and a ring-out.
import time, os
def sat_v(s): return s.word('sat_dbg',0) if 0 else int(time.time()*10)%100000
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
    if sc==8:
        if not getattr(s,"menushot",0): s.menushot=1; time.sleep(.3); s.shot("duel_menu")
        if os.environ.get("ALIENS") and not getattr(s,"setal",0):
            s.setal=1
            for _ in range(3): s.pulse("down",.1); time.sleep(.3)
            for _ in range(int(os.environ["ALIENS"])): s.pulse("right",.1); time.sleep(.3)
            for _ in range(3): s.pulse("up",.1); time.sleep(.3)
        if now-lastp>.8: lastp=now; s.pulse("start",.12)
        return
    r=s.word("sat_duel_result")
    if r and not getattr(s,"res",0): s.res=now; s.log("RESULT",r,"t",round(now-(t0 or now)),"hp",u16(0x3c0),u16(0x4c0)); time.sleep(.5); s.shot(f"duel_result{r}")
    if getattr(s,"res",0):
        if sc==1: s.log("BACK AT TITLE after",now-s.res); s.shot("duel_title"); s.stop()
        return
    if a[0x1b0]: return
    if a[0x380]==0 or a[0x480]==0 or a[1]!=2 or a[0x384]==4 or a[0x484]==4:
        if now-lastp>.6:
            lastp=now; pick+=1
            if pick==2: time.sleep(1.5); s.shot("char_select")
            s.pulse("start" if pick%2 else "p2start",.1)
            if pick%6==0: s.pulse("c",.08); s.pulse("p2c",.08)
        s.set([]); return
    if t0 is None: t0=now; s.shot("duel_begin")
    pc=(s.word("sat_smash",0,2),s.word("sat_smash",2,2)); st=(s.word("sat_smash",16,1),s.word("sat_smash",17,1)); rg=s.word("sat_smash",44)
    ln=s.word("sat_smash_log")
    while getattr(s,"logn",0)<ln:
        i=getattr(s,"logn",0)&31; b=s.word("sat_smash_log",4+i*8,8).to_bytes(8,"big"); s.logn=getattr(s,"logn",0)+1
        v=int.from_bytes(b[6:8],"big",signed=True); s.log("KNOCK tick",int.from_bytes(b[0:2],"big"),"by P%d"%(b[2]+1),"dmg",b[3],"pct",int.from_bytes(b[4:6],"big"),"speed",v)
        if abs(v)>=120 and not getattr(s,"launch",0): s.launch=1; s.shot(f"smash_launch_pct{int.from_bytes(b[4:6],'big')}")
    if rg!=getattr(s,"rg",0):
        s.rg=rg; s.log("RINGOUT",rg,"stocks",st,"pct",pc,"t",round(now-t0)); time.sleep(.2)
        if rg<=2: s.shot(f"smash_ringout{rg}")
    if os.environ.get("SHOTS") and now-getattr(s,"lastshot",0)>6: s.lastshot=now; s.shot(f"p_{sat_v(s)}"); s.log("SHOT",sat_v(s),"st",a[0x384],a[0x484],"out",s.word("sat_smash",20,1),s.word("sat_smash",21,1),"cred",a[0x18c],"x",u16(0x390),u16(0x490),"b0",a[0x1b0],"mode",a[1])
    if n%60==0: s.log("PCT",pc,"STOCKS",st,"rings",rg,"t",round(now-t0),"aliens",s.word("sat_alien_spawns"),hex(s.word("sat_alien_last")),"spawner",s.ram(0x1816,1)[0],"culled",s.word("sat_alien_culled"),"shots",s.word("sat_shot_hits"),"probe",s.word("sat_shot_probe"),s.word("sat_shot_probe",4,16).to_bytes(16,"big").hex(),s.word("sat_shot_probe",20,2),"pool",sum(1 for i in range(16) if s.ram(0xae80+i*0x80,4)!=bytes(4)),"t12",[s.ram(0x9580+i*0xc0+2,1).hex() for i in range(20) if s.ram(0x9580+i*0xc0,4)!=bytes(4)],"parked",s.word("sat_doors_parked"),"ee7d",s.ram(0xee7d,1)[0],"kos",s.word("sat_smash_kos"))
    if t0 and now-t0>20 and not getattr(s,"hs",0): s.hs=1; s.shot("smash_hud")
    h=(s.word("sat_duel_stats",0),s.word("sat_duel_stats",4))
    if h!=hits:
        hits=h; shots+=1
        s.log("HIT",h,"hp",u16(0x3c0),u16(0x4c0),"state",a[0x384:0x388].hex(),a[0x484:0x488].hex())
    px,py,qx,qy=u16(0x390),u16(0x394),u16(0x490),u16(0x494)
    k=[]
    if qx<px-24: k.append("p2right")
    elif qx>px+24: k.append("p2left")
    if qy<py-3: k.append("p2up")
    elif qy>py+3: k.append("p2down")
    if px<qx-60: k.append("right")
    elif px>qx+60: k.append("left")
    if n%8<3 and abs(qx-px)<70: k.append("a")
    ph=n%200   # gun phase: P1 backs off for 50 steps while P2 holds, then P1 faces P2 and fires (C is the gun, pad.c; B is jump)
    if ph<50: k=["left" if px<qx else "right"]
    elif ph<80:
        k=["right" if px<qx else "left"] if ph<56 or abs(qx-px)>110 else []
        if ph>=56 and ph%6<2: k.append("c")
    if 50<=n%200<80 and n%3==0: s.log("T4",[s.ram(0x8680+i*0x80,4).hex()+"@"+str(int.from_bytes(s.ram(0x8690+i*0x80,2),"big"))+","+str(int.from_bytes(s.ram(0x8694+i*0x80,2),"big")) for i in range(24) if s.ram(0x8680+i*0x80,1)!=bytes(1)],"T8",[s.ram(0x9280+i*0x80,4).hex()+"@"+str(int.from_bytes(s.ram(0x9290+i*0x80,2),"big")) for i in range(6) if s.ram(0x9280+i*0x80,1)!=bytes(1)],"T12",[s.ram(0x9580+i*0xc0,4).hex()+"@"+str(int.from_bytes(s.ram(0x9590+i*0xc0,2),"big")) for i in range(20) if s.ram(0x9580+i*0xc0,1)!=bytes(1) and s.ram(0x9582+i*0xc0,1)!=b""],"pl",px,py,qx,qy,"face",s.ram(0x8380,0x80).hex()[:64],"ee7d",s.ram(0xee7d,1)[0],"shots",s.word("sat_shot_hits"),"probe",s.word("sat_shot_probe"))
    if ph>=80 and abs(qx-px)<70 and n%8>=5 and abs(qy-py)<=8: k.append("p2a")
    s.set(k)
    if now-t0>float(os.environ.get('FIGHT',300)): s.shot("duel_end"); s.stop()
