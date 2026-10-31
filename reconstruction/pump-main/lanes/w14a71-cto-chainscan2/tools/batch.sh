#!/bin/bash
# batch.sh name... : run capvar for e/<name>.py, 2 at a time (work0/work1); print res + error order
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a71-cto-chainscan2
cd $OUT
run(){ r=$(bash tools/capvar.sh $1 e/$1.py $2 2>&1 | tail -1); o=$( [ -f rx/$1/fn.bin ] && python3 tools/eord.py rx/$1/fn.bin); echo "$r | $o"; rm -rf var/$1; }
args=("$@"); n=${#args[@]}
for ((k=0;k<n;k+=2)); do
  run ${args[k]} 0 & 
  if [ $((k+1)) -lt $n ]; then run ${args[k+1]} 1 & fi
  wait
done
