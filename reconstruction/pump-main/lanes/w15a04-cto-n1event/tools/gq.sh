#!/bin/bash
O=~/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event
while read n sp; do [ -z "$n" ] && continue; bash $O/tools/gcap.sh $1 $n "$sp" 2>>$O/gq$1.err; done < $2
echo DONE$1 >> $O/gq$1.done
