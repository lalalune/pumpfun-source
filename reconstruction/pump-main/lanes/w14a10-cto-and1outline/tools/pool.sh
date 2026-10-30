#!/bin/bash
# pool.sh names...: run trials 2 at a time on slots 0/1
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a10-cto-and1outline
a=("$@"); n=${#a[@]}
for ((i=0;i<n;i+=2)); do
  bash $O/tools/run1.sh ${a[$i]} 0 &
  if [ $((i+1)) -lt $n ]; then bash $O/tools/run1.sh ${a[$((i+1))]} 1 & fi
  wait
done
