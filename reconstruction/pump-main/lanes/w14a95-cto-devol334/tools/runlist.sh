#!/bin/bash
# runlist.sh <listfile> <vdir> <res.jsonl> <slot>
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a95-cto-devol334
L=$1; V=$2; R=$3; W=$4
while read n; do
  [ -z "$n" ] && continue
  grep -q "\"name\": \"$n\"" $R 2>/dev/null && continue
  line=$(bash $OUT/tools/capvar.sh $n $V/$n.py $W 2>/dev/null < /dev/null | tail -1)
  [ -z "$line" ] && line="{\"name\":\"$n\",\"error\":\"nooutput\"}"
  python3 -c "
import json,sys
try:
  d=json.loads(sys.argv[1]); n=d['bytes']//8-88; d['M']=round(d['ratio']*(3339+n)/2); print(json.dumps(d))
except Exception: print(json.dumps({'name':sys.argv[2],'error':sys.argv[1][:300]}))
" "$line" $n >> $R
  rm -f $OUT/ir/$n.ll $OUT/rx/$n/m.o; rm -rf $OUT/var/$n
done < $L
