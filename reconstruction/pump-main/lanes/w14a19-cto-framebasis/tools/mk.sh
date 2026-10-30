#!/bin/bash
# mk.sh <name> <genes,comma|file:patch.py> [work] : variant of var/m3 + genes -> src.sh -> x/<name> (frame.txt kept); deletes var+ir
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis; T=$O/tools; n=$1; g=$2; w=${3:-work0}
rm -rf $O/var/$n; rsync -a $O/var/m3/ $O/var/$n/
cd $T && python3 -c "
import sys,fg2
p='$O/var/$n/src/creator/admin_cto.rs'; s=open(p).read()
g='$g'
if g.startswith('py:'):
    exec(open(g[3:]).read())   # defines edit(s)->s
    s=edit(s)
else:
    s=fg2.apply(s,[x for x in g.split(',') if x])
open(p,'w').write(s)" || { echo "$n APPLYFAIL"; rm -rf $O/var/$n; exit 1; }
export PUMP_BUILD_SLOTS=10
bash $T/src.sh $n $w 2>&1 | tail -1
rm -rf $O/var/$n $O/ir/$n
