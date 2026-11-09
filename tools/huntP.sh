# usage: huntP.sh N(instance 8|9)  PASSIVE run from the stage 0c state, then continuing runs from its end state (as the pkgG-era grabs came: grab at v12310 to v13487)
Y=${1:?}
cd /e/AvP/learning/lane-all
R=E:/AvP/learning/lane-all/runW2/hp${Y}_pas
rm -rf $R; PASSIVE=1 CLS=1 BOT_CHAR=1 VID=2 bash tools/diag_runH$Y.sh $R E:/AvP/learning/lane-all/runW2/state_J_schaefer.yss E:/AvP/learning/lane-all/runW2/abs_warpJ.cue E:/AvP/learning/lane-all/runW2/sat_warpJ.elf 5 170 >/dev/null 2>&1
cp yaba$Y/saves/_003.yss runW2/state_J_pas$Y.yss
for n in 1 2 3 4 5 6 7 8; do
  R=E:/AvP/learning/lane-all/runW2/hp${Y}_$n
  rm -rf $R; BOT_CHAR=1 VID=2 bash tools/diag_runH$Y.sh $R E:/AvP/learning/lane-all/runW2/state_J_pas$Y.yss E:/AvP/learning/lane-all/runW2/abs_warpJ.cue E:/AvP/learning/lane-all/runW2/sat_warpJ.elf $((Y*100+n)) 200 >/dev/null 2>&1
  if grep -aq "TABLE READ" $R/run.log; then echo "TABLE READ in hp${Y}_$n" > runW2/hp${Y}_found.txt; break; fi
done
echo D > runW2/hp${Y}.done
