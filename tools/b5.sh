cd /e/AvP/worktrees/lane-all; P=E:/AvP/learning/lane-packs; L=E:/AvP/learning/lane-all; C=E:/AvP/learning/lane-chars; R=E:/AvP/learning/lane-rounds; F=E:/AvP/learning/lane-fit; G=E:/AvP/learning/lane-golden2/census; W=$L/workD
export ROUNDS_VARIANTS=$P/spec.json ROUNDS_JOBS=8 ROUNDS_CONST_LIVE=$L/const_live8.json ROUNDS_PAD_MODE=budget ROUNDS_FILL_MARGIN=10
python tools/rounds_config.py $C/census.json $W E:/AvP/learning/lane-audio $G,$C/cens/c1,$C/cens/c2,$C/cens/c3,$C/cens/p2 > $L/cfgD.txt 2>&1; tail -n 2 $L/cfgD.txt | cut -c1-200
python tools/rounds_rank.py $W $G,$C/cens/c1,$C/cens/c2,$C/cens/c3,$C/cens/p2 $R/w1 $R/w2 $R/w3 $R/w4 $R/k0 $R/k1 $R/k2 $R/k3 $R/wa $F/c1 $F/c2 $F/c3 | cut -c1-100 | tail -2
python tools/rounds_variants.py rank $W $P/spec.json | tail -2 | cut -c1-200
export LEARN_OUT=E:/AvP/learning/lane-ending/learn2
python tools/satint_merge.py $W | tail -1
echo B5-CONFIG-DONE
