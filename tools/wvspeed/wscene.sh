#!/bin/bash
# usage: wscene.sh NAME TAG KIND [MODEL 1|0]   lane wv-speed. KIND: crowd (stage 1, Wolverine via arcade), or stage:N (stage select entry N, Wolverine picked), pred:N (Predator Warrior, stage select entry N), predarc (Predator, arcade stage 1).
# window: 1200 vblanks after reset (about 700 into the stage), bot with health held, Wolverine bot (bw) presses his special every 300 vblanks.
NAME=$1; TAG=$2; KIND=$3; MODEL=${4:-1}; BOT=${BOT:-bw}
L=/e/AvP/learning/lane-wv-speed; D=$L/ymir_wv${YN}; cd $D
export EXE=ymir-wv.exe HW_PROF=1
[ "$MODEL" = 1 ] && export HW_MODEL=1
case $KIND in
 crowd)   DRV="w:3300 t:start:3 t:a:8 s:12 s:12 p:select t:right:0.8 t:start:5 s:30 p:stage v: x:reset $BOT:${LEN:-1200} x:dump s:4 p:end";;
 stage:*) N=${KIND#stage:}; RT=""; for i in $(seq 1 $N); do RT="$RT t:right:0.7"; done
          DRV="w:3300 t:start:3 t:down:0.6 t:down:0.6 t:down:0.6 t:a:4 t:right:1 t:start:5$RT t:start:3 r:${PRE:-700} p:stage v: x:reset $BOT:${LEN:-1200} x:dump s:4 p:end";;
 pred:*)  N=${KIND#pred:}; RT=""; for i in $(seq 1 $N); do RT="$RT t:right:0.7"; done
          DRV="w:3300 t:start:3 t:down:0.6 t:down:0.6 t:down:0.6 t:a:4 t:start:5$RT t:start:3 r:${PRE:-700} p:stage v: x:reset b:${LEN:-1200} x:dump s:4 p:end";;
 predarc) DRV="w:3300 t:start:3 t:a:8 s:12 s:12 p:select t:start:5 s:30 p:stage v: x:reset b:${LEN:-1200} x:dump s:4 p:end";;
esac
export DRV
./runp.sh $NAME ${CUE:-E:/AvP/learning/lane-wv-speed/iso_$TAG.cue} $L/elf_$TAG.elf
