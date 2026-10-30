#!/bin/bash
# pc.sh <name> <base m.ll> [edits.py] [--llc ..]: llcm + chunk + lseq
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a10-cto-and1outline
r=$(python3 $O/tools/llcm.py "$@") || { echo "$r"; exit 1; }
c=$(python3 $O/tools/chunk.py $O/rx/$1/m.o)
python3 -c "import json,sys;a=json.loads(sys.argv[1]);b=json.loads(sys.argv[2]);a.update({k:b[k] for k in ('rm','rmV','rmT','Lrm','rmC')});print(json.dumps(a))" "$r" "$c" | tee -a $O/results.jsonl
python3 $O/tools/lseq.py $O/rx/$1/m.o 2>&1 | tail -1
