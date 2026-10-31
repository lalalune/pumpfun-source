#!/bin/bash
# lpipe.sh <rx> [N singles=80] [K climb=30] [R rounds=12] [P procs=3] [BASEFORCE]
# w15a28 pipe.sh adapted (experiment only): colmap vote, sticky single screen, sticky climb, forced build,
# joint permhc (forces + spill perm), true LCS (evall) and window-rotation check (winrot) on one raw-IR capture.
# Unforced M/Mperm/Mhc come from scr.py's mp.py (rx/mp_<rx>/mp.json).
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil; cd $O; n=$1; N=${2:-80}; K=${3:-30}; R=${4:-12}; P=${5:-3}; B=${6:-}
t=${TAGSFX:-}; export RAPRIO_STICKY=1
LLC=$O/llvmb/bin/llc; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
if [ -n "$B" ]; then python3 t84/colmap.py rx/$n/m.ll cm/$n$t --force "$B" > cm/$n$t.colmap.txt 2>&1
else python3 t84/colmap.py rx/$n/m.ll cm/$n$t > cm/$n$t.colmap.txt 2>&1; fi
python3 -c "
import json
B='$B'; d=json.load(open('cm/$n$t.json')); k=0; f=open('cm/$n$t.jobs','w')
fv={x.split('=')[0] for x in B.split(',') if x}
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours'] or str(v) in fv: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':(B+',' if B else '')+'%d=%s'%(v,o),'full':1})+'\n'); k+=1
  if k>=$N: break"
rm -f cm/$n$t.scr cm/$n$t.climb.jsonl; python3 t84/screen.py rx/$n/m.ll cm/$n$t.jobs cm/$n$t.scr $P
python3 t84/sclimb.py rx/$n/m.ll cm/$n$t.scr cm/$n$t.climb.jsonl "$B" $K $R > cm/$n$t.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n$t.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '')")
mkdir -p rx/${n}${t}ra
RAPRIO_FORCE=$F $LLC $A rx/$n/m.ll -stop-after=prologepilog -o rx/${n}${t}ra/pei.mir
RAPRIO_FORCE=$F $LLC $A rx/$n/m.ll -filetype=obj -o rx/${n}${t}ra/f.o
python3 -c "
import sys; sys.path.insert(0,'t2'); import oracle; open('rx/${n}${t}ra/fn.bin','wb').write(oracle.elf_fn('rx/${n}${t}ra/f.o',oracle.KEEP))"
python3 t2/permhc.py rx/${n}${t}ra 2>/dev/null > rx/${n}${t}ra/permhc.out; rm -f rx/${n}${t}ra/f.o
python3 t2/evall.py ${n}${t}ra 2>&1 | tail -1 > rx/${n}${t}ra/evall.out
echo "FORCE $F" > rx/${n}${t}ra/force.txt
python3 t2/rowsum.py $n "$t" | tee -a data/joint.jsonl
