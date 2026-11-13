"""usage: exact_run.py NAME VBLANKS   (env GS_CUE, GS_EXE, GS_OFF, GS_OFF2, HW_*; see runp.sh)  -> boots the disc and plays the build's own scripted pad (SAT_INPUT_SCRIPT) for VBLANKS vblanks, no input from here.
Own window, SW_SHOWNOACTIVATE, labelled; gs.log and the screenshots go to runs/NAME."""
import sys, time, os, shutil
sys.path.insert(0, 'E:/AvP/learning/lane-wv-speed/ymir_wv')
import ygs
name, vbs = sys.argv[1], int(sys.argv[2])
cue = os.environ['GS_CUE']
out = f'{ygs.HERE}/runs/{name}'; os.makedirs(out, exist_ok=True)
y = ygs.Y(cue)
t0 = time.time(); last = 0; lf = open(out + '/run.log', 'w')
if os.environ.get('HW_DUMP_FINAL'):
    while y.vb() < int(os.environ.get('HW_RESET_VB', min(400, vbs // 2))) and y.pr.poll() is None: time.sleep(1)
    if not os.environ.get('HW_NO_RESET'): open(ygs.HERE + '/hw_cmd.txt', 'w').write('reset x')
try:
    while y.vb() < vbs and y.pr.poll() is None and time.time() - t0 < 1500:
        time.sleep(1.0)
        if y.win() and y.vb() > 100 and not getattr(y, '_lab', 0):
            y._lab = 1; y.label('WV-SPEED lane Ymir (scripted pad) - ' + name)
        if time.time() - last > float(os.environ.get('SHOTS','20')):
            last = time.time(); y.shot(f'{out}/p{y.vb():06d}.png'); lf.write(f'{time.time()-t0:.0f}s vb={y.vb()} {y.last()}\n'); lf.flush()
    if os.environ.get('HW_DUMP_FINAL'):
        open(ygs.HERE + '/hw_cmd.txt', 'w').write('dump ' + name); time.sleep(8)
    y.shot(out + '/last.png'); lf.write('done\n')
finally:
    y.kill(); time.sleep(1)
    try: shutil.copy(ygs.HERE + '/gs.log', out + '/gs.log')
    except Exception as e: print(e)
