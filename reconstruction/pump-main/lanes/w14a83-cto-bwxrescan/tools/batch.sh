#!/bin/bash
# batch.sh <res.jsonl> names... : 2-worker capvar queue (gen/<name>.py), appends rx + px + post-opt IR order of the 289 blocks
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a83-cto-bwxrescan
R=$1; shift
run(){ n=$1; w=$2; r=$(bash $O/tools/capvar.sh $n $O/gen/$n.py $w 2>$O/ir/err_$n.txt | tail -1)
  p=$(python3 $O/tools/px.py $O/rx/$n/m.ll 2>/dev/null | tail -1)
  q=$(python3 -c "
import sys,json; sys.path.insert(0,'$O/tools'); import bwx
try:
  m=open('$O/rx/$n/m.ll').read(); _,fn,_=bwx.split(m); _,bl,_=bwx.blocks(fn); L=[b[0] for b in bl]; print(json.dumps(L[:24]))
except Exception as e: print('null')")
  echo "{\"n\":\"$n\",\"rx\":${r:-null},\"px\":${p:-null},\"order\":${q:-null}}" >> $R; rm -rf $O/var/$n $O/ir/$n.ll; }
i=0; for n in "$@"; do run $n $((i%2)) & i=$((i+1)); if [ $((i%2)) = 0 ]; then wait; fi; done; wait
