#!/bin/bash
# batch.sh <specfile>: lines "name genes"; 2 parallel captures; append mm results to results.txt
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a108-cto-crlrepay; cd $OUT
run(){ s=$1; w=$2; while read n g; do [ -z "$n" ] && continue; [ -f rx/$n/res.json ] && continue; tools/cv.sh $n $g $w > log_$n.txt 2>&1; r=$(python3 tools/mm.py $n 2>/dev/null || tail -1 log_$n.txt); echo "$n $g | $r" >> ${RES:-results.txt}; rm -f ir/$n.ll; done < $s; }
awk 'NR%2==1' $1 > $1.a; awk 'NR%2==0' $1 > $1.b
run $1.a 0 & run $1.b 1 & wait
