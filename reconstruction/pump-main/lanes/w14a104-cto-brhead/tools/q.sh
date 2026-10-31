#!/bin/bash
# q.sh <slot> <names...>
O=~/.cache/pumpfun-reconstruction/lanes/w14a104-cto-brhead; S=$1; shift
for n in "$@"; do bash $O/tools/trial.sh $n $S >> $O/tmp/q$S.log 2>&1; rm -rf $O/var/$n; done
echo DONE >> $O/tmp/q$S.log
