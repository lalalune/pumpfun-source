#!/bin/bash
# batch.sh <listfile>: run capvar for each name in two lanes (slots 0,1)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a115-cto-devol338st
cd $O
run(){ for n in "$@"; do bash tools/capvar.sh $n ed/$n.py $W >> $O/res.jsonl 2>>$O/err.log || echo "{\"name\":\"$n\",\"error\":\"fail\"}" >> $O/res.jsonl; done; }
L=($(cat $1)); A=(); B=()
for i in "${!L[@]}"; do if (( i%2==0 )); then A+=(${L[$i]}); else B+=(${L[$i]}); fi; done
W=0 run "${A[@]}" & W=1 run "${B[@]}" & wait
echo DONE >> $O/res.jsonl
