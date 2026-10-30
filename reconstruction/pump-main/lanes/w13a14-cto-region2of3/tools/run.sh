#!/bin/bash
# run.sh <slot 0|1> <name>... : build variants sequentially on work<slot>
O=$HOME/.cache/pumpfun-reconstruction/lanes/w13a14-cto-region2of3
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a14-cto-region2of3
S=$1; shift
for n in "$@"; do
  V=$O/var/$n; rm -rf $V; mkdir -p $V
  rsync -a --exclude target $WT/programs/pump/ $V/
  python3 - "$O/gen/variants.py" "$V/src/creator/admin_cto.rs" "$n" <<'PY' || { echo "{\"name\":\"$n\",\"ok\":false,\"error\":\"apply\"}" >> $O/gen/results.jsonl; continue; }
import sys,runpy
V=runpy.run_path(sys.argv[1])['V']; p=sys.argv[2]; s=open(p).read()
for name in sys.argv[3].split('+'):
    for old,new in V[name]:
        assert s.count(old)==1,(name,old[:60],s.count(old)); assert old.count('\n')==new.count('\n'); s=s.replace(old,new)
open(p,'w').write(s)
PY
  r=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $V $O/work$S $O/t/$n 2>&1 | tail -1)
  echo "{\"name\":\"$n\",\"r\":$r}" >> $O/gen/results.jsonl
  rm -f $O/t/$n/candidate.so $O/t/$n/*.o 2>/dev/null
  rm -rf $V
done
