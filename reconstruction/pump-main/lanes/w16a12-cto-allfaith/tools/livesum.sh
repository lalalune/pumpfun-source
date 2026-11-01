#!/bin/bash
# livesum.sh: callee-saved occupancy summary over every stk/<n>_p0/pei.mir (livecs.py) + trampoline check -> stdout
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
for d in stk/*_p0; do n=$(basename $d _p0); [ -f $d/pei.mir ] || continue; python3 tools/livecs.py $d/pei.mir --json 2>/dev/null | python3 -c "
import json,sys
r=json.loads(sys.stdin.read()); n='$n'
def s(p):
  x=r.get(p)
  if not x: return '-'
  return ','.join(x['live'])+('['+'/'.join(sorted({d.split('@')[0] for v in x['defs'].values() for d in v if '@' in d}))+']' if x['live'] else '')
print(n.ljust(6),'w_ata',s('w_ata').ljust(22),'sweep',s('sweep').ljust(24),'tcf',s('tcf').ljust(4),'shcpi',s('shcpi').ljust(4),'poolgate',s('poolgate').ljust(16),'pool',s('pool'))
"; done
python3 tools/tramp.py orig $(ls -d rx/*/ | grep -v "ra/\|mp_" | sed 's#$#fn.bin#')
