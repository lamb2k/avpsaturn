Lane perf-pic (2026-11-12) harness. Paths are the lane's (E:/AvP/learning/lane-perf-pic, own Ymir copies ymir_pic, ymir_pic2..4: the profiling Ymir of lane perf-hw plus the probes of
tools/perf/ymir/sh2_perf_pic.diff, the 'D' line per slave draw, the 'S' lines of sat_gfx_stage, HW_PCS and HW_SCULOG samplers).
pbuild.sh TAG "FLAGS" [HEAD|WT]  private build of the worktree into wd_TAG (a copy of a finished work dir, wd_tmpl), iso_TAG.iso / elf_TAG.elf / map_TAG.txt
mkcue1.sh TAG                     iso_TAG.cue          clone_ymir.sh N   own Ymir copy N (paths compiled in) so runs go in parallel
scene.sh N NAME CUE ELF DOWNS RIGHTS [MODEL]   stage select scene (RIGHTS = list entry: 0 1-1 crowd, 1 stage 1-2 boss ...) with the bot, window 1200 vblanks after 300 into the stage
wscene.sh N NAME TAG [MODEL]      Wolverine fight (GUEST_DEFAULT=1 build): arcade, character select, right, start, stage 1, bot      exact.sh N NAME CUE ELF flat|stock|model   tick-indexed RAM dumps
look.sh N NAME CUE ELF            look-check run of a SAT_SCRIPT_FREEZE build (screenshots at the freezes)   hosttest.sh / wslhost.sh   host identity scripts under WSL (CR stripped)
Analysis: tools/perf/an_runs.py (one line per run), an_pic.py, an_stage.py (phases of a draw), slave_table.py (slave work per function group), hwan.py (tools/perf/ymir).
