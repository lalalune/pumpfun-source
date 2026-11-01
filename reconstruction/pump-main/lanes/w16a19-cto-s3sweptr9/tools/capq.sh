#!/bin/bash
# capq.sh <slot> name... : sequential captures on one work dir, each followed by a background rx (opt -O3 + llc)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9; S=$1; shift
for n in "$@"; do
  bash $OUT/t2/cap.sh $n $OUT/e/$n.py $S >> $OUT/capq$S.log 2>&1 && (cd $OUT && nice -n 5 python3 t2/rx.py $n --base ir/$n.ll >> $OUT/rxq.log 2>&1 &)
done
echo "done $S $(date +%T)" >> $OUT/capq$S.log
