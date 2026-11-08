# usage: mkstateW.sh RUN CUE ELF OUTSTATE SECS   boot a -DSAT_WARP image on own Yaba (yaba7, 9677), warp to stage 0c, save the stage 0c section 6 state. VideoCore 2 (1 shows "no game loaded" here).
R=${1:?}; mkdir -p $R; cp ${2:?} $R/abs.cue; cp ${3:?} $R/sat.elf
Y=E:/AvP/learning/lane-all/yaba7
cd $R && OUT_STATE=${4:?} WARP=0x0c BOT_CHAR=${BOT_CHAR:-0} YABA_EXE='E:\AvP\learning\lane-all\yaba7\yabasanshiro.exe' YABA_INI=$Y/yabause.ini YABA_PORT=9677 YABA_VIDEO=2 QT_OPENGL=desktop YABA_PAD=mcp YABA_CUE=$R/abs.cue YABA_ELF=$R/sat.elf YABA_SOUND=0 timeout $(( ${5:?} + 90 )) python E:/AvP/worktrees/lane-all/saturn/rt/play_yaba.py $R E:/AvP/learning/lane-all/tools/diag_mkstate.py ${5:?} >> $R/run.log 2>&1
echo DONE > $R/DONE
