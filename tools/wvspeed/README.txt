Lane wv-speed (2026-11-13) harness. Paths are the lane's (E:/AvP/learning/lane-wv-speed, Ymir copies ymir_wv, ymir_wv2, ymir_wv3 with their paths compiled in; the Ymir sources are not in this repo, GPL: the perf-pic lane's copy plus the patches of tools/perf/ymir).
pbuild.sh TAG "FLAGS" [WT|DIR:path]   private build into wd_TAG (a copy of a finished work dir, wd_tmpl); GD=1 builds Wolverine on by default. recipe_*.txt are the flag sets.
wscene.sh NAME TAG KIND   scene run: stage:N (Wolverine, stage select entry N), pred:N (Predator Warrior), env PRE LEN BOT; worker.sh + tasks.txt run the 30 scenes of the note on three Ymir copies.
exact.sh NAME TAG flat|stock|model   tick-indexed route (test flags SAT_INPUT_SCRIPT, _TICK, SAT_BOOT_CLEAR_EQ, SAT_INPUT_SCRIPT_WV), RAM dumps for tools/perf/ramdiff.py.
busy.py table.py top.py kinds.py hooks.py symdiff.py   analysis of the hwprof dumps (master busy share, function ranks, stall kinds, guest layer cost, A/B per function).
ymir/drv.py   the route driver with the Wolverine bot (bw) and NOAUTO=1 (no timed screenshots); ymir/exact_run.py HW_RESET_VB; ymir/ygs.py reads 60 KB of gs.log.
Use a fresh backup RAM in the Ymir profile (prof_fresh of lane perf-hw, md5 08851ed5): a saved bonus-character setting overrides GUEST_DEFAULT (see the note, section 1).
