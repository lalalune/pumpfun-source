#!/bin/bash
# batch.sh <log> <slot> name...: run capvar for each e/<name>.py sequentially on a slot
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a38-cto-cbflagphi
LOG=$1; S=$2; shift 2
for n in "$@"; do bash tools/capvar.sh $n $PWD/e/$n.py $S >> $LOG 2>&1 || echo "{\"name\":\"$n\",\"error\":1}" >> $LOG; done
echo DONE >> $LOG
