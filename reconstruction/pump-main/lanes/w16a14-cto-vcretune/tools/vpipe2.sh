#!/bin/bash
# vpipe2.sh <name> [N=80] [K=30] [R=12] [P=2]: colmap vote -> single-force screen (vscreen.py threads) -> greedy sticky climb
# -> joint (forced-build Mhc via mpf.py). Experiment only; tools from w16a04 t84 (patched RAPRIO llc).
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a14-cto-vcretune; T=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil/t84
cd $O; n=$1; N=${2:-80}; K=${3:-30}; R=${4:-12}; P=${5:-2}; export RAPRIO_STICKY=1
python3 $T/colmap.py rx/$n/m.ll cm/$n > cm/$n.colmap.txt 2>&1
python3 -c "
import json
d=json.load(open('cm/$n.json')); k=0; f=open('cm/$n.jobs','w')
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours']: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':'%d=%s'%(v,o),'full':1})+'\n'); k+=1
  if k>=$N: break"
python3 s16/vscreen.py rx/$n/m.ll cm/$n.jobs cm/$n.scr $P
rm -f cm/$n.climb.jsonl; python3 $T/sclimb.py rx/$n/m.ll cm/$n.scr cm/$n.climb.jsonl "" $K $R > cm/$n.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '')")
RAPRIO_FORCE=$F MP_LLC=llcf.sh HC=1 python3 s16/mpf.py jt_$n rx/$n/m.ll > cm/$n.joint.json 2>&1
echo "{\"name\":\"$n\",\"force\":\"$F\",\"joint\":$(tail -1 cm/$n.joint.json)}" >> cm/joint.jsonl
