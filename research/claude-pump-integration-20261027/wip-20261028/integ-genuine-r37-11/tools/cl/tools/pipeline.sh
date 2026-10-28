#!/bin/bash
# pipeline.sh TAG [base crate dir]: fresh base copy -> restructure.py -> changes2.py -> changes3.py -> build (TAG-a)
#                                   -> layout.py apply -> build (TAG-b) -> score. Leaves the result in work/TAG-src.
set -e
SC=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work
L=$SC/lanes/coordlib
BASE=${2:-$SC/base/current/pump}
S=$L/work/$1-src
rm -rf $S; cp -R $BASE $S
python3 $L/tools/restructure.py $S
python3 $L/tools/changes2.py $S
python3 $L/tools/changes3.py $S
[ -n "$NO_C4" ] || python3 $L/tools/changes4.py $S
$L/tools/build.sh $1-a $S > /dev/null
python3 $L/layout.py apply --src $S --cand $L/work/b$1-a/unstripped.so | grep -E "^anchors|^wrote"
$L/tools/build.sh $1-b $S
grep -o '"runtime_valid": [a-z]*' $L/work/b$1-b/fastbuild.json
