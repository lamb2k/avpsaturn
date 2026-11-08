# usage: warp_run.sh PKG RUN WARP SECS   (BOT_CHAR, BOT_P2/YABA_P2 from env). DIAGNOSTIC readmap leg from boot at stage word WARP, port 9640.
P=${1:?}; R=${2:?}; mkdir -p $R
python - "$P" "$R" <<'X'
import re, sys, pathlib
p, r = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
(r / 'abs.cue').write_text(re.sub(r'FILE "([^"]+)"', lambda m: 'FILE "' + str(p / m[1]) + '"', (p / 'avp_saturn.cue').read_text()))
X
cp ${ELF:?} $R/sat.elf
cd $R && WARP=${3:?} YABA_EXE='E:\AvP\learning\lane-emu\yaba\yabasanshiro.exe' YABA_VIDEO=2 QT_OPENGL=desktop YABA_PAD=mcp YABA_CUE=$R/abs.cue YABA_ELF=$R/sat.elf YABA_SOUND=0 timeout $(( ${4:?} + 90 )) python E:/AvP/worktrees/lane-all/saturn/rt/play_yaba.py $R E:/AvP/learning/lane-all/tools/diag_warp.py $4 >> $R/run.log 2>&1
