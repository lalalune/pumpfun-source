#!/bin/bash
# stack.sh <name>: placement restore (ar.sh) + spill-colour bounds (permhc on raw and restored) + true LCS -> stack/<name>.txt
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound; cd $O; n=$1; mkdir -p stack
bash t2/ar.sh $n > stack/$n.ar.json 2>stack/$n.ar.err || { echo "AR FAIL $n"; tail -3 stack/$n.ar.err; }
cp -f rx/$n/m.o rx/$n/f.o 2>/dev/null; cp -f rx/${n}__r/m.o rx/${n}__r/f.o
python3 t2/permhc.py rx/$n 2>/dev/null > stack/$n.ph.json &
python3 t2/permhc.py rx/${n}__r 2>/dev/null > stack/$n.phr.json
wait
python3 t2/evall.py $n ${n}__r 2>/dev/null | tail -2 > stack/$n.ev.txt
python3 t2/fobj.py rx/m0/pei.mir rx/$n/pei.mir > stack/$n.fobj.txt
rm -f rx/$n/f.o rx/${n}__r/f.o
echo "$n $(cat stack/$n.ar.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["ratio"],d["bytes"],"M",d["M"],"share",d["share_call"],[ (f["reg"],f["slot"],f["kinds"]) for j in d["ares"]["joins"] for f in j.get("fix",[])])') | ph $(cat stack/$n.ph.json) | phr $(cat stack/$n.phr.json)" > stack/$n.txt
cat stack/$n.ev.txt >> stack/$n.txt
