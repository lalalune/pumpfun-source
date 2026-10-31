#!/bin/bash
# cq.sh <slot> <resfile> <edit files...>
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a72-cto-rescan304
W=$1; R=$2; shift 2
for f in "$@"; do n=$(basename $f .py); tools/capvar.sh $n $f $W 2>/dev/null | tail -1 >> $R;  done
