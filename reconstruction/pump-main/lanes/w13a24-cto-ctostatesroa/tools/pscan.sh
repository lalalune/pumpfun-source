#!/bin/bash
# pscan.sh <m.ll> <items> <tag> [nproc]: split items, run iredit scan in N processes (-j 2), merge to scan_<tag>.log
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a24-cto-ctostatesroa; cd $OUT
M=$1; I=$2; T=$3; N=${4:-4}; BASE=${BASE:-}
rm -f it_${T}_part*; split -n r/$N $I it_${T}_part 2>/dev/null || python3 -c "
import sys
L=open('$I').read().split('\n'); L=[l for l in L if l]
for k in range($N): open('it_${T}_part%02d'%k,'w').write('\n'.join(L[k::$N])+'\n')"
for p in it_${T}_part*; do python3 tools/iredit.py scan $M it/scan_${T}_$(basename $p) "$BASE" $p -j 2 > ${p}.log 2>&1 & done; wait
cat it_${T}_part*.log | grep '^{' > scan_$T.log; rm -f it_${T}_part*
python3 -c "
import json
r=[json.loads(l) for l in open('scan_$T.log')]
r.sort(key=lambda x:-x['ratio'])
for x in r[:${TOP:-15}]: print(x['item'],x['ratio'],x['bytes'])
"
