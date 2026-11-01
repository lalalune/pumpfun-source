#!/bin/bash
# capvar.sh <name> <edits.py> <slot>: copy main crate, apply edits (as run.sh), capture post-opt IR (capopt.py), frame map
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a14-shim-shimwhole
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a14-shim-shimwhole
N=$1; E=$2; W=$3; B=${4:-$WT/programs/pump}
rm -rf $OUT/var/c_$N; rsync -a --exclude target $B/ $OUT/var/c_$N/
python3 - $OUT/var/c_$N/src/creator/admin_cto.rs $OUT/var/c_$N/src/lib.rs "$E" <<'PY' || exit 1
import sys,runpy
f,lib,e=sys.argv[1],sys.argv[2],sys.argv[3]; g=runpy.run_path(e)
for path,key in ((f,'EDITS'),(lib,'LIBEDITS')):
    s=open(path).read(); n0=s.count('\n')
    for a,b in g.get(key,[]):
        c=s.count(a); assert c==1,(key,c,a[:160]); s=s.replace(a,b)
    if key=='EDITS' and 'F' in g: s=g['F'](s)
    assert s.count('\n')==n0,('line count changed',path)
    open(path,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
python3 $OUT/tools/capopt.py $OUT/var/c_$N $OUT/work$W $OUT/ir/$N > $OUT/ir/$N.log 2>&1
python3 $OUT/tools/framemap.py $OUT/ir/$N/m.ll > $OUT/ir/$N/frame.txt
rm -rf $OUT/var/c_$N $OUT/ir/$N/candidate.so $OUT/ir/$N/link.map
diff <(cut -c1-24 $OUT/ir/main7d5e/frame.txt) <(cut -c1-24 $OUT/ir/$N/frame.txt) | head -40
