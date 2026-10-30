#!/bin/bash
# batch.sh <slot> name1 name2 ... : run edits/<name>.py sequentially on work<slot>
O=$HOME/.cache/pumpfun-reconstruction/lanes/w13a48-cto-vaultspill
s=$1; shift
for n in "$@"; do $O/tools/vrun.sh $n $O/edits/$n.py $s >/dev/null 2>&1; done
echo done $s
