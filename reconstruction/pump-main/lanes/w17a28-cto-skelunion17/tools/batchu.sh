#!/bin/bash
# batchu.sh <out.jsonl> name=COMBO ...: capture variants two at a time (work1/work2)
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a28-cto-skelunion17
of=$1; shift
items=("$@"); i=0
while [ $i -lt ${#items[@]} ]; do
  a=${items[$i]}; b=${items[$((i+1))]}
  python3 $OUT/tools/capu.py ${a%%=*} 1 ${a#*=} >> $of 2>&1 &
  if [ -n "$b" ]; then python3 $OUT/tools/capu.py ${b%%=*} 2 ${b#*=} >> $of 2>&1 & fi
  wait
  i=$((i+2))
done
echo '{"done":1}' >> $of
