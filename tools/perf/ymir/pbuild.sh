#!/bin/bash
# usage: pbuild.sh TAG "EXTRA KERNEL_CFLAGS" [REV]   private build of the perf-hw worktree (or git REV) into wd; iso saved as iso_TAG.iso, map/elf as map_TAG.txt / elf_TAG.elf
# recipe = fix7n4 (hwboot chain6 G7N13): GUEST_DEFAULT=0, KEXTRA -DSAT_GFX_FIT=2
TAG=$1; EXTRA=$2; REV=${3:-HEAD}
L=/e/AvP/learning/lane-perf-hw; W=$L/wd; S=$L/src_$TAG
rm -rf $S; mkdir -p $S
if [ "$REV" = "WT" ]; then (cd /e/AvP/worktrees/perf-hw && tar cf - --exclude=.git .) | tar xf - -C $S; REVH=$(git -C /e/AvP/worktrees/perf-hw rev-parse HEAD)
else git -C /e/AvP/worktrees/perf-hw archive $REV | tar -x -C $S; REVH=$(git -C /e/AvP/worktrees/perf-hw rev-parse $REV); fi
cd $S
export GUEST_DEFAULT=0 REVEAL_VOICE=E:/AvP/learning/lane-wv-sounds/wav/reveal_voice_intro.bin DUEL_FILES=0 CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 CHAR_FUZZ_KEY_STAGES= WV_SOUND=E:/AvP/learning/lane-wv-sounds/assets3 WV_SKIP_KEYCHECK=1
GA=/e/AvP/learning/lane-wv-native-gfx/D12
BASE="-DSAT_TILE_ROWTRIM=2 -DSAT_WV_NATIVE_GFX -DSAT_WV_DIALOG=1 -DSAT_WV_SOUND -DSAT_WV_HEAL -DSAT_WV_FLASH=1 -DSAT_WV_FLASH_FREEZE=12 -DWV_SFX_BERSERKER=13 -DSAT_HOME_FONT_COLD -DSAT_FPS_HUD -DSAT_BUILD_REV=$(echo ${REVH:0:6} | tr a-f A-F) -DSAT_GFX_FIT=2 $EXTRA"
LOG=$L/b_$TAG.log
echo "head $REVH tag $TAG extra $EXTRA" > $LOG; START=$(date +%s)
POSE_KEYS=0 KEEP_ROUND_FILES=1 GUEST_ASSETS=$GA \
KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=0 -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1 $BASE" \
python saturn/rt/build.py E:/AvP/learning/lane-perf-hw/wd >> $LOG 2>&1
RC=$?
echo "rc $RC secs $(( $(date +%s) - START ))" >> $LOG
if [ $RC = 0 ]; then cp $W/sat.iso $L/iso_$TAG.iso; cp $W/sat.map $L/map_$TAG.txt; cp $W/sat.elf $L/elf_$TAG.elf; cp $W/align_gate.txt $L/align_$TAG.txt 2>/dev/null; fi
echo done >> $LOG
