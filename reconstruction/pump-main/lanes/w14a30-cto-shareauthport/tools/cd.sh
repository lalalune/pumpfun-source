#!/bin/bash
# cd.sh <mn.ll> <dir> clones...: per clone, place scan then pp on the top-4 pinned placements
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a30-cto-shareauthport
B=$1; D=$2; shift 2; mkdir -p $OUT/$D
for x in "$@"; do n=$(echo $x | tr -d '%.')
  MODE=place XVAL=$x python3 $OUT/tools/pscan.py $B x $OUT/$D/${n}_place.jsonl 4 > $OUT/$D/${n}_place.log 2>&1
  for p in $(python3 -c "
import json;R=[json.loads(l) for l in open('$OUT/$D/${n}_place.jsonl')];R=[r for r in R if r.get('bytes')==27400];R.sort(key=lambda r:-r['ratio'])
print(' '.join(r['lab'].split(':')[0] for r in R[:8]))"); do
    PLACE=$p MODE=pp XVAL=$x python3 $OUT/tools/pscan.py $B x $OUT/$D/${n}_pp_$p.jsonl 4 > /dev/null 2>&1
  done
done; echo done > $OUT/$D/ALLDONE
