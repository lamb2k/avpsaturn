Profiling and cost-model Ymir (lane perf-hw, 2026-11-12). The Ymir sources are not in this repo (GPL, a checkout of the lane's baseline a9f0cdae plus the speed lane's patches).
sh2_perf_hw.diff   my changes to the speed lane's patched sh2.cpp (E:/AvP/learning/lane-perf/ymir_gs/sh2.cpp): the hardware cost model and profiler (hwblock.cpp is the same block, readable on its own),
                   the write taps that split the master into tick / vblank handler / idle, the game RAM dump at chosen ticks, HW_FLAT, per-symbol address offsets (GS_OFF, GS_OFF2, GS_OFFR).
Environment of the patched exe: HW_PROF=1 (histograms), HW_MODEL=1 (MODELLED costs; HW_HFILL 7, HW_LWLONG 14, HW_CARTBEAT 6, HW_VDP2 40, HW_WBUF 1 ...), HW_FLAT=1 (every cached or cache-through access costs 1: placement cannot change timing),
HW_GD / HW_DBG / HW_RAMB (symbol addresses, runp.sh takes them from the ELF), HW_DUMP_TICKS=n,n,... (game RAM image at the start of those ticks), hw_cmd.txt (reset / dump NAME).
hw_run.py (stage select route, bot, health held), exact_run.py (the build's own scripted pad), runp.sh, hwan.py / hwcover.py / hwtable.py / ramdiff.py (analysis), pbuild.sh (private build from the worktree).
Paths inside are the lane's (E:/AvP/learning/lane-perf-hw/...).
