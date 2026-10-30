#!/bin/bash
# show.sh <results.jsonl>
python3 -c "
import sys,json
for l in open(sys.argv[1]):
  d=json.loads(l); print(d['name'],d.get('status'),d.get('bytes'),d.get('ratio'),d.get('slots_diff'),d.get('calls'),d.get('secs'),d.get('dup_of',''),d.get('error','')[:100])" $1
