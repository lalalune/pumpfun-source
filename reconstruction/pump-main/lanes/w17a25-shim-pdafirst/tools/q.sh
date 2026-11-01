#!/bin/bash
# q.sh name1 name2 ...: capture e/<name>.py variants, 2 at a time (work0/work1); results in res/<name>.json, region table in res/<name>.rc
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a25-shim-pdafirst
run1(){ n=$1; w=$2
  $OUT/tools/cap.sh $n $OUT/e/$n.py $w > $OUT/res/$n.json 2>&1
  if [ -f $OUT/fx/$n/fn.bin ]; then
    ( cd $OUT/tools; python3 rc.py $OUT/fx/${REF:-m1}/fn.bin $OUT/fx/$n/fn.bin | tail -2; python3 rc.py $OUT/fx/${REF:-m1}/fn.bin $OUT/fx/$n/fn.bin --mask r | tail -1 | sed 's/^/  r: /'; python3 rc.py $OUT/fx/${REF:-m1}/fn.bin $OUT/fx/$n/fn.bin --mask rfj | tail -1 | sed 's/^/  rfj: /' ) > $OUT/res/$n.rc 2>&1
    rm -f $OUT/fx/$n/in.ll $OUT/fx/$n/o3.ll
  fi
}
args=("$@"); i=0
while [ $i -lt ${#args[@]} ]; do
  run1 ${args[$i]} work0 & p0=$!
  j=$((i+1)); if [ $j -lt ${#args[@]} ]; then run1 ${args[$j]} work1 & p1=$!; fi
  wait
  i=$((i+2))
done
echo DONE "$@" >> $OUT/res/q.log
