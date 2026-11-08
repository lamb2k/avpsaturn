# usage: diag_run.sh RUN STATE SCRIPT SECS   (BOT_CHAR etc from env). Diagnostic leg from a kept state. Own instance: E:/AvP/learning/lane-all/yaba7 on port 9647.
R=${1:?}; mkdir -p $R; cp E:/AvP/learning/lane-all/run_d1/abs.cue E:/AvP/learning/lane-all/run_d1/sat.elf $R/ 2>/dev/null
Y=E:/AvP/learning/lane-all/yaba7
cp ${2:?} "$Y/saves/_003.yss"
cd $R && YABA_EXE='E:\AvP\learning\lane-all\yaba7\yabasanshiro.exe' YABA_INI=$Y/yabause.ini YABA_PORT=9647 YABA_VIDEO=2 QT_OPENGL=desktop YABA_PAD=mcp YABA_CUE=$R/abs.cue YABA_ELF=$R/sat.elf YABA_SOUND=${YABA_SOUND:-0} YABA_LOAD=3 timeout $(( ${4:?} + 90 )) python E:/AvP/worktrees/lane-all/saturn/rt/play_yaba.py $R ${3:?} $4 >> $R/run.log 2>&1
