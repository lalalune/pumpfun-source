#!/bin/bash
# pe.sh <name> <edits.py...>: apply post-opt IR edits in order to rx/base/m.ll, wr.py + debug RA log + wtl summary
O=~/.cache/pumpfun-reconstruction/lanes/w14a82-cto-walletweight; N=$1; shift
mkdir -p $O/pe/$N
python3 - $O/rx/base/m.ll $O/pe/$N/m.ll "$@" <<'PY' || exit 1
import sys,runpy
t=open(sys.argv[1]).read()
for p in sys.argv[3:]:
  for e in runpy.run_path(p)['EDITS']:
    if callable(e): t=e(t); continue
    a,b=e; c=t.count(a); assert c==1,(c,a[:150]); t=t.replace(a,b)
open(sys.argv[2],'w').write(t)
PY
python3 $O/tools/wr.py $O/pe/$N/m.ll | sed "s#\"f\": \"[^\"]*\"#\"f\": \"$N\"#"
