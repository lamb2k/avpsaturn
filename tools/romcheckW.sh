# usage: romcheckW.sh RUN WARPSTAGE SECS [BOT_CHAR]   warp image runW/warp636.iso on own Yaba (yaba7, 9677)
R=${1:?}; mkdir -p $R; cp E:/AvP/learning/lane-all/runW/abs_warp636.cue $R/abs.cue; cp E:/AvP/learning/lane-all/runW/sat_warp636.elf $R/sat.elf
S=C:/Users/lambd/AppData/Local/Temp/claude/e83856dea146ee0a/f3e9269b-a684-4079-b1bf-6ddbce0503a6/scratchpad
Y=E:/AvP/learning/lane-all/yaba7
cd $R && ROM_BIN=E:/AvP/learning/lane-all/runW/rom_final.bin CP=$S/cp_200000.json CPALL=$S/cp_all.json WARP=${2:?} BOT_CHAR=${4:-0} YABA_EXE='E:\AvP\learning\lane-all\yaba7\yabasanshiro.exe' YABA_INI=$Y/yabause.ini YABA_PORT=9677 YABA_VIDEO=2 QT_OPENGL=desktop YABA_PAD=mcp YABA_CUE=$R/abs.cue YABA_ELF=$R/sat.elf YABA_SOUND=0 timeout $(( ${3:?} + 90 )) python E:/AvP/worktrees/lane-all/saturn/rt/play_yaba.py $R E:/AvP/learning/lane-all/tools/diag_romcheck.py ${3:?} >> $R/run.log 2>&1
echo DONE > $R/DONE
