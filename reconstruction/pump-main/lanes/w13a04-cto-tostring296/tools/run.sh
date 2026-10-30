#!/bin/bash
# run.sh v1 [v2] : measure up to 2 variants concurrently; print summary
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a04-cto-tostring296; TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools
i=0; for v in "$@"; do $TOOLS/measure.sh $OUT/var/$v $OUT/work$i $OUT/t/$v > $OUT/t/$v.json 2>$OUT/t/$v.err & i=$((i+1)); done; wait
for v in "$@"; do
 if [ -f $OUT/t/$v/unstripped.so ]; then $OUT/tools/mkann.sh $OUT/t/$v/unstripped.so $OUT/an_$v.txt >/dev/null 2>&1; W=$(python3 $OUT/tools/chunks2.py $OUT/orig_a.txt $OUT/an_$v.txt | tail -1 | awk '{print $2}'); NTS=$(grep -c "ToString" $OUT/an_$v.txt); else W=na; NTS=na; fi
 python3 -c "
import json;d=json.load(open('$OUT/t/$v.json'));a=d.get('admin_cto') or {};print('$v','ok',d.get('ok'),'norm',d.get('normalized'),'raw',d.get('raw'),'loss',len(d.get('losses',[])),'bytes',a.get('cand_bytes'),'ratio',a.get('ratio'),'slots',a.get('slots_diff'),'calls',a.get('calls_candidate'),'struct','$W','tostr','$NTS')" 2>&1 | tail -1
done
