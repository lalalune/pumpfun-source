#!/bin/bash
# pe2.sh <name> <edits.py> [base m.ll]: apply post-opt IR edits, wr.py + coal
O=~/.cache/pumpfun-reconstruction/lanes/w14a35-cto-walletr8; N=$1; E=$2; B=${3:-$O/rx/base/m.ll}
mkdir -p $O/pe/$N
python3 - $B $E $O/pe/$N/m.ll <<'PY' || exit 1
import sys,runpy
t=open(sys.argv[1]).read()
for e in runpy.run_path(sys.argv[2])['EDITS']:
    if callable(e): t=e(t); continue
    a,b=e; c=t.count(a); assert c==1,(c,a[:150]); t=t.replace(a,b)
open(sys.argv[3],'w').write(t)
PY
python3 $O/tools/wr.py $O/pe/$N/m.ll | sed "s#\"f\": \"[^\"]*\"#\"f\": \"$N\"#"
python3 $O/tools/coal.py $O/pe/$N/m.ll 2>&1 | tail -1 | sed 's/.*: pay=/  pay=/'
