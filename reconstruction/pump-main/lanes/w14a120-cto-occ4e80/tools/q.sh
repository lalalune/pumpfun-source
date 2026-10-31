#!/bin/bash
# q.sh <slot> <listfile>: each line "name spec"
O=~/.cache/pumpfun-reconstruction/lanes/w14a120-cto-occ4e80
while read n sp; do [ -z "$n" ] && continue; bash $O/tools/cg.sh $1 $n "$sp" 2>>$O/q$1.err; done < $2
echo DONE$1
