@echo off
call C:\BuildTools\VS2022\VC\Auxiliary\Build\vcvars64.bat >nul
cd /d E:\AvP\worktrees\loading\tools\__lzbuild__
cl /nologo /O2 /LD E:\AvP\worktrees\loading\tools\loading\lzhost.c /I E:\AvP\worktrees\loading\saturn\rt /Fe:E:\AvP\worktrees\loading\tools\__lzbuild__\lzhost.dll > b.log 2>&1
