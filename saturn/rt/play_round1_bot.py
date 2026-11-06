# Closed loop: reads game RAM over MCP rarely, chooses pad keys, sends them to Yaba's own window. Proof markers from golden_r1s:
# ff81b0 attract must be 0; ffd182 section 1, 2, 3; boss = ffa3c0 type 06 in section 2; ff81f3 is a SECTION clear flag, the boss clear is f3=1 in section 2, then section 3.
import time
prev=None; lastshot=0; n=0; ko=0; cont=0; inko=False; boss=None; t0=time.time(); lastpress=0; sec2clear=None; hpmin=999
lastsave=0
def save(s,v):
    global lastsave
    lastsave=v; s.log('save',s.m.call('save_state',slot=1)[:120])
minfree={}
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
def step(v,s):
    global prev,lastshot,n,ko,cont,inko,boss,lastpress,sec2clear
    n+=1
    a=s.ram(0x8000,0x460); d=s.ram(0xa3c0,6); c=s.ram(0xd180,6)
    g=lambda o:a[o]
    mode=g(1); h=g(0x1b0); cred=g(0x18c); g9=g(9); f3=g(0x1f3); sec=c[2]
    p0=g(0x380); top=g(0x384); hp=int.from_bytes(a[0x3c0:0x3c2],'big'); x=int.from_bytes(a[0x390:0x392],'big')
    cur=(mode,h,g9,f3,p0,top,sec,d[2],d[4])
    if cur!=prev: s.log('m',mode,'att',h,'cred',cred,'g09',g9,'f3',f3,'p',p0,top,'hp',hp,'x',x,'sec',sec,'a3c0 type',d[0],d[2],hex(d[4]<<8|d[5])); prev=cur
    if v-lastshot>=600:
        lastshot=v; s.shot(f'b_{v:06d}'); stacks(s)
        if v-lastsave>=1800: save(s,v)
        s.log('hp',hp,'x',x,'cred',cred,'rate v/s',round(v/(time.time()-t0-20),1))
    if top==4 and not inko: inko=True; ko+=1; s.log('KO',ko,'att',h); s.shot(f'ko{ko}_{v}'); stacks(s)
    if top!=4: inko=False
    if sec==2 and d[2]==6 and boss is None: boss=v; s.log('BOSS present',v); s.shot(f'boss_{v}')
    if sec==2 and f3 and not h and sec2clear is None: sec2clear=v; s.log('BOSS CLEAR f3 in section 2, attract 0, ko',ko,'continues',cont); s.shot(f'clear_{v}')
    if sec==3: s.log('SECTION 3 reached, attract',h,'ko',ko,'continues',cont); s.shot(f'after_{v}'); s.stop(); return
    now=time.time()
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
    s.set(['right'])
    for k in range(8):
        s.pulse('c' if k<5 else ('a' if k<7 else 'b'),0.05); time.sleep(0.05)
def fatal(s,c,d): s.shot('fatal'); stacks(s)
def end(s): stacks(s)
