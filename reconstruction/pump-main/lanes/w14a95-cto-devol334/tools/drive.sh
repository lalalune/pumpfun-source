#!/bin/bash
# drive.sh <q0> <q1> : two runlist workers, wait for both
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a95-cto-devol334
bash tools/runlist.sh $1 v2 t/as.jsonl 0 > t/run0.log 2>&1 &
bash tools/runlist.sh $2 v2 t/as.jsonl 1 > t/run1.log 2>&1 &
wait
echo done
