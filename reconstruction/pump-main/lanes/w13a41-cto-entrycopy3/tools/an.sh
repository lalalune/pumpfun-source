#!/bin/bash
# an.sh name... : reloads (ldxdw from r10), entry-region seg ratio, regdelta vs main
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a41-cto-entrycopy3
for n in "$@"; do
  [ -f $O/rx/$n/m.o ] || continue
  bash $O/tools/dis.sh $O/rx/$n/m.o > $O/rx/$n/fn.dis
  rl=$(grep -c "ldxdw r[0-9], \[r10 - " $O/rx/$n/fn.dis)
  python3 - $O/rx/$n/fn.bin $n $rl <<'PY'
import sys,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a41-cto-entrycopy3/tools')
src=open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a41-cto-entrycopy3/tools/rx.py').read(); g={}; exec(src[:src.index("OUT=os.environ.get('RX_OUT'")],g)
o=g['mask'](g['orig_window']()); c=g['mask'](open(sys.argv[1],'rb').read())
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
h={}
for a,b,k in sm.get_matching_blocks():
    for i in range(a,a+k): h[i*8//0x800]=h.get(i*8//0x800,0)+1
# entry: orig 0x0000-0x0800 tokens matched
print(sys.argv[2],'reloads',sys.argv[3],'ratio',round(sm.ratio(),5),'match_by_0x800',[h.get(i,0) for i in range(14)])
PY
done
