"""usage: look_run.py NAME   (env GS_CUE, GS_EXE, HW_* as exact_run.py)  Boots a SAT_INPUT_SCRIPT_TICK + SAT_SCRIPT_FREEZE build in my own Ymir (scripted pad, no input from here). At each freeze (the game's tick task waits 100 vblanks
at stage ticks 500 900 1400 2000 2600 3200 3700, the vblank handler and the slave go on) it takes a screenshot when the picture has settled (70 vblanks into the wait): runs/NAME/look_<mark>.png."""
import sys, time, os, shutil
sys.path.insert(0, 'E:/AvP/learning/lane-perf-pic/ymir_pic')
import ygs
name = sys.argv[1]; cue = os.environ['GS_CUE']
out = f'{ygs.HERE}/runs/{name}'; os.makedirs(out, exist_ok=True)
y = ygs.Y(cue)
t0 = time.time(); lf = open(out + '/run.log', 'w'); mark = 0; frozen_since = None; last_tw = -1; shot_done = False
try:
    while y.pr.poll() is None and time.time() - t0 < 2400 and mark < 7:
        time.sleep(0.15)
        d = y.last()
        if not d: continue
        if y.win() and y.vb() > 100 and not getattr(y, '_lab', 0): y._lab = 1; y.label('PERF-PIC lane Ymir (look check) - ' + name)
        tw, vb = int(d['tw']), d['vb']
        if tw != last_tw: last_tw = tw; frozen_since = vb; shot_done = False
        elif d['st'] != '00' and frozen_since is not None and vb - frozen_since >= 70 and not shot_done:
            shot_done = True; mark += 1; y.shot(f'{out}/look_{mark}.png'); lf.write(f'mark {mark} tw {tw} vb {vb} {d}\n'); lf.flush()
    lf.write('done\n')
finally:
    y.kill(); time.sleep(1)
    try: shutil.copy(ygs.HERE + '/gs.log', out + '/gs.log')
    except Exception as e: print(e)
