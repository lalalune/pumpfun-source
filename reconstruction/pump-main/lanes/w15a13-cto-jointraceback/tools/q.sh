#!/bin/bash
# q.sh <list of names>: run e/<name>.py through cs.sh, 2 at a time, results -> res.txt, ledger record
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a13-cto-jointraceback; cd $OUT
run(){ w=$1; shift; for n in "$@"; do [ -f rx/$n/res.json ] && continue; r=$(tools/cs.sh $n e/$n.py $w 2>&1 | tail -2 | tr '\n' ' '); echo "$n | $r" >> res.txt; python3 tools/rec.py $n "$r"; done; }
a=(); b=(); i=0; for n in "$@"; do if [ $((i%2)) = 0 ]; then a+=($n); else b+=($n); fi; i=$((i+1)); done
run 0 "${a[@]}" & run 1 "${b[@]}" & wait
