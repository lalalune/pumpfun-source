#!/bin/bash
# ev.sh <name>: per-cell measures on rx/<name> -> res/ev_<name>.txt (sc, mp (Mperm/Mhc/LCS), eo, accreg, ares live-ins, rfj)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a22-cto-s3outline; cd $O; n=$1; f=res/ev_$n.txt
{
echo "== $n $(cat rx/$n/res.json)"
python3 tools/sc.py rx/$n/m.o 2>&1 | tail -1
python3 tools/mp.py ${n}_mp rx/$n/m.ll 2>&1 | tail -1
python3 tools/eo.py $n 2>&1 | tail -1
python3 tools/accreg.py $n 2>&1 | tail -1
bash t2/ar.sh $n > rx/$n.ar.json 2>rx/$n.ar.err; python3 -c "
import json; d=json.load(open('rx/$n.ar.json')); a=d['ares']
print('ares', 'restored M',d['M'],'bytes',d['bytes'],'share_call',d['share_call'],'joins',[(j['name'],j['liveins'],j['extra']) for j in a['joins']])" 2>&1
python3 tools/lcschunk.py main $n --mask rfj 2>&1 | tail -1
} > $f 2>&1
rm -rf rx/${n}_mp/f.o
cat $f
