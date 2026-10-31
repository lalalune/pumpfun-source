#!/bin/bash
# batch.sh <listfile> <resfile>: run capvar.sh for each name in list (e/src/<name>.py) with 2 workers (slots 0/1)
O=~/.cache/pumpfun-reconstruction/lanes/w14a107-cto-headargswap; cd $O
L=$1; R=$2
run(){ w=$1; shift; for n in "$@"; do r=$(bash tools/capvar.sh $n e/src/$n.py $w 2>>$O/err.log | tail -1); m=$(python3 tools/wr.py rx/$n/m.ll 2>/dev/null | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print(d['M'])" 2>/dev/null); echo "$r M=$m" >> $R; rm -rf var/$n; done; }
mapfile -t N < $L 2>/dev/null || N=($(cat $L))
A=(); B=(); i=0; for n in "${N[@]}"; do if ((i%2)); then B+=($n); else A+=($n); fi; i=$((i+1)); done
run 0 "${A[@]}" & run 1 "${B[@]}" & wait
echo DONE >> $R
