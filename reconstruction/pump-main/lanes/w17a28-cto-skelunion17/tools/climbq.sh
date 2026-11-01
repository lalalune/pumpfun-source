#!/bin/bash
# climbq.sh <out.jsonl> name[:mv] ...: sequential step.py with climb
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a28-cto-skelunion17
of=$1; shift
for it in "$@"; do
  n=${it%%:*}; f=""; [ "$it" != "$n" ] && f="--mv58"
  python3 $OUT/tools/step.py $n $f 2>&1 | tail -1 >> $of
done
echo '{"done":1}' >> $of
