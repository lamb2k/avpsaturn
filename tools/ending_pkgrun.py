# usage: pkgrun.py PKG RUN SECONDS [SLOT]: verify PKG hashes, run the bot on those bytes under soft-core Yaba, verify again.
import hashlib,os,pathlib,re,subprocess,sys
pkg,run,secs=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
run.mkdir(parents=True,exist_ok=True)
def check(tag):
    bad=[]
    for l in (pkg/'SHA256SUMS.txt').read_text().splitlines():
        if l.startswith('#'):continue
        h,n=l.split('  ',1)
        if hashlib.sha256((pkg/n).read_bytes()).hexdigest()!=h:bad.append(n)
    print(tag,'hash check','BAD '+str(bad) if bad else 'ok',flush=True)
check('before')
cue=(pkg/'avp_saturn.cue').read_text()
cue=re.sub(r'FILE "([^"]+)"',lambda m:'FILE "'+str(pkg/m[1])+'"',cue)
(run/'abs.cue').write_text(cue)
env=dict(os.environ,YABA_EXE=r'E:\AvP\learning\lane-emu\yaba\yabasanshiro.exe',YABA_VIDEO='2',YABA_SOUND='0',QT_OPENGL='desktop',YABA_PAD='mcp',YABA_CUE=str(run/'abs.cue'),YABA_ELF=str(pkg/'sat_package.elf.keep') if (pkg/'sat_package.elf.keep').exists() else str(run/'sat.elf'))
wt=pathlib.Path(__file__).resolve().parents[1]
repo=pathlib.Path(r'E:\AvP\worktrees\lane-ending')
import shutil,time
SLOT=pathlib.Path(os.environ['APPDATA'])/'YabaSanshiro/_003.yss'
LEG=os.environ.get('LEG_SECS','300'); leg=int(sys.argv[4]) if len(sys.argv)>4 else 0; t0=time.time()
while time.time()-t0<float(secs):
    if leg:
        env['YABA_LOAD']='3'; shutil.copy(SLOT,run/f'slot_leg{leg%3}.yss')   # last three leg joins kept; a fault cannot lose the run
    else: env.pop('YABA_LOAD',None)
    ts=time.time(); print('LEG',leg,'start',time.strftime('%H:%M:%S'),flush=True)
    subprocess.run([sys.executable,str(repo/'saturn/rt/play_yaba.py'),str(run),str(repo/'saturn/rt/play_full_bot.py'),LEG],env=env)
    if time.time()-ts<60: print('leg ended in under a minute, stopping');break
    leg+=1
    if (run/'DONE').exists(): break
check('after')
