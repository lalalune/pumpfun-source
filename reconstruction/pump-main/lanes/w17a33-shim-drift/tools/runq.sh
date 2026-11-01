#!/bin/bash
# runq.sh <queue.txt> <workers>: screen each neutral base (name ids sig) x its B set; append analysis to res/ana.txt
cd $HOME/.cache/pumpfun-reconstruction/lanes/w17a33-shim-drift
q=$1; W=${2:-8}
while read -r name ids sig; do
  [ -z "$name" ] && continue
  [ -f b/$name.done ] && continue
  python3 tools/drift.py mkb $name $ids --local 15 > b/$name.nb
  python3 tools/screenq.py ir/m0.s.ll gen/U.jsonl b/$name.jsonl $W --combo b/$name.combo --base-sig $sig --base-M 2295 > b/$name.log 2>&1
  python3 tools/drift.py ana $name $sig >> res/ana.txt 2>&1
  touch b/$name.done
done < $q
