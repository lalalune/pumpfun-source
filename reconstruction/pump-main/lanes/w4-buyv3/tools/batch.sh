#!/bin/bash
# batch.sh t1 t2 ... : run trials 3 at a time; results in $OUT/<t>.res
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w4-buyv3; cd $OUT
i=0
for t in "$@"; do
  rm -f $t.res
  slot=$((i%3+1)); WORK=$OUT/work$slot $OUT/oracle/trial.sh $t edits/$t.py > $t.res 2>&1 &
  i=$((i+1)); if [ $((i%3)) -eq 0 ]; then wait; fi
done; wait
for t in "$@"; do tail -1 $t.res; done
