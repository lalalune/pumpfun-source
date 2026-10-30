#!/bin/bash
# par.sh t1 t2 t3 : run up to 3 trials (v/<t>.rs) in parallel, print summaries
O=~/.cache/pumpfun-reconstruction/lanes/w4-sweep; cd $O
i=0; for t in "$@"; do (W=$i bash scripts/trial.sh $t v/$t.rs > out/$t.txt 2>&1; python3 scripts/ccalls.py out/$t/unstripped.so > out/$t.calls 2>/dev/null) & i=$((i+1)); done; wait
for t in "$@"; do grep -h "struct=\|FAIL\|error" out/$t.txt | head -3; done
