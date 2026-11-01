#!/bin/bash
# run.sh <name> <edits.py> <slot> [base crate]: copy crate, apply EDITS=[(old,new),...] (line count kept), measure, region-compare vs main
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a14-shim-shimwhole
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a14-shim-shimwhole
N=$1; E=$2; W=$3; B=${4:-$WT/programs/pump}
rm -rf $OUT/var/$N; rsync -a --exclude target $B/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs $OUT/var/$N/src/lib.rs "$E" <<'PY' || { echo "$N EDITFAIL" >> $OUT/res/R.txt; exit 1; }
import sys,runpy
f,lib,e=sys.argv[1],sys.argv[2],sys.argv[3]; g=runpy.run_path(e)
for path,key in ((f,'EDITS'),(lib,'LIBEDITS')):
    s=open(path).read(); n0=s.count('\n')
    for a,b in g.get(key,[]):
        c=s.count(a); assert c==1,(key,c,a[:160]); s=s.replace(a,b)
    if key=='EDITS' and 'F' in g: s0=s; s=g['F'](s); assert s!=s0,'F changed nothing'
    assert s.count('\n')==n0,('line count changed',path)
    open(path,'w').write(s)
PY
r=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N 2>&1 | tail -1)
echo "$r" > $OUT/res/$N.json
python3 - "$N" "$r" >> $OUT/res/R.txt <<'PY'
import json,sys
n,r=sys.argv[1:3]
try: d=json.loads(r)
except Exception: print(n,'BADJSON',r[:300]); sys.exit()
if not d.get('ok'): print(n,'FAIL',str(d.get('error'))[-600:].replace('\n',' ')); sys.exit()
c=d['admin_cto']; print(n,'norm',d['normalized'],'raw',d['raw'],'L',len(d['losses']),len(d['raw_losses']),'ratio',c['ratio'],'slots',c['slots_diff'],'bytes',c['cand_bytes'],'calls',c['calls_candidate'],'sha',d['sha'])
PY
if [ -f $OUT/t/$N/unstripped.so ]; then python3 $OUT/tools/rc.py $OUT/t/main7d5e/unstripped.so $OUT/t/$N/unstripped.so | tail -2 >> $OUT/res/R.txt; python3 $OUT/tools/rc.py $OUT/t/main7d5e/unstripped.so $OUT/t/$N/unstripped.so --mask rfj | tail -2 | sed 's/^/  rfj /' >> $OUT/res/R.txt; fi
rm -rf $OUT/var/$N
grep -A4 "^$N " $OUT/res/R.txt | tail -5
