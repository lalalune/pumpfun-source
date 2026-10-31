#!/bin/bash
# pipe.sh <rx>: Mperm, colmap, sticky single screen, sticky climb, joint (forces + spill perm), true LCS
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a28-cto-flaghoistrepay; cd $O; n=$1; export RAPRIO_STICKY=1
t2/mp.sh $n 2>&1 | tail -1
python3 t84/colmap.py rx/$n/m.ll cm/$n > /dev/null 2>&1
python3 -c "
import json
d=json.load(open('cm/$n.json')); k=0; f=open('cm/$n.jobs','w')
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours']: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':'%d=%s'%(v,o)})+'\n'); k+=1
  if k>=80: break"
rm -f cm/$n.scr cm/$n.climb.jsonl; python3 t84/screen.py rx/$n/m.ll cm/$n.jobs cm/$n.scr 3
python3 t84/sclimb.py rx/$n/m.ll cm/$n.scr cm/$n.climb.jsonl '' 30 12 > cm/$n.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L[-1].get('force') else '')")
tail -2 cm/$n.climb.log | cut -c1-200
mkdir -p rx/${n}ra; LLC=$O/llvmb/bin/llc; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
RAPRIO_FORCE=$F $LLC -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections rx/$n/m.ll -stop-after=prologepilog -o rx/${n}ra/pei.mir
RAPRIO_FORCE=$F $LLC -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections rx/$n/m.ll -filetype=obj -o rx/${n}ra/f.o
python3 -c "
import sys; sys.path.insert(0,'t2'); import oracle; open('rx/${n}ra/fn.bin','wb').write(oracle.elf_fn('rx/${n}ra/f.o',oracle.KEEP))"
python3 t2/permhc.py rx/${n}ra 2>/dev/null; rm -f rx/${n}ra/f.o
python3 t2/evall.py $n ${n}ra 2>&1 | tail -2
