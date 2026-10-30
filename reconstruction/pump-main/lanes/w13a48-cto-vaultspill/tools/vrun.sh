#!/bin/bash
# vrun.sh <name> <edits.py> <workslot>: copy main crate, apply edits (EDITS=[(old,new)...] each must occur once, no newline changes), measure, fbsplit
set -u
O=$HOME/.cache/pumpfun-reconstruction/lanes/w13a48-cto-vaultspill
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a48-cto-vaultspill
n=$1; e=$2; w=$3
rm -rf $O/var/$n; mkdir -p $O/var/$n
rsync -a --exclude target $WT/programs/pump/ $O/var/$n/
python3 - "$O/var/$n/src/creator/admin_cto.rs" "$e" <<'PY' || exit 1
import sys,runpy
p,e=sys.argv[1:3]; t=open(p).read(); n0=t.count('\n')
for x,y in runpy.run_path(e)['EDITS']:
    c=t.count(x); assert c==1,(c,x[:120]); t=t.replace(x,y)
assert t.count('\n')==n0,'line count changed'
open(p,'w').write(t)
PY
r=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $O/var/$n $O/work$w $O/t/$n)
fb=""
if [ -f $O/t/$n/unstripped.so ]; then python3 $O/tools/sobin.py $O/t/$n/unstripped.so $O/t/$n/fn.bin; fb=$(python3 $O/tools/fbsplit.py $O/t/$n/fn.bin 2>/dev/null); rm -f $O/t/$n/candidate.so; fi
echo "$n $(echo "$r" | python3 -c 'import json,sys;d=json.loads(sys.stdin.read());c=d.get("admin_cto",{});print(json.dumps({"ok":d["ok"],"n":d.get("normalized"),"raw":d.get("raw"),"losses":d.get("losses"),"rl":d.get("raw_losses"),"ratio":c.get("ratio"),"slots":c.get("slots_diff"),"bytes":c.get("cand_bytes"),"err":d.get("error","")[-400:]}))') $fb" | tee -a $O/results.txt
rm -rf $O/var/$n
