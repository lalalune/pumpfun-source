#!/bin/bash
# run.sh <name> <genes comma-list> <slot 0|1> [base crate dir]: apply genes (tools/genes.py) to a crate copy, measure.sh, objectives -> results.jsonl
set -u
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a06-cto-sweptcoal
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a06-cto-sweptcoal
T=$WT/reconstruction/pump-main/lanes/w14a06-cto-sweptcoal/tools
N=$1; G=$2; W=$3; BASE=${4:-$WT/programs/pump}
mkdir -p $O/var $O/t
rm -rf $O/var/$N; rsync -a --exclude target $BASE/ $O/var/$N/
python3 - $O/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || { echo "{\"name\":\"$N\",\"error\":\"EDIT_FAILED\"}" | tee -a $O/results.jsonl; exit 1; }
import sys; sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a06-cto-sweptcoal/reconstruction/pump-main/lanes/w14a06-cto-sweptcoal/tools')
import genes
f,gl=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for g in [x for x in gl.split(',') if x]:
    for a,b in genes.GENES[g]:
        c=s.count(a); assert c==1,(g,c,a[:100]); s=s.replace(a,b)
assert s.count('\n')==n0,'newline count changed'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
R=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $O/var/$N $O/work$W $O/t/$N 2>&1 | tail -1)
OBJ=$(cd $T && python3 obj.py $O/t/$N/unstripped.so 2>/dev/null | tail -1)
python3 - "$N" "$G" "$R" "$OBJ" <<'PY' | tee -a $O/results.jsonl
import json,sys
n,g,r,o=sys.argv[1:5]
try: d=json.loads(r)
except Exception: print(json.dumps({'name':n,'genes':g,'error':'parse','raw':r[-300:]})); sys.exit()
c=d.get('admin_cto') or {}
try: ob=json.loads(o)
except Exception: ob={}
print(json.dumps({'name':n,'genes':g,'ok':d.get('ok'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'norm':d.get('normalized'),'raw':d.get('raw'),'losses':len(d.get('losses') or []),'raw_losses':len(d.get('raw_losses') or []),'sha':d.get('sha'),'cf':ob.get('cf'),'b42':ob.get('both42'),'b44':ob.get('both44'),'bsum':ob.get('both_sum'),'psum':ob.get('plain_sum'),'err':(d.get('error') or '')[-200:]}))
PY
rm -f $O/t/$N/candidate.so $O/t/$N/link.map
rm -rf $O/var/$N
