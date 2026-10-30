#!/bin/bash
# runq.sh <listfile> : each line "name editsfile"; 2 workers; appends JSON (+fee tests count, errseq) to results_ir.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame; cd $OUT
run(){ W=$1; shift; while read -r N P; do [ -z "$N" ] && continue
  R=$(bash tools/capvar.sh $N $P $W 2>/dev/null | tail -1)
  FT=$(python3 tools/feetests.py rx/$N 2>/dev/null | grep -c TEST)
  ES=$(python3 tools/errseq.py rx/$N/fn.bin 2>/dev/null | cut -d' ' -f2-)
  bash tools/dis.sh rx/$N/m.o > rx/$N/m.dis 2>/dev/null; FM=$(python3 tools/absratio.py rx/$N/m.dis 2>/dev/null | awk '{print $3}')
  echo "{\"n\":\"$N\",\"r\":$R,\"feetests\":$FT,\"fm\":\"$FM\",\"errseq\":\"$ES\"}" >> results_ir.jsonl
  rm -f rx/$N/in.ll
done; }
L=$(wc -l < $1); H=$(( (L+1)/2 ))
head -n $H $1 > $1.a; tail -n +$((H+1)) $1 > $1.b
run 0 < $1.a & run 1 < $1.b & wait
