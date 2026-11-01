#!/bin/bash
# evalall.sh <name>...: fuev (true LCS, dotmap) + cells for each capture not yet evaluated
O=~/.cache/pumpfun-reconstruction/lanes/w16a11-cto-plaintail; cd $O
for n in "$@"; do
  [ -f rx/$n/fn.bin ] || { echo "$n: no fn.bin"; continue; }
  grep -q "\"name\":\"$n\"" data/cells.jsonl 2>/dev/null || bash t6/cells.sh $n rx/$n/m.ll >/dev/null 2>&1
  grep -q "rx/$n/fn.bin" data/fuev.jsonl 2>/dev/null || python3 tools/fuev.py rx/$n/fn.bin >> data/fuev.jsonl
done
