#!/bin/bash
# brjoint.sh <rx> <tag> [FORCES]: B/Br relayout (w14a87 Bspec963 via w14a98 sub.border2 content resolution against main's asm)
# on the sticky-forced build of rx, then joint permhc (forces + Br + spill perm). Experiment only (post-RA relayout oracle).
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil; cd $O; n=$1; t=$2; F=${3:-}
export RAPRIO_STICKY=1; LLC=$O/llvmb/bin/llc; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
mkdir -p br rx/${t}Br
RAPRIO_FORCE=$F $LLC $A rx/$n/m.ll -filetype=asm -o br/$t.s
RAPRIO_FORCE=$F $LLC $A rx/$n/m.ll -stop-after=prologepilog -o rx/${t}Br/pei.mir
cd t98 && python3 - "$O" "$t" <<'PY'
import sys,json,shutil
import sub,sc
O,t=sys.argv[1],sys.argv[2]
B=open(O+'/tmp/Bspec.txt').read().strip().split(',')
pm=O+'/br/m0.s'; pv=O+f'/br/{t}.s'
import os
if os.environ.get('BRPOS')=='1':
    # positional resolution: the variant block at main's index (validate span 14..39 has the same block count)
    R=sub.R; _,blm,_=R.parse(pm); ebm=R.explicit(blm); nm=[x[0] for x in ebm]
    am=sub.resolve(pm,B); im=[nm.index(x) for x in am]
    pre,blocks,post=R.parse(pv); eb=R.explicit(blocks); names=[x[0] for x in eb]
    listed=[names[i] for i in im]; lo,hi=min(im),max(im); span=names[lo:hi+1]; rest=[x for x in span if x not in listed]
    new=names[:lo]+listed+rest+names[hi+1:]; miss=[]
else:
    names,new,miss=sub.border2(pm,pv,B)
res={'tag':t,'miss':miss}
for rev,nm in ((0,'B'),(1,'Br')):
    tx,fl=sub.emit(pv,new,rev); p=O+f'/br/{t}_{nm}.s'; open(p,'w').write(tx)
    s=sc.score(p); s.pop('ch',None); res[nm]={'M':s['M'],'bytes':s['bytes'],'ratio':s['ratio'],'jM':s['jM'],'flips':fl}
s=sc.score(pv); s.pop('ch',None); res['base']={'M':s['M'],'bytes':s['bytes'],'ratio':s['ratio'],'jM':s['jM']}
shutil.copy(O+f'/br/{t}_Br.o',O+f'/rx/{t}Br/f.o')
print(json.dumps(res))
PY
cd $O; python3 t2/permhc.py rx/${t}Br 2>/dev/null; rm -f rx/${t}Br/f.o
