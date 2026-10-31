#!/bin/bash
# trial.sh <name(+joined)> <slot>: build edits from sp/defs.py, capture, rx, print seq head + sc
O=~/.cache/pumpfun-reconstruction/lanes/w14a104-cto-brhead; N=$1; S=$2; cd $O
python3 -c "
import sys; sys.path.insert(0,'sp'); import defs
open('src_edits/$N.py','w').write('EDITS='+repr(defs.get('$N')))" || exit 1
R=$(bash tools/capvar.sh $N src_edits/$N.py $S 2>&1 | tail -1)
echo "$R" > tmp/res_$N.json
if [ -f rx/$N/m.s ]; then
  echo "$N $R $(python3 tools/sc.py rx/$N/m.s | cut -d' ' -f2-)"
  python3 tools/seq.py rx/$N/m.s bb6.i 26 | awk '{printf "%s ",$1}'; echo
else echo "$N FAIL $R"; fi
