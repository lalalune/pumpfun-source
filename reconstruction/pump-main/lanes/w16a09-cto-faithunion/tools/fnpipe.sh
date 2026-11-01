#!/bin/bash
# fnpipe.sh <rx> <tag> [BASEFORCE]: RA pass whose screen and climb objective is the fnorm-rebased M (alloca layout mapped
# to main's frame), i.e. the climb sees register gains that a frame shift would hide. Then the full stacked bound.
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a09-cto-faithunion; cd $O; n=$1; t=$2; B=${3:-}; export RAPRIO_STICKY=1
export FN_VAR_PEI=$O/stk/$n/pei.mir FN_REF_PEI=$O/stk/ref/pei.mir
if [ -n "$B" ]; then python3 t84/colmap.py rx/$n/m.ll cm/$n$t --force "$B" > /dev/null 2>&1
else python3 t84/colmap.py rx/$n/m.ll cm/$n$t > /dev/null 2>&1; fi
python3 -c "
import json
B='$B'; d=json.load(open('cm/$n$t.json')); k=0; f=open('cm/$n$t.jobs','w')
fv={x.split('=')[0] for x in B.split(',') if x}
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours'] or str(v) in fv: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':(B+',' if B else '')+'%d=%s'%(v,o),'full':1})+'\n'); k+=1
  if k>=80: break"
rm -f cm/$n$t.scr cm/$n$t.climb.jsonl
python3 t84/screen_fn.py rx/$n/m.ll cm/$n$t.jobs cm/$n$t.scr 3
python3 t84/sclimb_fn.py rx/$n/m.ll cm/$n$t.scr cm/$n$t.climb.jsonl "$B" 30 12 > cm/$n$t.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n$t.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '$B')")
t2/stk.sh $n "$F" $t > /dev/null 2>&1
python3 - $n $t <<'PY'
import json,sys; n,t=sys.argv[1:3]; r=json.load(open(f'stk/{n}_{t}/stk.json')); r['n']=n; r['pass']=t
open('data/stkra.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps({k:r[k] for k in ('n','pass','nforce','bytes','M_plain','Mfn_plain','Mfnhc','stacked')}))
PY
