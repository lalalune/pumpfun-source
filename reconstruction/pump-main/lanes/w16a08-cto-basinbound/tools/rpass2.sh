#!/bin/bash
# rpass2.sh <rx> <tag> [K] [R]: restore-aware pass 2: colmap_r under the pass-1 forces (cm/<rx>.force), sticky singles on top,
# sclimb_r with that base, then joint permhc (+ shperm if SHB="deep shallow d" is set) on the final forced restored build.
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound; cd $O; n=$1; t=$2; K=${3:-30}; R=${4:-12}; export RAPRIO_STICKY=1
B=$(cat cm/$n.force)
python3 t84/colmap_r.py rx/$n/m.ll cm/$n$t --force "$B" > cm/$n$t.colmap.txt 2>&1
python3 -c "
import json
B='$B'; d=json.load(open('cm/$n$t.json')); k=0; f=open('cm/$n$t.jobs','w')
fv={x.split('=')[0] for x in B.split(',') if x}
for r in d['rows']:
  v=r['vreg']; o=max(r['votes'],key=r['votes'].get)
  if o=='r10' or o==r['ours'] or str(v) in fv: continue
  f.write(json.dumps({'name':'%d=%s'%(v,o),'force':','.join([x for x in [B,'%d=%s'%(v,o)] if x]),'full':1})+'\n'); k+=1
  if k>=80: break"
rm -f cm/$n$t.scr cm/$n$t.climb.jsonl; python3 t84/screen_r.py rx/$n/m.ll cm/$n$t.jobs cm/$n$t.scr 3
python3 t84/sclimb_r.py rx/$n/m.ll cm/$n$t.scr cm/$n$t.climb.jsonl "$B" $K $R > cm/$n$t.climb.log 2>&1
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/$n$t.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L[-1].get('force') else '')")
echo "$F" > cm/$n$t.force
D=rx/${n}${t}__ra; mkdir -p $D; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
RAPRIO_FORCE=$F llvmb/bin/llc $A rx/$n/m.ll -stop-after=prologepilog -o $D/pei.mir
RAPRIO_FORCE=$F python3 t2/llcw.py $A rx/$n/m.ll -filetype=obj -o $D/f.o
python3 -c "
import sys; sys.path.insert(0,'t2'); import oracle; open('$D/fn.bin','wb').write(oracle.elf_fn('$D/f.o',oracle.KEEP))"
python3 t2/permhc.py $D 2>/dev/null > cm/$n$t.joint.json; rm -f $D/f.o
[ -n "$SHB" ] && python3 t2/shperm.py ${n}${t}__ra $SHB > cm/$n$t.jsh.json
echo "$n$t: $(tail -1 cm/$n$t.climb.log | cut -c1-160) | joint $(cat cm/$n$t.joint.json) | jsh $(cat cm/$n$t.jsh.json 2>/dev/null)"
