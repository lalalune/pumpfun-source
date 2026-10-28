#!/bin/bash
# build.sh NN [srcdir] : snapshot srcdir (default lanes/coordlib/src) -> work/bNN/srcsnap, fastbuild it, score it vs i1.
set -e
SC=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work
L=$SC/lanes/coordlib
SRC=${2:-$L/src}
O=$L/work/b$1
rm -rf $O; mkdir -p $O
cp -R $SRC $O/srcsnap
python3 $SC/harness/fastbuild.py --src $O/srcsnap --work $L/work --out $O > $O/fastbuild.json 2>&1 || { grep -E "^(error|warning: unused)|-->|^\s+\|" $O/build.log | head -80; tail -5 $O/fastbuild.json; exit 1; }
python3 $SC/harness/score.py $O/unstripped.so --json $O/score.json --quiet | tee $O/score.out
