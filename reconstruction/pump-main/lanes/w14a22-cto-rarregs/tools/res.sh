#!/bin/bash
python3 -c "
import json,sys
for l in open(sys.argv[1]):
    r=json.loads(l); x=r.get('none')
    if isinstance(x,dict): print(r['name'], x['ratio'], x['bytes'], round(x['ratio']*(3339+ (x['bytes']//8 - x['lddw']))/2), x['outl'])
    else: print(r['name'],x,r.get('err'))" ${1:-/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs/res.jsonl}
