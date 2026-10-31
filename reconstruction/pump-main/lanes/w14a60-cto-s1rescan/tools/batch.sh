#!/bin/bash
# batch.sh <results.jsonl> name... : run capvar.sh on $OUT/e/<name>.py, 2 at a time (work0/work1), append rx results
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a60-cto-s1rescan
D=$(cd "$(dirname "$0")" && pwd)
R=$1; shift
run(){ r=$(bash $D/capvar.sh $1 $OUT/e/$1.py $2 2>/dev/null | tail -1); [ -z "$r" ] && r="{\"name\":\"$1\",\"error\":\"compile\"}"; echo "$r" >> $R; rm -f $OUT/rx/$1/m.o; }
while [ $# -gt 0 ]; do
  run $1 0 & p=$!; shift
  if [ $# -gt 0 ]; then run $1 1; shift; fi
  wait $p
done
echo DONE >> $R
