#!/bin/bash
# batch.sh <slot> name... : capture+rx+coal for src/<name>.py, append to screen.jsonl
O=~/.cache/pumpfun-reconstruction/lanes/w14a06-cto-sweptcoal; W=$1; shift
for N in "$@"; do
  R=$(bash $O/tools/capvar.sh $N $O/src/$N.py $W 2>&1 | tail -1)
  C=$(cd $O && python3 tools/coal.py rx/$N/m.ll 2>&1 | tail -1 | sed 's/.*m.ll: //')
  echo "{\"n\":\"$N\",\"rx\":$( [ "${R:0:1}" = "{" ] && echo "$R" || echo "\"$R\""),\"coal\":\"$C\"}" | tee -a $O/screen.jsonl
  rm -f $O/rx/$N/dbg.o $O/rx/$N/fn.bin
done
