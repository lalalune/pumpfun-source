#!/bin/bash
# sc.sh <name> <edits.py> <slot>: capvar + chunk table
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a02-cto-validatecr
r=$(bash $O/tools/capvar.sh $1 $2 $3 2>$O/rx/$1.err) || { echo "{\"name\":\"$1\",\"error\":\"compile\"}"; exit 1; }
c=$(python3 $O/tools/chunk.py $O/rx/$1/m.o)
python3 -c "import json,sys;a=json.loads(sys.argv[1]);b=json.loads(sys.argv[2]);a.update({k:b[k] for k in ('fm','rm','rmV','rmT','fmV','Lrm','Lfm','Ln','rmC')});print(json.dumps(a))" "$r" "$c" | tee -a $O/results.jsonl
