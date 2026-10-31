#!/bin/bash
# gcap.sh <slot> <name> <spec>: main crate + spec ('+'-joined: N1, gene names, @edits file in e/), capture, rx; append to gres.jsonl
O=~/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a04-cto-n1event
W=$1; N=$2; SP=$3
grep -q "\"name\": \"$N\"" $O/gres.jsonl 2>/dev/null && exit 0
rm -rf $O/var/$N; rsync -a --exclude target $WT/programs/pump/ $O/var/$N/
python3 - $O/var/$N/src/creator/admin_cto.rs "$SP" <<'PY' || { echo "{\"name\": \"$N\", \"spec\":\"$SP\",\"error\":\"apply\"}" >> $O/gres.jsonl; rm -rf $O/var/$N; exit 1; }
import sys,runpy
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a109-cto-stitch13/tools'); import genes as G
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event'
N1=[("let nf=a.bonding_curve.creator_fee_bps;","                                      "),("new_creator_fee_bps:nf,","new_creator_fee_bps:a.bonding_curve.creator_fee_bps,")]
f,sp=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
def ed(s,E):
    for e in E:
        if callable(e): s=e(s); continue
        a,b=e; c=s.count(a); assert c==1,(c,a[:100]); s=s.replace(a,b)
    return s
for t in sp.split('+'):
    if t=='N1': s=ed(s,N1)
    elif t.startswith('@'): s=ed(s,runpy.run_path(O+'/e/'+t[1:]+'.py')['EDITS'])
    else:
        t2=G.apply(s,[t]); assert t2!=s,('noop',t); s=t2
assert s.count('\n')==n0
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $O/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $O/tools/capraw.py $O/var/$N $O/work$W $O/ir/cap_$N > /dev/null 2>&1
rm -rf $O/var/$N
if [ ! -f $O/ir/cap_$N/raw.ll ] || grep -q '^error' $O/ir/cap_$N/build.log; then echo "{\"name\": \"$N\", \"spec\":\"$SP\",\"error\":\"compile\"}" >> $O/gres.jsonl; rm -rf $O/ir/cap_$N; exit 1; fi
mv $O/ir/cap_$N/raw.ll $O/ir/$N.ll; rm -rf $O/ir/cap_$N
cd $O && r=$(python3 tools/rx.py $N --base ir/$N.ll | tail -1)
rm -f $O/ir/$N.ll
echo "$r" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); d['spec']='$SP'; print(json.dumps(d))" >> $O/gres.jsonl
[ -n "$KEEPRX" ] || rm -rf $O/rx/$N
