#!/bin/bash
# mkvar.sh <name> <varsfile> : crate copy with V[name] edits applied into $OUT/b/<name>
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a29-shim-feetagpt
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a29-shim-feetagpt
n=$1; vf=$2
rm -rf $OUT/b/$n; mkdir -p $OUT/b/$n
rsync -a --exclude target $WT/programs/pump/ $OUT/b/$n/
python3 - "$OUT/b/$n/src/creator/admin_cto.rs" "$vf" "$n" <<'PY' || exit 1
import sys,runpy
f,vf,n=sys.argv[1:4]; V=runpy.run_path(vf)['V']; t=open(f).read(); n0=t.count('\n')
for a,b in V[n]:
    c=t.count(a); assert c==1,(n,c,a[:100]); t=t.replace(a,b)
assert t.count('\n')==n0,'line count changed'
open(f,'w').write(t)
PY
echo $OUT/b/$n
