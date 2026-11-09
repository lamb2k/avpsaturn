# usage: romcheckN.sh RUN WARPSTAGE SECS CUE ELF   env YN (yaba7 default) YP (9677), CPLIVE json (tools/const_live.py). Warp image on own Yaba, ROM view check after the stage's load.
R=${1:?}; mkdir -p $R; cp ${4:?} $R/abs.cue; cp ${5:?} $R/sat.elf
S=E:/AvP/learning/lane-all
YN=${YN:-yaba7}; Y=E:/AvP/learning/lane-all/$YN
cd $R && ROM_BIN=E:/AvP/learning/lane-all/runW/rom_final.bin CPLIVE=${CPLIVE:-} CP=$S/const636.json CPALL=$S/const_all.json WARP=${2:?} BOT_CHAR=0 YABA_EXE="E:/AvP/learning/lane-all/$YN/yabasanshiro.exe" YABA_INI=$Y/yabause.ini YABA_PORT=${YP:-9677} YABA_VIDEO=2 QT_OPENGL=desktop YABA_PAD=mcp YABA_CUE=$R/abs.cue YABA_ELF=$R/sat.elf YABA_SOUND=0 timeout $(( ${3:?} + 90 )) python E:/AvP/worktrees/lane-all/saturn/rt/play_yaba.py $R E:/AvP/learning/lane-all/tools/diag_romcheck.py ${3:?} >> $R/run.log 2>&1
echo DONE > $R/DONE
