#!/bin/bash
# batch.sh <results file> <names...>: 2 workers, capvar + scr per variant (e/src/<name>.py)
O=~/.cache/pumpfun-reconstruction/lanes/w14a113-cto-pw9src; cd $O; RES=$1; shift
run(){ w=$1; shift; for n in "$@"; do r=$(bash tools/capvar.sh $n e/src/$n.py $w 2>&1 | tail -1); if echo "$r" | grep -q '"ratio"'; then s=$(bash tools/scr.sh rx/$n/m.ll; python3 tools93/jfix2.py $O/rx/$n/m.ll $O/s/$n > s/$n.j 2>&1); echo "$s" >> $RES; rm -f rx/$n/fn.bin rx/$n/m.o; else echo "$n | FAIL $r" >> $RES; fi; rm -rf var/$n; done; }
A=(); B=(); i=0; for n in "$@"; do if [ $((i%2)) = 0 ]; then A+=($n); else B+=($n); fi; i=$((i+1)); done
run 0 "${A[@]}" & run 1 "${B[@]}" & wait
echo DONE >> $RES
