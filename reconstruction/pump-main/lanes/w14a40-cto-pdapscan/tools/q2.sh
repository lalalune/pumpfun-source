#!/bin/bash
# q2.sh <list> <srcdir> <res>: 2-worker capvar queue (one retry on a failed build)
M=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a40-cto-pdapscan; cd $M
run(){ w=$1; shift; for n in "$@"; do r=$(bash tools/capvar.sh $n $SD/$n.py $w 2>/dev/null | tail -1); echo "$r" | grep -q ratio || r=$(bash tools/capvar.sh $n $SD/$n.py $w 2>/dev/null | tail -1); echo "$r" >> $RES; rm -rf var/$n ir/$n.ll; done; }
SD=$2; RES=$3; A=($(cat $1)); E=(); O=()
for i in "${!A[@]}"; do if (( i % 2 == 0 )); then E+=(${A[$i]}); else O+=(${A[$i]}); fi; done
run 0 "${E[@]}" & run 1 "${O[@]}" & wait; echo DONE >> $RES
