#!/bin/bash
# mirdump.sh NAME  (dumps PreCodegen MIR for admin_cto into $OUT/mir-NAME)
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w6r2-layout-rodata; WT=./worktrees/w6r2-layout-rodata
rm -rf $OUT/mir-$1; mkdir -p $OUT/mir-$1; export PUMP_BUILD_SLOTS=10
python3 $OUT/scripts/capture.py ${SRC:-$WT/programs/pump} $OUT/work-cap $OUT/out/cap-$1 "-Zdump-mir=PreCodegen & ${FILT:-admin_cto}" "-Zdump-mir-dir=$OUT/mir-$1" > $OUT/out/cap-$1.log 2>&1
ls $OUT/mir-$1 | grep -c after
