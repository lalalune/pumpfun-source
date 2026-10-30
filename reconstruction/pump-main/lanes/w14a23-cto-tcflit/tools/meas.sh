#!/bin/bash
# meas.sh <name> <edits.py> <slot>: copy crate, apply edits, run measure.sh
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a23-cto-tcflit
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a23-cto-tcflit
N=$1; P=$2; W=$3
rm -rf $OUT/var/m_$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/m_$N/
python3 - $OUT/var/m_$N/src/creator/admin_cto.rs $P <<'PY' || exit 1
import sys
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g={}; exec(open(p).read(),g)
n0=s.count('\n')
if 'T' in g: s=g['T'](s)
for a,b in g.get("EDITS",[]):
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $OUT/var/m_$N $OUT/work$W $OUT/t/$N > $OUT/t/$N.json 2>$OUT/t/$N.err
python3 -c "import json;d=json.load(open('$OUT/t/$N.json'));print('$N',d['normalized'],d['raw'],d['losses'],d['raw_losses'],d['admin_cto'])"
rm -rf $OUT/var/m_$N
