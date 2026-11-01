#!/bin/bash
# c2q.sh name ...: re-voting climb2 from each step's climb forces (sequential)
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a28-cto-skelunion17
cd $OUT
for n in "$@"; do
  f=$(python3 -c "import json;print(','.join(json.load(open('st/$n/step.json'))['climb']['forces']))")
  python3 tools/climb2.py st/$n/m.ll c2/$n.jsonl --init $f --R 6 --E 4 > c2/$n.log 2>&1
done
echo done > c2/q.done
