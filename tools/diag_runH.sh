# usage: diag_runH.sh RUN STATE CUE ELF SEED SECS   Diagnostic leg from a kept state on own Yaba (yaba7, port 9647). env VID (VideoCore, default 1).
R=${1:?}; mkdir -p $R; cp ${3:?} $R/abs.cue; cp ${4:?} $R/sat.elf
Y=E:/AvP/learning/lane-all/yaba7
cp ${2:?} "$Y/saves/_003.yss"
cd $R && SEED=${5:?} WP_INTERP=1 BOT_CHAR=${BOT_CHAR:-0} YABA_EXE='E:\AvP\learning\lane-all\yaba7\yabasanshiro.exe' YABA_INI=$Y/yabause.ini YABA_PORT=9677 YABA_VIDEO=${VID:-1} QT_OPENGL=desktop YABA_PAD=mcp YABA_CUE=$R/abs.cue YABA_ELF=$R/sat.elf YABA_SOUND=0 YABA_LOAD=3 timeout $(( ${6:?} + 90 )) python E:/AvP/worktrees/lane-all/saturn/rt/play_yaba.py $R E:/AvP/learning/lane-all/tools/diag_wp2.py ${6:?} >> $R/run.log 2>&1
echo DONE > $R/DONE
