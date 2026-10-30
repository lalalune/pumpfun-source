#!/bin/bash
# edr.sh <m.ll> <edits|-> <spec...>: run ed.py for each spec in parallel (max 6), prefix with edit name
M=$1; E=$2; shift 2
for s in "$@"; do (r=$(python3 ~/.cache/pumpfun-reconstruction/lanes/w14a11-cto-headchain/tools/ed.py $M $E "$s"); echo "$(basename $E) $r") & 
  while [ $(jobs -r | wc -l) -ge 6 ]; do sleep 0.5; done; done; wait
