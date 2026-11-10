"""Lane wv-native3 11-09: Round 1 run of native Wolverine under Yaba (own copy, own port; keys by PostMessage to that window only). Derived from the gate lane's r2bot.py (E:/AvP/learning/lane-wolverine-gate).
It navigates from the title (coin, start, select), fights the way r2bot does (walk to the nearest enemy, attack taps, jumps, the boss at section 2) and, every BZ_EVERY vblanks, plays the Berserker motion (down, down+forward,
forward, then attack). Assists are off unless asked for: BOT_INVULN=1 tops health up, BOT_BOSSBOOST=1 sets the boss to 20 hp, BOT_BOSSWARP=1 moves him next to the boss, BOT_BOSSKILL=1 kills it after BOT_KILLAFTER
vblanks. None set = an unassisted Round 1 (continues with coin + start are the game's own). Window title: PROOF_TITLE. usage: python saturn/rt/play_yaba.py WORK tools/wolverine/r1run.py SECONDS
env: REC_OUT (prefix of throw clip dirs), SEC3_RUN (vblanks to run into section 3, default 600), BZ_EVERY (default 420, 0 = never), BOT_WATCH_PORT."""
# Closed loop: reads game RAM over MCP rarely, chooses pad keys, sends them to Yaba's own window. Proof markers from golden_r1s:
# ff81b0 attract must be 0; ffd182 section 1, 2, 3; boss = ffa3c0 type 06 in section 2; ff81f3 is a SECTION clear flag, the boss clear is f3=1 in section 2, then section 3.
import threading, time
prev=None; lastshot=0; n=0; ko=0; cont=0; inko=False; boss=None; t0=time.time(); lastpress=0; sec2clear=None; hpmin=999
lastsave=0
def save(s,v):
    global lastsave
    lastsave=v; s.log('save',s.m.call('save_state',slot=1)[:120])
minfree={}
import os, json
INVULN=os.environ.get('BOT_INVULN')=='1'
BOOST=os.environ.get('BOT_BOSSBOOST')=='1'
WARP=os.environ.get('BOT_BOSSWARP')=='1'
lastwarp=[-9999]
cnt={'hit':0,'throw':0,'getup':0,'ko':0,'refill':0,'hp_up':0,'held':0}
firsts=[]
clips=[0]
lasthp=[None]; lastheld=[0]; lastcat=[None]
def cat_of(a):
    st=(a[0x384],a[0x385],a[0x386])
    if st[0]==2 and st[1]==2: return 'hit'
    if st[0]==2 and st[1]==4: return 'throw'
    if st[0]==2 and st[1]==8: return 'getup'
    if st[0]==4: return 'ko'
    return None
def capture_throw(s,v):
    # paused, frame by frame, until the 0204xx state has been gone for 6 frames (max 120 frames); rows carry state and the guest clock
    m=s.m; tag='throw%d'%clips[0]; clips[0]+=1
    out=os.environ['REC_OUT']+'_'+tag; os.makedirs(out,exist_ok=True)
    tr=open(os.environ['REC_OUT']+'_'+tag+'.jsonl','w')
    m.call('pause'); gone=0
    for f in range(120):
        a=s.ram(0x8380,0x50)
        cur=0; wall=0; sn=int.from_bytes(a[0x1c:0x20],'big')   # native build: no clock statics, the frame record pointer says where the animation is
        st=a[4:7].hex()
        tr.write(json.dumps(dict(f=f,st=st,cur=cur,wall=wall,step=sn,hp=int.from_bytes(a[0x40:0x42],'big'),x=int.from_bytes(a[0x10:0x12],'big'),z=int.from_bytes(a[0x18:0x1a],'big'),face=a[0x0f]&1))+chr(10))
        m.call('framebuffer_burst',directory=out,frames=1,prefix='f')
        gone = gone+1 if not (st[:4]=='0204') else 0
        if gone>=6: break
    tr.close(); m.call('resume'); s.log('THROW clip',tag,'frames',f+1)

def stacks(s):
    sz=s.syms.get('sat_task_stack_size') or int(__import__('os').environ.get('TASK_STACK','2048'))
    for i in range(16):
        b=s.m.read(s.syms['task_stacks']+i*sz,sz); n=0
        while n<sz and b[n:n+4]==bytes([0xa5]*4): n+=4
        minfree[i]=min(minfree.get(i,sz),n)
    s.log('stack min free bytes per task',minfree)
def keylog(s):
    import pathlib
    b=b''.join(s.m.read(0x25A70000+a,0x4000) for a in range(0,0x10000,0x4000))
    pathlib.Path('keylog.bin').write_bytes(b)
def watch(s):
    # The flag can be set for less time than one step of the main loop takes, so a second MCP session polls only the proof markers. One read holds attract and flag; section is read right after.
    global sec2clear
    from capture_frontend_cram import Mcp
    m=Mcp('http://127.0.0.1:%s/mcp' % os.environ.get('BOT_WATCH_PORT','9718')); m.initialize()
    while not s.done:
        try:
            a=m.read(s.syms['RAMB']+0x81b0,0x44); sec=m.read(s.syms['RAMB']+0xd182,1)[0]
            v=int.from_bytes(m.read(s.syms['sat_dbg']+8,4),'big')
        except Exception as e:
            s.log('watch error',e); time.sleep(0.5); continue
        if a[0x43] and sec==2 and not a[0] and sec2clear is None:
            sec2clear=v; s.log('BOSS CLEAR f3 set in section 2, attract 0, watcher, vblank',v,'ko',ko,'continues',cont)
        time.sleep(0.005)
started=False
shotclear=[0]
boss_t0=[None]
KILL=os.environ.get('BOT_BOSSKILL')=='1'
KILLAFTER=int(os.environ.get('BOT_KILLAFTER','900'))
bgone=[0]
boss_hp=[None]
sec3=[None,0]
bz_seq=[None,0,0.0]
BZ_EVERY=int(os.environ.get('BZ_EVERY','420'))
titled=[False]
def r1step(v,s):
    global prev,lastshot,n,ko,cont,inko,boss,lastpress,started,sec2clear
    if not titled[0]:
        titled[0]=True
        try:
            import ctypes; ctypes.windll.user32.SetWindowTextW(ctypes.c_void_p(s.hwnd), os.environ.get('PROOF_TITLE','AvP NATIVE: round1 [port 9718]'))
        except Exception as e: s.log('retitle failed',e)
    if not started:
        started=True
        if os.environ.get('BOT_WATCH')=='1': threading.Thread(target=watch,args=(s,),daemon=True).start()
    n+=1
    a=s.ram(0x8000,0x460); d=s.ram(0xa3c0,6); c=s.ram(0xd180,6)
    g=lambda o:a[o]
    mode=g(1); h=g(0x1b0); cred=g(0x18c); g9=g(9); f3=g(0x1f3); sec=c[2]
    p0=g(0x380); top=g(0x384); hp=int.from_bytes(a[0x3c0:0x3c2],'big'); x=int.from_bytes(a[0x390:0x392],'big')
    ct=cat_of(a)
    if ct!=lastcat[0]:
        if ct: cnt[ct]+=1; firsts.append((ct,v)) if len(firsts)<60 else 0; s.log('STATE',ct,'#',cnt[ct],'st',a[0x384:0x387].hex(),'hp',hp,'x',x)
        lastcat[0]=ct
        if ct=='throw' and clips[0]<int(os.environ.get('THROW_CLIPS','3')): capture_throw(s,v)
    if lasthp[0] is not None and 0<hp<=101 and hp>=lasthp[0]+5: cnt['hp_up']+=1; s.log('PICKUP? hp up',lasthp[0],'->',hp,'v',v)
    if 0<hp<=101: lasthp[0]=hp
    held=a[0x3da]<<8|a[0x3db]
    if held!=lastheld[0]:
        if held: cnt['held']+=1; s.log('HELD item link',hex(held),'kind',hex(a[0x417]))
        lastheld[0]=held
    if INVULN and 0<hp<70 and top!=4:
        s.m.call('memory_write',address=hex(s.syms['RAMB']+0x83c0),bytes='0065'); cnt['refill']+=1; lasthp[0]=101
    cur=(mode,h,g9,f3,p0,top,sec,d[2],d[4])
    if cur!=prev: s.log('m',mode,'att',h,'cred',cred,'g09',g9,'f3',f3,'p',p0,top,'hp',hp,'x',x,'sec',sec,'a3c0 type',d[0],d[2],hex(d[4]<<8|d[5])); prev=cur
    if v-lastshot>=600:
        lastshot=v; s.shot(f'b_{v:06d}'); stacks(s)
        if v-lastsave>=1800: save(s,v)
        s.log('hp',hp,'x',x,'cred',cred,'rate v/s',round(v/(time.time()-t0-20),1))
    if top==4 and not inko: inko=True; ko+=1; s.log('KO',ko,'att',h); s.shot(f'ko{ko}_{v}'); stacks(s)
    if top!=4: inko=False
    if boss is not None and sec==2 and not (d[0]==1 and d[2]==6) and not bgone[0]: bgone[0]=v; s.log('BOSS GONE (a3c0 inactive) vblank',v,'f3',f3)
    if f3 and sec==2 and not h and sec2clear is None: sec2clear=v; s.log('BOSS CLEAR f3 seen in section 2, vblank',v)
    if sec==2 and d[2]==6 and boss is None: boss=v; s.log('BOSS present',v); s.shot(f'boss_{v}')
    if sec2clear is not None and not shotclear[0]: shotclear[0]=1; s.shot(f'clear_{sec2clear}')
    if sec==3:
        if sec3[0] is None: sec3[0]=v; s.log('SECTION 3 reached, attract',h,'ko',ko,'continues',cont,'counts',cnt); s.shot(f'after_{v}')
        if v-sec3[0]>=int(os.environ.get('SEC3_RUN','600')): s.shot(f'after_end_{v}'); s.log('SECTION 3 run done, counts',cnt,'x',x,'hp',hp); s.stop(); return
        if (v-sec3[0])//600!=sec3[1]: sec3[1]=(v-sec3[0])//600; s.shot(f'after_{v}')
    now=time.time()
    sc_=s.word('sat_home_screen') if 'sat_home_screen' in s.syms else 0   # the home menu of this build (title, pause): Start
    if sc_ in (1,3):
        s.set([])
        if now-lastpress>0.8:
            lastpress=now; s.pulse('start',0.1)
        return
    sel_=(mode==2 and not a[0x380] and not a[0x1e8] and not a[0x1e9] and h==0)   # the character select: Wolverine's slot is cursor 2 (as native_soak.py)
    if sel_:
        s.set([])
        if now-lastpress>0.6:
            lastpress=now
            s.pulse('right' if a[0x1cc]!=2 else 'start',0.08)
        return
    if h and sc_==0:   # the attract before the home menu is up: Start here would restart the game (home.c), so wait for the menu
        s.set([]); return
    if h or mode==4 or mode==0:
        s.set([])
        if now-lastpress>0.8:
            lastpress=now
            s.pulse('x' if cred==0 else 'start',0.08)
        return
    if p0==0 or top==4:
        s.set([])
        if now-lastpress>0.7:
            lastpress=now
            if cred==0: s.pulse('x',0.08); s.log('coin')
            elif n%2: s.pulse('start',0.08); cont+=1; s.log('start',cont)
            else: s.pulse('c',0.08)
        return
    bb=s.ram(0xa3c0,0x44)
    bhp=int.from_bytes(bb[0x40:0x42],'big')
    if bb[0]==1 and bb[2]==6 and sec==2 and 0<=bhp<=400:
        bx=int.from_bytes(bb[0x10:0x12],'big'); bz=int.from_bytes(bb[0x18:0x1a],'big')
        if boss_t0[0] is None: boss_t0[0]=v
        if v-boss_t0[0]>=KILLAFTER and bhp>0 and KILL:
            s.m.call('memory_write',address=hex(s.syms['RAMB']+0xa400),bytes='0000'); s.m.call('memory_write',address=hex(s.syms['RAMB']+0xa3c4),bytes='040000')
            s.log('BOSS KILL ASSIST: hp 0 and dying state poked, boss engaged for',v-boss_t0[0],'vblanks'); cnt['kill_assist']=1; bhp=0; boss_t0[0]=v+100000
        if v%200<8: s.log('boss st',bb[4:7].hex(),'hp',bhp,'me',a[0x384:0x387].hex())
        if BOOST and bhp>20:
            s.m.call('memory_write',address=hex(s.syms['RAMB']+0xa400),bytes='0014'); cnt['boost']=cnt.get('boost',0)+1; bhp=20
        if boss_hp[0]!=bhp: boss_hp[0]=bhp; s.log('BOSS hp',bhp,'x',bx,'z',bz,'me',x,int.from_bytes(a[0x398:0x39a],'big'))
        pz=int.from_bytes(a[0x398:0x39a],'big'); keys=[]
        if WARP and abs(bx-x)>130 and v-lastwarp[0]>120:
            lastwarp[0]=v; nx=bx+70 if x>bx else bx-70
            s.m.call('memory_write',address=hex(s.syms['RAMB']+0x8390),bytes='%04x'%nx); cnt['warp']=cnt.get('warp',0)+1
            s.log('WARP player x',x,'->',nx,'boss x',bx); x=nx
        dx=bx-x; dz=bz-pz
        if abs(dx)>85: keys.append('right' if dx>0 else 'left')
        elif abs(dx)<35: keys.append('left' if dx>0 else 'right')
        else:
            # close: a short step toward him sets the facing, then attack
            if (dx>0)!=bool(a[0x38f]&1): keys.append('right' if dx>0 else 'left')
        if dz<-9: keys.append('up')
        elif dz>9: keys.append('down')
        s.set(keys)
        if abs(dx)<=110 and abs(dz)<=16:
            for k in range(3): s.pulse('a',0.05); time.sleep(0.06)
        else: time.sleep(0.1)
        return
    if BZ_EVERY and v-bz_seq[1]>=BZ_EVERY and not h:
        bz_seq[1]=v; fw='right' if (a[0x38f]&1) else 'left'
        for keys in (['down'],['down',fw],[fw],[fw,'a'],[]):
            s.set(keys); time.sleep(0.09)
        cnt['bz']=cnt.get('bz',0)+1; s.log('BERSERKER motion #',cnt['bz'],'vblank',v,'hp',hp)
        return
    s.set(['right'])
    for k in range(8):
        s.pulse('a' if k<6 else 'b',0.05); time.sleep(0.05)
step=r1step
def fatal(s,c,d): s.shot('fatal'); stacks(s)
def end(s): stacks(s); s.log('END counts',cnt,'ko',ko,'boss',boss,'clear',sec2clear,'sec3',sec3[0],'firsts',firsts[:40])
