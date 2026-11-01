#!/bin/bash
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a09-cto-faithunion
n=$1
t2/fnpipe.sh $n fn1 >> fnq_$n.log 2>&1
B=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/${n}fn1.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '')")
t2/fnpipe.sh $n fn2 "$B" >> fnq_$n.log 2>&1
