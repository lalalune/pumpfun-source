#!/bin/bash
# pair.sh <editdir> name... : run capvar 2 at a time; prints result lines (also appended to t/res.jsonl)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a88-cto-sweeptagmem
cd $O; D=$1; shift
while [ $# -gt 0 ]; do
  a=$1; b=$2; shift; [ -n "$b" ] && shift
  bash tools/capvar.sh $a $D/$a.py 0 > t/cv_$a.txt 2>&1 &
  [ -n "$b" ] && bash tools/capvar.sh $b $D/$b.py 1 > t/cv_$b.txt 2>&1
  wait
  for n in $a $b; do r=$(tail -1 t/cv_$n.txt); python3 -c "
import json,sys
try:
  d=json.loads(sys.argv[1]); n=d['bytes']//8-88; d['M']=round(d['ratio']*(3339+n)/2); print(json.dumps(d))
except Exception: print(json.dumps({'name':sys.argv[2],'error':sys.argv[1][:300]}))
" "$r" $n | tee -a t/res.jsonl; done
  rm -rf $O/var/$a $O/var/$b
done
