#!/bin/bash
# vpipe2b.sh <name> <BASEFORCE> <tag> [N=80] [K=30] [R=12] [P=2]: pass 2 of vpipe2.sh (forces on top of BASEFORCE).
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a14-cto-vcretune; T=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil/t84
cd $O; n=$1; B=$2; t=$3; N=${4:-80}; K=${5:-30}; R=${6:-12}; P=${7:-2}; export RAPRIO_STICKY=1
python3 $T/colmap.py rx/$n/m.ll cm/$n$t --force "$B" > cm/$n$t.colmap.txt 2>&1
python3 -c "
import json
B='$B'; d=json.load(open('cm/$n$t.json')); k=0; f=open('cm/$n$t.jobs','w')
fv={x.split('=')[0] for x in B.split(',') if x}
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours'] or str(v) in fv: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':B+',%d=%s'%(v,o),'full':1})+'\n'); k+=1
  if k>=$N: break"
python3 s16/vscreen.py rx/$n/m.ll cm/$n$t.jobs cm/$n$t.scr $P
rm -f cm/$n$t.climb.jsonl; python3 $T/sclimb.py rx/$n/m.ll cm/$n$t.scr cm/$n$t.climb.jsonl "$B" $K $R > cm/$n$t.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n$t.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '$B')")
RAPRIO_FORCE=$F MP_LLC=llcf.sh HC=1 python3 s16/mpf.py jt_$n$t rx/$n/m.ll > cm/$n$t.joint.json 2>&1
echo "{\"name\":\"$n$t\",\"force\":\"$F\",\"joint\":$(tail -1 cm/$n$t.joint.json)}" >> cm/joint.jsonl
