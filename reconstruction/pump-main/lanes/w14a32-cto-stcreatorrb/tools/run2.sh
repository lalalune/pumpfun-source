#!/bin/bash
# run2.sh <resfile> <edit files...>: capvar two at a time
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a32-cto-stcreatorrb
R=$1; shift
cd $OUT
run(){ n=$(basename $1 .py); bash tools/capvar.sh $n $1 $2 >> $R 2>>$OUT/run2.err; }
while [ $# -gt 0 ]; do
  run $1 0 & p1=$!
  if [ $# -gt 1 ]; then run $2 1 & p2=$!; wait $p2; shift; fi
  wait $p1; shift
done
echo DONE >> $R
