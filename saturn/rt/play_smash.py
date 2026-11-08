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
                    if kk: s.pulse(side+kk,.15); time.sleep(.5)
            time.sleep(.4); s.shot("char_select_moved"); lastp=time.time()
        if now-lastp>.6:
            lastp=now; pick+=1
            s.pulse("start" if pick%2 else "p2start",.1)
            if pick%6==0: s.pulse("c",.08); s.pulse("p2c",.08)
        s.set([]); return
    if t0 is None: t0=now; s.shot("duel_begin"); s.log("CHARS d2",a[0x380+0xd2],a[0x480+0xd2],"81cc",a[0x1cc],"round",s.word("sat_rounds"),"loads",s.word("sat_rounds",4),"stage",hex(u16(0x1e8)),"menu",s.word("sat_duel_opt",0,4).to_bytes(4,"big").hex() if "sat_duel_opt" in s.syms else "")
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
    if n%60==0: s.log("PCT",pc,"STOCKS",st,"rings",rg,"t",round(now-t0),"aliens",s.word("sat_alien_spawns"),hex(s.word("sat_alien_last")),"spawner",s.ram(0x1816,1)[0],"culled",s.word("sat_alien_culled"),"shots",s.word("sat_shot_hits"),"probe",s.word("sat_shot_probe"),s.word("sat_shot_probe",4,16).to_bytes(16,"big").hex(),s.word("sat_shot_probe",20,2),"pool",(lambda P:sum(1 for i in range(16) if P[i*0x80:i*0x80+4]!=bytes(4)))(s.ram(0xae80,0x800)),"t12",(lambda P:len([i for i in range(20) if P[i*0xc0:i*0xc0+4]!=bytes(4)]))(s.ram(0x9580,0xf00)),"parked",s.word("sat_doors_parked"),"ee7d",s.ram(0xee7d,1)[0],"kos",s.word("sat_smash_kos"),"ctl",hex(s.word("sat_stage_ctl")),"gfxmiss",s.word("sat_gfx_stats",32),"81cc",a[0x1cc],"round",s.word("sat_rounds"),"refbank",s.word("sat_gfx_stats",48),"topbank",s.word("sat_gfx_stats",28,2),"8218",s.ram(0x8218,2).hex(),"81f3",s.ram(0x81f3,1).hex(),"stw",s.ram(0x81e8,2).hex(),"xy",u16(0x390),u16(0x394),u16(0x490),u16(0x494))
    if n%60==0 and "sat_gfx_census" in s.syms:   # SAT_PROF build: the keys the tile pack lacks (section<<28|key)
        mn=s.word("sat_gfx_census",32); s.log("MISSING",mn," ".join(hex(s.word("sat_gfx_census",36+4*i)) for i in range(min(mn,32))))
    if os.environ.get("GUNSCAN") and n%5==0:   # any record whose +0x26 word names a fighter
        R=s.ram(0x8600,0x7a00); hits_=[]
        for o in range(0,len(R)-0x40,0x20):
            w=int.from_bytes(R[o+0x26:o+0x28],"big")
            if w in (0x8380,0x8480) and R[o]: hits_.append("%x:%02x/%x x%d y%d z%d"%(0x8600+o,R[o],w,int.from_bytes(R[o+0x10:o+0x12],"big"),int.from_bytes(R[o+0x14:o+0x16],"big"),int.from_bytes(R[o+0x18:o+0x1a],"big")))
        if hits_: s.log("GS",len(hits_)," ".join(hits_[:10]))
    if os.environ.get("CTLDUMP") and n%30==0:   # controller pool: live records, +0..+7 and words +0x40..+0x4f
        P=s.ram(0xce80,0x800); s.log("CTL stw",s.ram(0x81e8,2).hex()," ".join("%x:%s/%s"%(0xce80+o,P[o:o+8].hex(),P[o+0x40:o+0x50].hex()) for o in range(0,0x800,0x40) if P[o]))
    if os.environ.get("GUNLOG") and a[0x486]==0x0c: s.log("GUN2 act",a[0x484:0x488].hex(),"n",s.ram(0,0) and 0,s.word("sat_shot_probe",20,2),"hits",s.word("sat_shot_hits"),"z",u16(0x398),u16(0x498),"x",u16(0x390),u16(0x490),"facing",a[0x38f],a[0x48f])
    if os.environ.get("DIFFROM") and t0 and (not hasattr(s,"rom0") or now-getattr(s,"romt",0)>15):   # program image on the cart: what changes during the fight
        img=b"".join(s.m.read(0x02400000+i,0x10000) for i in range(0,0x200000,0x10000))
        if not hasattr(s,"rom0"): s.rom0=img; s.log("ROMSNAP",len(img))
        else:
            ch=[]; i=0; a=s.rom0
            while i<len(img):
                if img[i]!=a[i]:
                    j=i
                    while j<len(img) and img[j]!=a[j]: j+=1
                    ch.append((i,j-i,img[i:min(j,i+8)].hex(),a[i:min(j,i+8)].hex())); i=j
                else: i+=1
            s.log("ROMDIFF",len(ch)," ".join("%x+%d:%s<-%s"%c for c in ch[:24]))
        s.romt=now
    if os.environ.get("IDLESHOTS") and n%60==30: s.shot(f"idle_{int(now-t0)}")
    if t0 and now-t0>20 and not getattr(s,"hs",0):
        s.hs=1; s.shot("smash_hud")
        if os.environ.get("PALDUMP"):   # sprite palette page (CPS2 palette base register ff802c), one line per bank
            reg=u16(0x2c); base=s.word("PAGE",((reg>>8)&0xff)*4)+((reg<<8)&0xffff); pal=s.m.read(base,0x400)
            for b in range(32): s.log("PAL",b,pal[b*32:b*32+32].hex())
            for j in range(4): s.log("REC1",j,s.ram(0x8380+j*0x40,0x40).hex()); s.log("REC2",j,s.ram(0x8480+j*0x40,0x40).hex())
            o=s.m.read(s.word("PAGE",0x70*4)+0x8000,0x800)   # object list: x, y, code, attr per entry; attr low 5 bits the bank
            ents=[(int.from_bytes(o[i:i+2],"big")&0x3ff,int.from_bytes(o[i+2:i+4],"big")&0x3ff,int.from_bytes(o[i+4:i+6],"big"),int.from_bytes(o[i+6:i+8],"big")) for i in range(0,0x800,8)]
            ents=ents[:next((j for j,e in enumerate(ents) if e[3]&0xff00==0xff00),len(ents))]
            import collections; s.log("OBJN",len(ents),"banks",sorted(collections.Counter(e[3]&0x1f for e in ents).items()))
            for j in range(0,len(ents),12): s.log("OBJ",j," ".join("%d,%d,%x,%x"%e for e in ents[j:j+12]))
    h=(s.word("sat_duel_stats",0),s.word("sat_duel_stats",4))
    if h!=hits:
        hits=h; shots+=1
        s.log("HIT",h,"hp",u16(0x3c0),u16(0x4c0),"state",a[0x384:0x388].hex(),a[0x484:0x488].hex())
    px,py,qx,qy=u16(0x390),u16(0x394),u16(0x490),u16(0x494)
    if os.environ.get("GUNTEST"):   # pad check: P2's C alone, then P1's C alone
        if not getattr(s,"gt0",0):
            if a[0x384]==2 and a[0x484]==2: s.gt0=now
            else: return
        el=now-s.gt0; k=["p2c"] if 3<el<4.5 else ["c"] if 8<el<9.5 else []
        if os.environ.get("GUNTEST")=="2":   # lined up: P2 to P1's depth, 80-120 to its right, facing it, then P2 fires bursts (P1 idle)
            k=[]; G=os.environ.get("GUNNER","p2")
            if el<8:
                if qy>py+1: k.append("p2down")
                elif qy<py-1: k.append("p2up")
                d=abs(qx-px); away="p2right" if qx>px else "p2left"; to="p2left" if qx>px else "p2right"
                if d>120: k.append(to)
                elif d<80: k.append(away)
            elif el<8.25: k=["p2left" if qx>px else "p2right"]
            elif el<9: k=[]
            else: k=[G+"c"] if int(el*3)%2==0 else []
            if el>20: s.log("GT END hits",s.word("sat_shot_hits"),"n",s.word("sat_shot_probe",20,2),"diag",[s.word("sat_shot_diag",i*2,2) for i in range(6)],"pct",s.word("sat_smash",0,2),s.word("sat_smash",2,2)); s.shot("guntest"); s.stop(); return
        s.set(k); s.log("GT",round(el,1),k,a[0x384:0x388].hex(),a[0x484:0x488].hex(),"xyz",px,py,u16(0x398),qx,qy,u16(0x498),"hits",s.word("sat_shot_hits"),"n",s.word("sat_shot_probe",20,2),"diag",[s.word("sat_shot_diag",i*2,2) for i in range(6)])
        if el>14 and os.environ["GUNTEST"]=="1": s.stop()
        return
    # Both close in on each other in x and meet in depth (down raises +0x14), then trade attacks in turn.
    # Every 150 steps one fighter backs off and fires its gun (C) for a while, P1 and P2 by turns; the other keeps closing in.
    k=[]; dx=qx-px; dy=qy-py
    if dx>40: k+=["right","p2left"]
    elif dx<-40: k+=["left","p2right"]
    if dy>4: k+=["down","p2down"]   # the harness's P2 up/down raise and lower +0x14 the other way round from P1 (s58, s59)
    elif dy<-4: k+=["up","p2up"]
    if abs(dx)<=60 and abs(dy)<=6:
        if n%6<2: k.append("a")
        elif 3<=n%6<5: k.append("p2a")
    GP=int(os.environ.get("GUNP","150")); ph=n%GP; gunner=(n//GP)%2
    if ph<30:
        me,them=("","p2") if gunner==0 else ("p2","")
        mx,ox=(px,qx) if gunner==0 else (qx,px)
        k=[x for x in k if (x.startswith("p2") if gunner==0 else not x.startswith("p2"))]
        k=[x for x in k if x not in ("a","p2a")]
        if ph<12: k.append(me+("left" if mx<ox else "right"))
        elif ph<14: k.append(me+("right" if mx<ox else "left"))
        elif ph%4<2: k.append(me+"c")
    if os.environ.get("GUNLOG") and ph<30 and gunner==1: s.log("P2PH",ph,"keys",k,"p2",a[0x484:0x488].hex(),"x",qx,px)
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
