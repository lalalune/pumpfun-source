#!/bin/bash
# mv.sh <base.ll> <name> moves... : apply block moves (mv2.py) and score with px.py
M=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a112-cto-irorder14
b=$1; n=$2; shift 2
python3 $M/tools/mv2.py $b $M/io/$n.ll "$@" && echo "$* : $(python3 $M/tools/px.py $M/io/$n.ll)"; [ -z "$KEEP" ] && rm -f $M/io/$n.ll $M/io/$n.bin
