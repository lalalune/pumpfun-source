#!/bin/bash
# batch.sh name... : run capvar on names, two at a time (work0/work1), append results to res.jsonl
cd ~/.cache/pumpfun-reconstruction/lanes/w14a48-cto-tailerr
set -- "$@"
while [ $# -gt 0 ]; do
  a=$1; shift; b=$1; [ $# -gt 0 ] && shift
  tools/capvar.sh $a e/$a.py 0 2>/dev/null | tail -1 >> res.jsonl &
  [ -n "$b" ] && { sleep 1; tools/capvar.sh $b e/$b.py 1 2>/dev/null | tail -1 >> res.jsonl; }
  wait
done
