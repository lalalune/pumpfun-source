#!/bin/bash
# queue.sh SLOT QUEUEFILE : each line "NAME hunk hunk..."
L=~/.cache/pumpfun-reconstruction/lanes/y1-cto-diffwin; SLOT=$1
while read -r line; do [ -z "$line" ] && continue; set -- $line; n=$1; [ -f $L/res/$n.json ] && continue; $L/tools/run.sh $SLOT "$@" >/dev/null 2>&1 </dev/null; done < $2
