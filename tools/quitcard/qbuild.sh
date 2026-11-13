#!/bin/bash
# usage: qbuild.sh TAG "EXTRA KERNEL_CFLAGS" [GD]   private build of the quitcard worktree (working tree, WT) into wd_TAG; iso saved as iso_TAG.iso, map/elf as map_TAG.txt / elf_TAG.elf
# recipe = fix7p5 (L12): fix7q2's recipe + BOOT_CFLAGS="-DSAT_LOAD_LZ -DSAT_LOAD_COALESCE -DSAT_BOOT_DISC_ORDER"; GD=1 builds the Wolverine-default disc (as perf-hw W builds)
TAG=$1; EXTRA=$2; GD=${3:-0}
L=/e/AvP/learning/lane-quitcard; W=$L/wd_$TAG; S=$L/src_$TAG; WT=/e/AvP/worktrees/quitcard
rm -rf $S; mkdir -p $S
(cd $WT && tar cf - --exclude=.git .) | tar xf - -C $S; REVH=$(git -C $WT rev-parse HEAD)
cd $S
export GUEST_DEFAULT=$GD REVEAL_VOICE=E:/AvP/learning/lane-wv-sounds/wav/reveal_voice_intro.bin DUEL_FILES=0 CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 CHAR_FUZZ_KEY_STAGES= WV_SOUND=E:/AvP/learning/lane-wv-sounds/assets3 WV_SKIP_KEYCHECK=1
export BOOT_CFLAGS="-DSAT_LOAD_LZ -DSAT_LOAD_COALESCE -DSAT_BOOT_DISC_ORDER"
GA=/e/AvP/learning/lane-wv-native-gfx/D12
BASE="-DSAT_TILE_ROWTRIM=2 -DSAT_WV_NATIVE_GFX -DSAT_WV_DIALOG=1 -DSAT_WV_SOUND -DSAT_WV_HEAL -DSAT_WV_FLASH=1 -DSAT_WV_FLASH_FREEZE=12 -DWV_SFX_BERSERKER=13 -DSAT_HOME_FONT_COLD -DSAT_FPS_HUD -DSAT_BUILD_REV=$(echo ${REVH:0:6} | tr a-f A-F) -DSAT_GFX_FIT=2 $EXTRA"
LOG=$L/b_$TAG.log
echo "head $REVH tag $TAG gd $GD extra $EXTRA" > $LOG; START=$(date +%s)
POSE_KEYS=0 KEEP_ROUND_FILES=1 GUEST_ASSETS=$GA \
KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=$GD -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1 $BASE" \
python saturn/rt/build.py E:/AvP/learning/lane-quitcard/wd_$TAG >> $LOG 2>&1
RC=$?
echo "rc $RC secs $(( $(date +%s) - START ))" >> $LOG
if [ $RC = 0 ]; then cp $W/sat.iso $L/iso_$TAG.iso; cp $W/sat.map $L/map_$TAG.txt; cp $W/sat.elf $L/elf_$TAG.elf; cp $W/align_gate.txt $L/align_$TAG.txt 2>/dev/null; fi
echo done >> $LOG
