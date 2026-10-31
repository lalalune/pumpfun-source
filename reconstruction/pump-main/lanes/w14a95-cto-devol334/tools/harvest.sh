#!/bin/bash
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a95-cto-devol334
for d in rx/*/; do [ $d/res.json -nt rx/B1/res.json ] || continue; n=$(basename $d); [ "$n" = B0 ] && continue; [ -f $d/res.json ] || continue; grep -q "\"name\": \"$n\"" t/as.jsonl && continue
python3 -c "
import json,sys
d=json.loads(open(sys.argv[1]).read()); n=d['bytes']//8-88; d['M']=round(d['ratio']*(3339+n)/2); print(json.dumps(d))" $d/res.json >> t/as.jsonl; done
