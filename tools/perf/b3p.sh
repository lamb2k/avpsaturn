#!/bin/bash
# 3e recipe + SAT_PERF_STAGES (measurement build) from the perf-reconcile worktree into w3p (copy of wd3e)
cd /e/AvP/worktrees/perf-reconcile
EXTRA="$1"; TAGN="$2"
DUEL_FILES=0 CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 CHAR_FUZZ_KEY_STAGES= WV_SOUND=/e/AvP/learning/lane-wv-sounds/assets3 POSE_KEYS=0 KEEP_ROUND_FILES=1 GUEST_ASSETS=/e/AvP/learning/lane-wolverine-merge/D11 \
KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1 -DSAT_TILE_ROWTRIM=2 -DSAT_WV_NATIVE_GFX -DSAT_WV_DIALOG=1 -DSAT_WV_SOUND -DSAT_WV_HEAL -DSAT_WV_FLASH=1 -DSAT_WV_FLASH_FREEZE=12 -DWV_SFX_BERSERKER=13 $EXTRA" \
cmd.exe //c "start /low /b /wait python saturn/rt/build.py E:/AvP/learning/lane-perf/$TAGN" > /e/AvP/learning/lane-perf/b_$TAGN.log 2>&1
echo rc $? >> /e/AvP/learning/lane-perf/b_$TAGN.log
