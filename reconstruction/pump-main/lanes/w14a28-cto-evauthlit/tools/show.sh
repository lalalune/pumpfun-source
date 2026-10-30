#!/bin/bash
cat $1 2>/dev/null | python3 -c "
import sys,json
for l in sys.stdin:
    r=json.loads(l); c=r.get('admin_cto',{})
    print(r['name'], r.get('error','')[:200], c.get('ratio'), c.get('slots_diff'), c.get('cand_bytes'), c.get('calls_candidate'), 'L',len(r.get('losses',[])), len(r.get('raw_losses',[])), r.get('sha'))
"
