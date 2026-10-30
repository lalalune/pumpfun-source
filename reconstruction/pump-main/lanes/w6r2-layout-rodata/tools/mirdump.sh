#!/bin/bash
# mirdump.sh NAME  (dumps PreCodegen MIR for admin_cto into $OUT/mir-NAME)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w6r2-layout-rodata; WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata
rm -rf $OUT/mir-$1; mkdir -p $OUT/mir-$1; export PUMP_BUILD_SLOTS=10
python3 $OUT/scripts/capture.py ${SRC:-$WT/programs/pump} $OUT/work-cap $OUT/out/cap-$1 "-Zdump-mir=PreCodegen & ${FILT:-admin_cto}" "-Zdump-mir-dir=$OUT/mir-$1" > $OUT/out/cap-$1.log 2>&1
ls $OUT/mir-$1 | grep -c after
