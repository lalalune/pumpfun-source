#!/bin/bash
# rpipe.sh <rx> [K] [R]: RA bound on the RESTORED layout: colmap_r (votes on the restored build), sticky single screen and
# greedy sticky climb through llcw.py (patched llc + ares.py join-restore), then joint permhc on the final forced restored build.
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound; cd $O; n=$1; K=${2:-30}; R=${3:-12}; export RAPRIO_STICKY=1
python3 t84/colmap_r.py rx/$n/m.ll cm/$n > cm/$n.colmap.txt 2>&1
python3 -c "
import json
d=json.load(open('cm/$n.json')); k=0; f=open('cm/$n.jobs','w')
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours']: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':'%d=%s'%(v,o),'full':1})+'\n'); k+=1
  if k>=80: break"
rm -f cm/$n.scr cm/$n.climb.jsonl; python3 t84/screen_r.py rx/$n/m.ll cm/$n.jobs cm/$n.scr 3
python3 t84/sclimb_r.py rx/$n/m.ll cm/$n.scr cm/$n.climb.jsonl '' $K $R > cm/$n.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L[-1].get('force') else '')")
echo "$F" > cm/$n.force
D=rx/${n}__ra; mkdir -p $D; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
RAPRIO_FORCE=$F llvmb/bin/llc $A rx/$n/m.ll -stop-after=prologepilog -o $D/pei.mir
RAPRIO_FORCE=$F python3 t2/llcw.py $A rx/$n/m.ll -filetype=obj -o $D/f.o
python3 -c "
import sys; sys.path.insert(0,'t2'); import oracle; open('$D/fn.bin','wb').write(oracle.elf_fn('$D/f.o',oracle.KEEP))"
python3 t2/permhc.py $D 2>/dev/null > cm/$n.joint.json; rm -f $D/f.o
python3 t2/evall.py ${n}__ra 2>/dev/null | tail -1 > cm/$n.ev.txt
echo "$n RA: $(tail -1 cm/$n.climb.log | cut -c1-160) | joint $(cat cm/$n.joint.json) | $(cat cm/$n.ev.txt)"
