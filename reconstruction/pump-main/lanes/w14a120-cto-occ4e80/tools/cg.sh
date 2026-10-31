#!/bin/bash
# cg.sh <slot> <name> <spec>: spec = gene names / @localedit joined by '+'; capture + rx; append result to results.jsonl
O=~/.cache/pumpfun-reconstruction/lanes/w14a120-cto-occ4e80
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a120-cto-occ4e80
W=$1; N=$2; SP=$3
grep -q "\"name\": \"$N\"" $O/results.jsonl 2>/dev/null && { grep "\"name\": \"$N\"" $O/results.jsonl | tail -1; exit 0; }
rm -rf $O/var/$N; rsync -a --exclude target $WT/programs/pump/ $O/var/$N/
python3 - $O/var/$N/src/creator/admin_cto.rs "$SP" <<'PY' || { echo "{\"name\":\"$N\",\"spec\":\"$SP\",\"error\":\"apply\"}" | tee -a $O/results.jsonl; rm -rf $O/var/$N; exit 1; }
import sys,runpy
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a109-cto-stitch13/tools'); import genes as G
f,sp=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for t in sp.split('+'):
    if not t or t=='-': continue
    if t.startswith('@'):
        for e in runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a120-cto-occ4e80/e/'+t[1:]+'.py')['EDITS']:
            if callable(e): s=e(s); continue
            a,b=e; c=s.count(a); assert c==1,(t,c,a[:100]); s=s.replace(a,b)
    else: s=G.apply(s,[t])
assert s.count('\n')==n0
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $O/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $O/tools/capraw.py $O/var/$N $O/work$W $O/ir/cap_$N > /dev/null 2>&1
if [ ! -f $O/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"spec\":\"$SP\",\"error\":\"compile\"}" | tee -a $O/results.jsonl; grep -m2 -A3 '^error' $O/ir/cap_$N/build.log >&2; rm -rf $O/ir/cap_$N $O/var/$N; exit 1; fi
mv $O/ir/cap_$N/raw.ll $O/ir/$N.ll; rm -rf $O/ir/cap_$N $O/var/$N
cd $O && r=$(python3 tools/rx.py $N --base ir/$N.ll | tail -1)
rm -f $O/ir/$N.ll
echo "$r" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); d['spec']='$SP'; print(json.dumps(d))" | tee -a $O/results.jsonl
