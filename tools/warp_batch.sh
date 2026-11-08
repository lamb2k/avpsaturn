# DIAGNOSTIC readmap batch: each "char stage" pair from boot via SAT_WARP on pkgW, waiting for port 9640 to be free first.
L=E:/AvP/learning/lane-all; cd $L
for job in "1 0x0c" "3 0x0e" "3 0x1c" "3 0x1e" "3 0x24" "2 0x0e" "2 0x1c" "2 0x1e" "2 0x24" "p 0x0e" "p 0x1c" "p 0x1e" "p 0x24" "p 0x0c"; do
  set -- $job; R=$L/w$1_$2; rm -rf "${R:?}"
  until ! netstat -ano | grep -q ":9640 .*LISTEN"; do sleep 10; done
  if [ $1 = p ]; then BOT_CHAR=0 BOT_P2=1 YABA_P2=1 ELF=$L/sat_pkgW.elf sh tools/warp_run.sh $L/pkgW $R $2 300
  else BOT_CHAR=$1 ELF=$L/sat_pkgW.elf sh tools/warp_run.sh $L/pkgW $R $2 300; fi
  echo "$job $(grep -aE 'FATAL 0x|lost' $R/run.log | head -1 | cut -c1-120) $(python tools/readmiss.py workR $R | tail -1)"
done
echo BATCH-DONE
