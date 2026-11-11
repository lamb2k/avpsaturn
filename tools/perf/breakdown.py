"""Stage breakdown of the heavy slave pictures (lane perf2, 2026-11-11): usage breakdown.py TAG [TAG ...]   (cwd E:/AvP/learning/lane-perf2, runs/TAG/log.json from run2.py on a SAT_PERF_STAGES build)
For each scene (A idle, W walk, F attack) the draws that took more than HEAVY ticks (default 3,500, about a field): n, and median / worst of
  stage[5]            wake to the end of the sprite build (palette, priority and the sprite commands, plot not yet started)
  [7]-[6]             scroll 2        [8]-[7] scroll 3        [9]-[8] scroll 1 (the whole call)
  [10]-[8]            scroll 1: the blank mask pass (home_maps_rows, or the incremental plan)        [11] ticks in home_row_map (the column fit, summed)        [12]-[10] the row loop
  layer_uploads       layer tiles copied in the draw        refused_layer  lookups refused in the draw
Stage values are the slave's FRT since the wake (SAT_PERF_STAGES): [10] and [12] are cleared at the start of every draw, so a draw that did not redraw scroll 1 shows 0 there."""
import json, os, statistics as S, sys
HEAVY = int(os.environ.get('HEAVY', '3500'))
def med(v): return int(S.median(v)) if v else 0
def run(tag):
    p = f"runs/{tag}/log.json"
    if not os.path.exists(p): return
    L = json.load(open(p))['log']
    for seg, lab in (('A', 'idle'), ('W', 'walk right'), ('F', 'attack')):
        R = [r for r in L if r['seg'] == seg][5:]
        ev = [(R[i - 1], r) for i, r in enumerate(R) if i and r['done'] != R[i - 1]['done']]
        draws = [(p_, r) for p_, r in ev]
        heavy = [(p_, r) for p_, r in draws if r['gfx'] > HEAVY]
        cols = {'gfx': [], 'st5': [], 'sc2': [], 'sc3': [], 'sc1': [], 'bm': [], 'fit': [], 'rows': [], 'lupl': [], 'ref': []}
        for p_, r in heavy:
            s = r['stg']
            if len(s) < 13: continue
            cols['gfx'].append(r['gfx']); cols['st5'].append(s[5]); cols['sc2'].append(s[7] - s[6]); cols['sc3'].append(s[8] - s[7]); cols['sc1'].append(s[9] - s[8])
            if s[12]: cols['bm'].append(s[10] - s[8]); cols['fit'].append(s[11]); cols['rows'].append(s[12] - s[10])
            cols['lupl'].append(r.get('lupl', 0)); cols['ref'].append(r.get('refl', 0) - p_.get('refl', 0))
        n1 = len(cols['bm'])
        print(f"| {tag} | {lab} | {len(draws)} | {len(heavy)} | {med(cols['gfx'])} / {max(cols['gfx'] or [0])} | {med(cols['st5'])} / {max(cols['st5'] or [0])} | {med(cols['sc2'])} / {max(cols['sc2'] or [0])} | {med(cols['sc3'])} / {max(cols['sc3'] or [0])} | "
              f"{med(cols['sc1'])} / {max(cols['sc1'] or [0])} | {n1}: {med(cols['bm'])} / {max(cols['bm'] or [0])} | {med(cols['fit'])} / {max(cols['fit'] or [0])} | {med(cols['rows'])} / {max(cols['rows'] or [0])} | {med(cols['lupl'])} / {max(cols['lupl'] or [0])} | {sum(cols['ref'])} |")
if __name__ == '__main__':
    print(f"| run | scene | draws | heavy (> {HEAVY}) | draw ticks med / worst | sprites [5] | scroll 2 | scroll 3 | scroll 1 | s1 draws: blank pass [10]-[8] | column fit [11] | row loop [12]-[10] | layer uploads | refused |")
    print("| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |")
    for t in sys.argv[1:]: run(t)
