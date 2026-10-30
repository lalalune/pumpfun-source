#!/bin/bash
# rawx.sh <name> <edits.py> : apply EDITS to raw slim IR (base.ll), opt -O3, slim to execute, llc oracle
OUT=${OUT:-$HOME/.cache/pumpfun-reconstruction/lanes/w12a08-cto-errorder}
OPT=$(ls ~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt | head -1)
N=$1; E=$2; B=${3:-$OUT/raw/base.ll}
python3 - $B $E $OUT/raw/$N.ll <<'PY' || exit 1
import sys,runpy
t=open(sys.argv[1]).read(); g=runpy.run_path(sys.argv[2])
for a,b in g['EDITS']:
    c=t.count(a); assert c==1,(c,a[:150]); t=t.replace(a,b)
open(sys.argv[3],'w').write(t)
PY
$OPT -O3 $OUT/raw/$N.ll -S -o $OUT/raw/$N.o3.ll || exit 1
python3 -c "
import sys;sys.path.insert(0,'$OUT/tools')
from slim import slim
open('$OUT/raw/$N.slim.ll','w').write(slim(open('$OUT/raw/$N.o3.ll').read(),keep=r'admin_cto7execute17h'))
"
rm -f $OUT/raw/$N.o3.ll $OUT/raw/$N.ll
python3 $OUT/tools/orc.py $OUT/raw/$N.slim.ll $OUT/raw/$N
