#!/bin/bash
# cclimb.sh <m.ll> <name> [climb args]: colour map + colour-target single screen + forward selection (private llc; experiment only)
O=~/.cache/pumpfun-reconstruction/lanes/w14a93-cto-pdaheadra; T=$(cd $(dirname $0); pwd); M=$1; N=$2; shift 2
cd $O; mkdir -p cm s
python3 $T/colmap.py $M cm/$N ${SCREEN_BASE_FORCE:+--force $SCREEN_BASE_FORCE} | head -1
python3 - $N <<'PY'
import json,sys
n=sys.argv[1]; d=json.load(open(f'cm/{n}.json')); J=[]
for r in d['rows']:
    if r['miss']>=2 and r['orig_major']!='r10' and r['orig_major']!=r['ours']:
        J.append({'name':f"cf{r['orig_major']}_{r['vreg']}",'v':r['vreg'],'force':f"{r['vreg']}={r['orig_major']}",'full':1})
    if r['miss']>=3 and r['ours'] in ('r6','r7','r8','r9'):
        J.append({'name':f"cfsp_{r['vreg']}",'v':r['vreg'],'force':f"{r['vreg']}=spill",'full':1})
open(f's/jcc_{n}.jsonl','w').write('\n'.join(json.dumps(j) for j in J)+'\n')
PY
rm -f s/rcc_$N.jsonl s/ccc_$N.jsonl
python3 $T/screen.py $M s/jcc_$N.jsonl s/rcc_$N.jsonl ${CC_N:-4}
CLIMB_N=${CC_N:-4} python3 $T/climb.py $M s/rcc_$N.jsonl s/ccc_$N.jsonl 150 12 "$@" | cut -c1-400
