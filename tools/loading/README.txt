Loading lane tools (2026-11-12). Paths inside are the lane's (E:/AvP/learning/lane-loading/...). The Ymir sources are not in this repo (GPL, baseline a9f0cdae); ymir_loading.diff is my change to them
(log-only: CD seek and sector reads, VBlank-IN, VDP1 swaps, pad changes and a frame hash, all stamped with the scheduler's master clock; the pad also read from a file).
route.py  drive Ymir by the pad file only; waits in emulated frames; steps f r t h q p m x k v z (see its docstring); lroute.sh adds the symbol addresses for RAM pokes
an.py / loads.py / summ.py / blank.py / sheet.py  analysis of trace.log; storedir.py, expsum.py, isols.py  disc and STORE.BIN tables, expected load sums; lbuild.sh, stage_l.sh  private build and Fenrir-style folder
