#!/bin/bash
# evalf.sh <name>: price a captured source form rx/<name>/m.ll: ire (llcw restore, permhc), coal (SW/RP merged?), coalor (ideal order)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9; cd $O; n=$1
a=$(python3 t2/ire.py E_$n --base rx/$n/m.ll --perm 2>&1 | tail -1)
c=$(python3 t2/coal.py rx/$n/m.ll 2>&1 | head -1)
o=$(python3 t2/coalor.py rx/$n/m.ll O_$n --perm 2>&1 | tail -1)
echo "{\"form\":\"$n\",\"ire\":$a,\"coal\":\"$c\",\"coalor\":$o}" >> $O/cm/evalf.jsonl
