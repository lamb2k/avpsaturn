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
        if os.environ.get("MENU") and not getattr(s,"setmenu",0):   # e.g. MENU=up,right,right: cursor starts on START
            s.setmenu=1
            for kk in os.environ["MENU"].split(","): s.pulse(kk,.1); time.sleep(.3)
            time.sleep(.3); s.shot("duel_menu_set")
        if now-lastp>.8: lastp=now; s.pulse("start",.12)
        return
    r=s.word("sat_duel_result")
    if r and not getattr(s,"res",0): s.res=now; s.log("RESULT",r,"t",round(now-(t0 or now)),"hp",u16(0x3c0),u16(0x4c0)); time.sleep(.5); s.shot(f"duel_result{r}")
    if getattr(s,"res",0):
        if sc==1: s.log("BACK AT TITLE after",now-s.res); s.shot("duel_title"); s.stop()
        return
    if a[0x1b0]: return
    if a[0x380]==0 or a[0x480]==0 or a[1]!=2 or a[0x384]==4 or a[0x484]==4:
        if os.environ.get("SELSHOTS") and getattr(s,"seln",0)<24 and now-getattr(s,"sellast",0)>.5:
            s.sellast=now; s.seln=getattr(s,"seln",0)+1; s.shot(f"sel_{s.seln:02d}"); s.log("SEL",s.seln,"mode",a[1],"p",a[0x380],a[0x480],"pick",pick)
        if a[1]==2 and getattr(s,"menushot",0) and getattr(s,"m2",None) is None: s.m2=pick
        if getattr(s,"m2",None) is not None and pick>=s.m2+2 and not getattr(s,"selwait",0):   # after both start presses   # the select screen: it changes resolution, so wait for the picture (s36.log: about 3 s after mode 2)
            s.selwait=1
            for j in range(4): time.sleep(0.8); s.shot(f"char_select_{j}")
            for side,keys in (("",os.environ.get("P1MOVE","")),("p2",os.environ.get("P2MOVE",""))):
                for kk in keys.split(","):
                    if kk: s.pulse(side+kk,.1); time.sleep(.35)
            time.sleep(.4); s.shot("char_select_moved"); lastp=time.time()
        if now-lastp>.6:
            lastp=now; pick+=1
            s.pulse("start" if pick%2 else "p2start",.1)
            if pick%6==0: s.pulse("c",.08); s.pulse("p2c",.08)
        s.set([]); return
    if t0 is None: t0=now; s.shot("duel_begin"); s.log("CHARS d2",a[0x380+0xd2],a[0x480+0xd2],"stage",hex(u16(0x1e8)),"menu",s.word("sat_duel_opt",0,4).to_bytes(4,"big").hex() if "sat_duel_opt" in s.syms else "")
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
    if n%60==0: s.log("PCT",pc,"STOCKS",st,"rings",rg,"t",round(now-t0),"aliens",s.word("sat_alien_spawns"),hex(s.word("sat_alien_last")),"spawner",s.ram(0x1816,1)[0],"culled",s.word("sat_alien_culled"),"shots",s.word("sat_shot_hits"),"probe",s.word("sat_shot_probe"),s.word("sat_shot_probe",4,16).to_bytes(16,"big").hex(),s.word("sat_shot_probe",20,2),"pool",sum(1 for i in range(16) if s.ram(0xae80+i*0x80,4)!=bytes(4)),"t12",[s.ram(0x9580+i*0xc0+2,1).hex() for i in range(20) if s.ram(0x9580+i*0xc0,4)!=bytes(4)],"parked",s.word("sat_doors_parked"),"ee7d",s.ram(0xee7d,1)[0],"kos",s.word("sat_smash_kos"),"ctl",hex(s.word("sat_stage_ctl")),"8218",s.ram(0x8218,2).hex(),"81f3",s.ram(0x81f3,1).hex(),"stw",s.ram(0x81e8,2).hex(),"xy",u16(0x390),u16(0x394),u16(0x490),u16(0x494))
    if os.environ.get("IDLESHOTS") and n%60==30: s.shot(f"idle_{int(now-t0)}")
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
    ph=n%200   # gun phase (C is the gun, pad.c): P1 backs off for 20 steps, then faces P2 and fires for 20; P2 keeps its own moves
    p2k=[x for x in k if x.startswith("p2")]
    if ph<20: k=["left" if px<qx else "right"]+p2k
    elif ph<40:
        k=(["right" if px<qx else "left"] if ph<23 else [])+p2k
        if ph>=23 and ph%4<2: k.append("c")
    if os.environ.get("GUNLOG"):
        r=a[0x380:0x480]; s.log("GUN act",r[4:8].hex(),"8b",r[0x8b],"8c",r[0x8c],"d2",r[0xd2],"ee",hex(r[0xee]),"shots",s.word("sat_shot_hits"),"seen",s.word("sat_shot_probe"),"aimed",s.word("sat_shot_aimed"),"diag",[s.word("sat_shot_diag",i*2,2) for i in range(6)],"facing",a[0x38f],a[0x48f],"pct",s.word("sat_smash",0,2),s.word("sat_smash",2,2),"x",u16(0x390),u16(0x490))
        P=s.ram(0x8680,0xc00)
        for i in range(24):
            q=P[i*0x80:i*0x80+0x80]
            if q[0] and int.from_bytes(q[0x26:0x28],"big") in (0x8380,0x8480): s.log("SREC",hex(0x8680+i*0x80),q[:8].hex(),"x",int.from_bytes(q[0x10:0x12],"big"),"y",int.from_bytes(q[0x14:0x16],"big"),"z",int.from_bytes(q[0x18:0x1a],"big"),"f",q[0xf],"1c",q[0x1c:0x20].hex())
    sh=s.word("sat_shot_hits")
    if sh!=getattr(s,"shn",0):
        s.shn=sh; s.log("SHOT HIT",sh,"pct",s.word("sat_smash",0,2),s.word("sat_smash",2,2))
        if not getattr(s,"shotstill",0): s.shotstill=1; time.sleep(.1); s.shot("shot_hit")
    if ph>=80 and abs(qx-px)<70 and n%8>=5 and abs(qy-py)<=8: k.append("p2a")
    if os.environ.get("GUNLOG"):   # P1 walks off, turns to face P2, then fires every other step; P2 stands
        # P2 walks to 110 px on the side P1 faces (+0x0f: 0 fires toward lower x, from the shot records), then P1 fires every other step
        s.gn=getattr(s,"gn",0)+1; g=s.gn; tx=px-110 if a[0x38f]==0 else px+110
        k=["p2left"] if qx>tx+12 else ["p2right"] if qx<tx-12 else []
        if qy<py-3: k.append("p2up")
        elif qy>py+3: k.append("p2down")
        if abs(qx-tx)<=12 and g%2: k.append("c")
        if g==20 and not getattr(s,"gs",0): s.gs=1; s.shot("gun_fire")
    s.set(k)
    if now-t0>float(os.environ.get('FIGHT',300)): s.shot("duel_end"); s.stop()
