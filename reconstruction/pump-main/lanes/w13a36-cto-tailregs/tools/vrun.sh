#!/bin/bash
# vrun.sh <name> <edit.py> <workN> : copy crate, apply EDITS from edit.py to admin_cto.rs, measure, summarize
O=~/.cache/pumpfun-reconstruction/lanes/w13a36-cto-tailregs
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a36-cto-tailregs
n=$1; e=$2; w=$3
rm -rf $O/var/$n; rsync -a --exclude target $WT/programs/pump/ $O/var/$n/
python3 - $O/var/$n/src/creator/admin_cto.rs $e <<'PY' || { echo "{\"name\":\"$n\",\"err\":\"edit\"}"; exit 1; }
import sys,runpy
p,e=sys.argv[1:3]; t=open(p).read(); E=runpy.run_path(e)['EDITS']
for a,b in E:
    c=t.count(a)
    if c!=1: print('count',c,a[:120],file=sys.stderr); sys.exit(1)
    t=t.replace(a,b)
open(p,'w').write(t)
PY
r=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $O/var/$n $O/$w $O/sv/$n)
python3 -c "
import json,sys; d=json.loads(sys.argv[1]); c=d.get('admin_cto',{})
print(json.dumps({'name':'$n','ok':d.get('ok'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'n':d.get('normalized'),'raw':d.get('raw'),'losses':len(d.get('losses') or []),'raw_losses':len(d.get('raw_losses') or []),'sha':d.get('sha')}))" "$r" | tee -a $O/sv/results.jsonl
python3 $O/tools/tail.py $O/sv/$n/unstripped.so 2>/dev/null | sed 's/^/  /'
rm -rf $O/var/$n
