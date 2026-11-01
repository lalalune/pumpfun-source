#!/bin/bash
# batch.sh <varsfile> <name>...: capture variants two at a time (work1/work2), log json lines to <varsfile>.jsonl
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a29-shim-feetagpt
vf=$1; shift
names=("$@"); i=0
while [ $i -lt ${#names[@]} ]; do
  a=${names[$i]}; b=${names[$((i+1))]}
  $OUT/tools/capvar.sh $a $vf work1 >> $vf.jsonl 2>&1 &
  if [ -n "$b" ]; then $OUT/tools/capvar.sh $b $vf work2 >> $vf.jsonl 2>&1 & fi
  wait
  i=$((i+2))
done
echo DONE >> $vf.jsonl
