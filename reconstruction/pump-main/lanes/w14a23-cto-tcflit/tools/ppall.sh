#!/bin/bash
# ppall.sh <mode> <list>: pscan over TCF clones of rx/m3/mn.ll
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a23-cto-tcflit
M=$1
while read x; do
  n=$(echo $x | tr -d '%.'); MODE=$M XVAL=$x XGEP=%i363 python3 tools/pscan.py rx/m3/mn.ll x pp/${M}_$n.jsonl 4 > pp/${M}_$n.log 2>&1
done < $2
echo done > pp/ALLDONE_$M
