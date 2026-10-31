#!/bin/bash
# run.sh <specfile>: lines "name genes(+)"; 2 parallel captures; results to res.txt (ratio, bytes, M, true-LCS --- / rfj, entry-chunk delta)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a10-cto-newentrycopy; cd $OUT
one(){ n=$1; g=$2; w=$3; [ -f rx/$n/res.json ] || bash tools/cv.sh $n $g $w > log_$n.txt 2>&1
  if [ -f rx/$n/res.json ]; then r=$(cat rx/$n/res.json); l=$(python3 tools/lcs.py $n --masks ---,rfj 2>/dev/null | awk '{print $3,$4}'); c=$(python3 tools/lcschunk.py main $n 2>/dev/null | tail -1 | cut -d' ' -f3-); m=$(python3 tools/mm.py $n | awk '{print "M",$5,"skM",$9}'); echo "$n $g | $r | $m | $l | ch $c" >> res.txt; else echo "$n $g | FAIL $(tail -c 300 log_$n.txt | tr '\n' ' ')" >> res.txt; fi; }
run(){ while read n g; do [ -z "$n" ] && continue; one $n $g $2; done < $1; }
awk 'NR%2==1' $1 > $1.a; awk 'NR%2==0' $1 > $1.b
run $1.a 0 & run $1.b 1 & wait
