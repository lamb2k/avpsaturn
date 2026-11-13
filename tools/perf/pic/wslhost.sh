#!/bin/bash
# runs under WSL: wslhost.sh SCRIPT [args]  (SCRIPT relative to the perf-pic worktree). CRs stripped, root symlinked.
W=/mnt/e/AvP/worktrees/perf-pic; R=/tmp/pic/root; S=$1; shift
rm -rf /tmp/pic; mkdir -p $R/x; ln -s $W/saturn $R/saturn; ln -s $W/tests $R/tests
sed 's/\r$//' $W/$S > $R/x/run.sh
TMPDIR=/tmp/pic bash $R/x/run.sh "$@"
