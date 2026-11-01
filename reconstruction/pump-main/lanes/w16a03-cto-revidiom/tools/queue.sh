#!/bin/bash
# queue.sh <name>...: run cap.sh for each e/<name>.py, two at a time (work0/work1), append results to res.jsonl
OUT=~/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom
cd $OUT
run(){ n=$1; s=$2; bash tools/ir/cap.sh $n e/$n.py $s > ir/$n.res 2>&1; r=$(tail -1 ir/$n.res); l=$(python3 tools/binlcs.py $n 2>/dev/null | tail -1); echo "{\"name\":\"$n\",\"res\":$([ -n "$r" ] && echo "$r" | grep -q '^{' && echo "$r" || echo '"fail"'),\"lcs\":\"$l\"}" >> res.jsonl; rm -f ir/$n.ll; rm -rf rx/$n/in.ll rx/$n/o3.ll; }
set -- "$@"
while [ $# -gt 0 ]; do
  a=$1; shift; b=${1:-}; [ -n "$b" ] && shift
  run $a 0 & p1=$!
  if [ -n "$b" ]; then run $b 1 & p2=$!; wait $p2; fi
  wait $p1
done
echo QUEUE_DONE >> res.jsonl
