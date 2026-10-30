#!/bin/bash
# capgene.sh <name> <genes comma-list> <slot>: main crate + w13a40 genes -> raw IR ir/<name>.ll -> rx (opt+llc) -> rx/<name>/m.ll
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a44-cto-clonera7fb
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a44-cto-clonera7fb
G=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a40-cto-clonera7fb/reconstruction/pump-main/lanes/w13a40-cto-clonera7fb/tools
N=$1; GL=$2; W=$3
rm -rf $O/var/$N; rsync -a --exclude target $WT/programs/pump/ $O/var/$N/
python3 - $O/var/$N/src/creator/admin_cto.rs "$GL" $G <<'PY' || exit 1
import sys; sys.path.insert(0,sys.argv[3]); import genes
f,gl=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for g in [x for x in gl.split(',') if x]:
    for a,b in genes.GENES[g]:
        c=s.count(a); assert c==1,(g,c,a[:100]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
python3 $O/tools/capraw.py $O/var/$N $O/work$W $O/ir/cap_$N > $O/ir/cap_$N.log 2>&1
[ -f $O/ir/cap_$N/raw.ll ] || { echo "{\"name\":\"$N\",\"error\":\"capture\"}"; exit 1; }
mv $O/ir/cap_$N/raw.ll $O/ir/$N.ll; rm -rf $O/ir/cap_$N $O/var/$N
cd $O && RX_OUT=$O python3 tools/rx.py $N --base ir/$N.ll | tail -1
