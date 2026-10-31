#!/bin/bash
# pass2.sh <rx> <tag> <baseforce>: colmap under base forces, sticky singles on top of base, sclimb with base
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a28-cto-flaghoistrepay; cd $O; n=$1; t=$2; B=$3; export RAPRIO_STICKY=1
python3 t84/colmap.py rx/$n/m.ll cm/$n$t --force "$B" > /dev/null 2>&1
python3 -c "
import json
B='$B'; d=json.load(open('cm/$n$t.json')); k=0; f=open('cm/$n$t.jobs','w')
fv={x.split('=')[0] for x in B.split(',')}
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours'] or str(v) in fv: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':B+',%d=%s'%(v,o),'full':1})+'\n'); k+=1
  if k>=80: break"
rm -f cm/$n$t.scr cm/$n$t.climb.jsonl; python3 t84/screen.py rx/$n/m.ll cm/$n$t.jobs cm/$n$t.scr 3
python3 t84/sclimb.py rx/$n/m.ll cm/$n$t.scr cm/$n$t.climb.jsonl "$B" 30 12 > cm/$n$t.climb.log 2>&1
python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n$t.climb.log') if l.startswith('{')]
print('$n$t',[(x['round'],x['ratio'],x['bytes'],x.get('L2')) for x in L]); print('FORCE',L[-1]['force'])"
