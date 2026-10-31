#!/bin/bash
# bat.sh <listfile>: run names from list, two at a time (slots 0,1); results appended to $O/results.txt
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a19-cto-c1b01frame; cd $O
run(){ s=$1; shift; for n in "$@"; do r=$(t2/cv2.sh $n e/$n.py $s 2>&1 | tail -1); echo "$n $r" >> results.txt; rm -f ir/$n.ll; done; }
mapfile_a=($(cat $1)); A=(); B=(); i=0
for n in "${mapfile_a[@]}"; do if [ $((i%2)) = 0 ]; then A+=($n); else B+=($n); fi; i=$((i+1)); done
run 0 "${A[@]}" & run 1 "${B[@]}" & wait
echo DONE >> results.txt
