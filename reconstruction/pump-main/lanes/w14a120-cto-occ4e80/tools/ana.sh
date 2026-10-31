#!/bin/bash
# ana.sh <name>: colour map + single colour-force screen of rx/<name>/m.ll; prints top 6 forces
O=~/.cache/pumpfun-reconstruction/lanes/w14a120-cto-occ4e80; N=$1; cd $O
python3 tools/colmap.py rx/$N/m.ll cm/$N | head -1
python3 - $N <<'PY'
import json,sys
n=sys.argv[1]; d=json.load(open(f'cm/{n}.json')); J=[]
for r in d['rows']:
    if r['miss']>=2 and r['orig_major']!='r10' and r['orig_major']!=r['ours']:
        J.append({'name':f"cf{r['orig_major']}_{r['vreg']}",'v':r['vreg'],'force':f"{r['vreg']}={r['orig_major']}",'full':1,'sites':r['sites'][:3]})
open(f's/jcc_{n}.jsonl','w').write('\n'.join(json.dumps(j) for j in J)+'\n')
PY
rm -f s/rcc_$N.jsonl; python3 tools/screen.py rx/$N/m.ll s/jcc_$N.jsonl s/rcc_$N.jsonl 4 >/dev/null 2>&1
python3 - $N <<'PY'
import json,sys
n=sys.argv[1]; R=[json.loads(l) for l in open(f's/rcc_{n}.jsonl')]
R.sort(key=lambda r:-r['ratio'])
for r in R[:6]: print(' ',r['force'],r['ratio'],r['bytes'],r.get('sites'))
PY
