#!/bin/bash
# runv.sh <variant> <workN> : copy main crate, apply variant, measure, record JSON line in $OUT/results.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a07-cto-sweepthread
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools
v=$1; w=$2; SRC=${SRCDIR:-$WT/programs/pump}
mkdir -p $OUT/var/$v
rsync -a --delete --exclude target $SRC/ $OUT/var/$v/
python3 - "$OUT/var/$v/src/creator/admin_cto.rs" "$v" <<'PY' || { echo "{\"variant\":\"$v\",\"error\":\"edit\"}" >> $OUT/results.jsonl; exit 1; }
import sys,runpy
p,v=sys.argv[1],sys.argv[2]
V=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread/tools/variants.py')['V']
s=open(p).read()
for o,n in V[v]:
    c=s.count(o)
    if c!=1: print('match count',c,'for',o[:80],file=sys.stderr); sys.exit(1)
    s=s.replace(o,n)
assert s.count('\n')==open(p).read().count('\n'), 'line count changed'
open(p,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
r=$($TOOLS/measure.sh $OUT/var/$v $OUT/$w $OUT/t/$v 2>&1 | tail -1)
echo "{\"variant\":\"$v\",\"r\":$r}" >> $OUT/results.jsonl
echo "$v $r" | cut -c1-400
