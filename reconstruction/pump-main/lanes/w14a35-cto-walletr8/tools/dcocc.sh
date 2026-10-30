#!/bin/bash
# dcocc.sh <m.ll>: find the do_coin vreg in the greedy MIR, print its fate and physreg occupancy at its last selectOrSplit
O=~/.cache/pumpfun-reconstruction/lanes/w14a35-cto-walletr8; d=$(dirname $1); bash $O/tools/ra.sh $1 $d/ra.log
V=$(python3 - $d/ra.log <<'PY'
import re,sys
t=open(sys.argv[1]).read(); g=t[t.index('GREEDY REGISTER ALLOCATION'):]; g=g[g.index('MACHINEINSTRS'):]
m=re.search(r'%(\d+):gpr = COPY killed \$r0\n\d+B\t  %(\d+):gpr = MOV_ri 0\n\d+B\t  %(\d+):gpr = MOV_ri 0\n\d+B\t  JNE_ri %\1:gpr, 0',g)
print('%'+m.group(2))
PY
)
L=$(grep -n "^selectOrSplit GPR:$V " $d/ra.log | tail -1 | cut -d: -f1)
echo "do_coin=$V fate: $(grep -E "^assigning $V to|^\[$V -> fi" $d/ra.log | tail -1)"
python3 $O/tools/occat.py $d/ra.log $V $((L+1))
