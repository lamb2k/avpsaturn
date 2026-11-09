cd /e/AvP/learning/lane-all
OUT=runW2/state_J_schaefer.yss
BOT_CHAR=1 bash tools/mkstateW9.sh E:/AvP/learning/lane-all/runW2/mkJ E:/AvP/learning/lane-all/runW2/abs_warpJ.cue E:/AvP/learning/lane-all/runW2/sat_warpJ.elf E:/AvP/learning/lane-all/$OUT 200 >/dev/null 2>&1
ST=E:/AvP/learning/lane-all/$OUT
for n in 1 2 3 4 5 6 7 8 9 10 11 12; do
  R=E:/AvP/learning/lane-all/runW2/grab_$n
  rm -rf $R; BOT_CHAR=1 VID=2 bash tools/diag_runH9.sh $R $ST E:/AvP/learning/lane-all/runW2/abs_warpJ.cue E:/AvP/learning/lane-all/runW2/sat_warpJ.elf $((100+n)) 200 >/dev/null 2>&1
  if grep -aq "TABLE READ" $R/run.log; then echo "TABLE READ in grab_$n" > runW2/grab_found.txt; break; fi
  cp yaba9/saves/_003.yss runW2/state_J_cont_$n.yss; ST=E:/AvP/learning/lane-all/runW2/state_J_cont_$n.yss
done
echo D > runW2/grab.done
