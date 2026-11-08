cd /e/AvP/worktrees/lane-all; P=E:/AvP/learning/lane-packs; L=E:/AvP/learning/lane-all; C=E:/AvP/learning/lane-chars; R=E:/AvP/learning/lane-rounds; F=E:/AvP/learning/lane-fit; G=E:/AvP/learning/lane-golden2/census; W=$L/work
export ROUNDS_VARIANTS=$P/spec.json ROUNDS_JOBS=8 ROUNDS_CONST_PAGES=$L/const_pages.json
python tools/rounds_config.py $C/census.json $W E:/AvP/learning/lane-audio $G,$C/cens/c1,$C/cens/c2,$C/cens/c3,$C/cens/p2 > $L/cfg.txt 2>&1; tail -n 2 $L/cfg.txt | cut -c1-200
python tools/rounds_rank.py $W $G,$C/cens/c1,$C/cens/c2,$C/cens/c3,$C/cens/p2 $R/w1 $R/w2 $R/w3 $R/w4 $R/k0 $R/k1 $R/k2 $R/k3 $R/wa $F/c1 $F/c2 $F/c3 | cut -c1-100 | tail -2
python tools/rounds_variants.py rank $W $P/spec.json | tail -2 | cut -c1-200
export LEARN_OUT=E:/AvP/learning/lane-ending/learn2
python tools/satint_merge.py $W | tail -1
python saturn/package/build_package.py $W E:/AvP/learning/lane-all/pkgH > $L/pkgH.log 2>&1; grep -E 'commit|NO-GO|rror' $L/pkgH.log | cut -c1-200; tail -2 $L/pkgH.log | cut -c1-300
python - <<'X'
import json
S=json.load(open('E:/AvP/learning/lane-all/work/round_stats.json')); print({k:v['dropped_keys'] for k,v in S.items() if v['dropped_keys'] and '_m' not in k})
R=json.load(open('E:/AvP/learning/lane-all/work/rounds.json')); print({f['name']:len(f['keep_pages']) for f in R['files'][:20]})
X
echo B3-DONE
