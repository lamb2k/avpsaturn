#!/bin/bash
# usage: clone_ymir.sh N  -> ymir_picN (own copy of the profiling Ymir with its own paths compiled in, so runs go in parallel)
N=$1; L=/e/AvP/learning/lane-perf-pic; D=$L/ymir_pic$N
rm -rf $D; mkdir -p $D/run $D/runs
cd $L/ymir_pic; cp *.py *.cpp *.sh link.rsp build.bat $D/; cp -r prof $D/prof
cp -r run/D3Dcompiler_47.dll run/dxcompiler.dll run/dxil.dll run/shaders $D/run/
cd $D; sed -i "s#lane-perf-pic/ymir_pic#lane-perf-pic/ymir_pic$N#g" *.py *.cpp *.sh link.rsp build.bat
cmd.exe //c "E:\AvP\learning\lane-perf-pic\ymir_pic$N\build.bat" > build_ymir.log 2>&1; tail -3 build_ymir.log
cp ymir-sdl3.exe run/ymir-pic.exe; ls -la run/ymir-pic.exe
