# usage: runall.py PKG RUN SECONDS [leg]: verify PKG hashes, run the whole-game bot in legs on those bytes under soft-core Yaba, verify again.
# env BOT_CHAR, BOT_P2/YABA_P2, CAPT=1 (per-leg raw SCSP output in RUN/raw), LEG_SECS, YABA_SOUND.
import hashlib, os, pathlib, re, shutil, subprocess, sys, time
pkg, run, secs = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), float(sys.argv[3])
run.mkdir(parents=True, exist_ok=True)
def check(tag):
    bad = []
    for l in (pkg / 'SHA256SUMS.txt').read_text().splitlines():
        if l.startswith('#'):
            continue
        h, n = l.split('  ', 1)
        if hashlib.sha256((pkg / n).read_bytes()).hexdigest() != h:
            bad.append(n)
    print(tag, 'hash check', 'BAD ' + str(bad) if bad else 'ok', flush=True)
check('before')
cue = (pkg / 'avp_saturn.cue').read_text()
(run / 'abs.cue').write_text(re.sub(r'FILE "([^"]+)"', lambda m: 'FILE "' + str(pkg / m[1]) + '"', cue))
elf = pathlib.Path(os.environ.get('ELF', pkg.parent / 'work/sat_package.elf'))
shutil.copy(elf, run / 'sat.elf')
env = dict(os.environ, YABA_EXE=r'E:\AvP\learning\lane-emu\yaba\yabasanshiro.exe', YABA_VIDEO='2', QT_OPENGL='desktop', YABA_PAD='mcp', YABA_CUE=str(run / 'abs.cue'), YABA_ELF=str(run / 'sat.elf'))
env.setdefault('YABA_SOUND', '0')
repo = pathlib.Path(r'E:\AvP\worktrees\lane-all')
SLOT = pathlib.Path(os.environ['APPDATA']) / 'YabaSanshiro/_003.yss'
LEG = os.environ.get('LEG_SECS', '240')
leg = int(sys.argv[4]) if len(sys.argv) > 4 else 0
t0 = time.time()
(run / 'raw').mkdir(exist_ok=True)
while time.time() - t0 < secs and not (run / 'DONE').exists():
    if leg:
        env['YABA_LOAD'] = '3'
        if os.environ.get('RESUME_FROM'):   # join state kept by an earlier run
            shutil.copy(os.environ.pop('RESUME_FROM'), SLOT)
        shutil.copy(SLOT, run / f'slot_leg{leg % 3}.yss')
    else:
        env.pop('YABA_LOAD', None)
    if os.environ.get('CAPT'):
        env['AVP_SCSP_RAW'] = str(run / 'raw' / f'leg{leg:03d}.raw')
    print('LEG', leg, 'start', time.strftime('%H:%M:%S'), flush=True)
    ts = time.time()
    with open(run / 'run.log', 'a') as lf:
        rc = subprocess.run([sys.executable, str(repo / 'saturn/rt/play_yaba.py'), str(run), str(repo / 'saturn/rt/play_full_bot.py'), LEG], env=env, stdout=lf, stderr=subprocess.STDOUT).returncode
    if rc == 3:   # another lane took the emulator: this leg is void, its join state goes back
        print('leg void, another Yaba on the port', leg, flush=True)
        if leg:
            shutil.copy(run / f'slot_leg{leg % 3}.yss', SLOT)
        time.sleep(20)
        continue
    if time.time() - ts < 60:
        print('leg ended in under a minute, stopping'); break
    leg += 1
    if 'FATAL' in (run / 'rounds_proof.txt').read_text(errors='replace').split('LEG')[-1] and not (run / 'DONE').exists():
        pass
print('stopped at leg', leg, 'DONE' if (run / 'DONE').exists() else '', flush=True)
check('after')
