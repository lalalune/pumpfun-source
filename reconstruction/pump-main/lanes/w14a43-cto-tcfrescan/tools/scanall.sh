#!/bin/bash
# scanall.sh <mode> <list> <mn.ll> <outdir> [threads]
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a43-cto-tcfrescan
M=$1; mkdir -p $4
while read x; do
  n=$(echo $x | tr -d '%.'); MODE=$M XVAL=$x python3 tools/pscan.py $3 x $4/${M}_$n.jsonl ${5:-6} > $4/${M}_$n.log 2>&1
done < $2
echo done > $4/ALLDONE_$M
