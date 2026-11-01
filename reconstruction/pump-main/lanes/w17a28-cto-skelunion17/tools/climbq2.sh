#!/bin/bash
# climbq2.sh <out.jsonl> <R> name[:mv] ...: sequential step.py with climb (R rounds)
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a28-cto-skelunion17
of=$1; R=$2; shift; shift
for it in "$@"; do
  n=${it%%:*}; f=""; [ "$it" != "$n" ] && f="--mv58"
  python3 $OUT/tools/step.py $n $f --R $R 2>&1 | tail -1 >> $of
done
echo '{"done":1}' >> $of
