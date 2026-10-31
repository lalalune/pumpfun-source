#!/bin/bash
# kv.sh <slot> <combo...>: capture each knob combo (names from e/klib.py joined by +)
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a43-cto-tcfrescan
W=$1; shift
for c in "$@"; do n=k_$(echo $c|tr '+' '_'); KN=$c tools/capvar.sh $n e/klib.py $W 2>/dev/null | tail -1 | sed "s/^/$c /" >> t/kv.res; rm -f ir/$n.ll; done
