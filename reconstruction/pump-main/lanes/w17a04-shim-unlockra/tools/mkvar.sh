#!/bin/bash
# mkvar.sh <name> <edits.py>: copy the worktree crate to $OUT/var/<name> and apply EDITS (line count kept)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a04-shim-unlockra
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a04-shim-unlockra
N=$1; E=$2; SRCB=${SRCB:-$WT/programs/pump}
rm -rf $OUT/var/$N; mkdir -p $OUT/var; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$E" <<'PY' || exit 1
import sys,runpy
f,e=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for a,b in runpy.run_path(e)['EDITS']:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
echo $OUT/var/$N
