#!/bin/bash
# runlist.sh <res.jsonl> name1 name2 ... : run capvar for each e/<name>.py, 2 at a time (work0/work1)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a59-cto-unownedrgn
R=$1; shift; cd $OUT
run(){ W=$1; shift; for n in "$@"; do ./tools/capvar.sh $n e/$n.py $W >> $R 2>>$OUT/err.log || echo "{\"name\":\"$n\",\"error\":\"compile\"}" >> $R; rm -rf $OUT/var/$n; done; }
A=(); B=(); i=0; for n in "$@"; do if ((i%2==0)); then A+=($n); else B+=($n); fi; i=$((i+1)); done
run 0 "${A[@]}" & run 1 "${B[@]}" & wait
