#!/bin/bash
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a23-cto-tcflit
python3 - <<'PY' > pr/plan.txt
import json
d=json.load(open('pr/cfg.json'))
ns=sorted(d['cfg'])
for i,a in enumerate(ns):
    for ca in d['cfg'][a]:
        for b in ns[i+1:]:
            print(a,d['xv'][a],ca,b,d['xv'][b],' '.join(d['cfg'][b]))
PY
while read a xa ca b xb rest; do
  t=pr/m_${a}_$(echo $ca|tr ':.' '__').ll
  [ -f $t ] || DUMP=$t DUMPJOB=$ca XVAL=$xa XGEP=%i363 python3 tools/pscan2.py rx/m5/mn.ll x /dev/null 1
  printf '%s\n' $rest > pr/jobs_$$.txt
  MODE=list JOBS=pr/jobs_$$.txt XVAL=$xb XGEP=%i363 python3 tools/pscan2.py $t x pr/r_${a}_$(echo $ca|tr ':.' '__')__$b.jsonl 4 > /dev/null 2>&1
done < pr/plan.txt
echo fin
