#!/bin/bash
# var.sh <name> <edits.py> <workslot>: copy worktree crate, apply EDITS, measure.sh into t/<name>
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a30-cto-shareauthport
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a30-cto-shareauthport
N=$1; P=$2; W=$3
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs $P <<'PY' || exit 1
import sys
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g={}; exec(open(p).read(),g)
n0=s.count('\n')
for a,b in g.get("EDITS",[]):
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N 2>/dev/null | tail -1 | python3 -c "import json,sys;d=json.loads(sys.stdin.read());a=d.get('admin_cto',{});print(json.dumps({'name':'$N','ok':d.get('ok'),'n':d.get('normalized'),'r':d.get('raw'),'losses':d.get('losses'),'raw_losses':d.get('raw_losses'),'ratio':a.get('ratio'),'slots':a.get('slots_diff'),'bytes':a.get('cand_bytes')}))"
rm -rf $OUT/var/$N
