#!/bin/bash
# runk.sh <queue.txt> <workers>: knob bases (name ids sig dbt)
cd $HOME/.cache/pumpfun-reconstruction/lanes/w17a33-shim-drift
q=$1; W=${2:-6}
while read -r name ids sig dbt; do
  [ -z "$name" ] && continue
  [ -f b/$name.done ] && continue
  python3 tools/drift.py mkk $name $ids $dbt > b/$name.nb
  python3 tools/screenq.py ir/m0.s.ll gen/U.jsonl b/$name.jsonl $W --combo b/$name.combo --base-sig $sig --base-M 2295 > b/$name.log 2>&1
  python3 tools/drift.py ana $name $sig >> res/ana.txt 2>&1
  touch b/$name.done
done < $q
