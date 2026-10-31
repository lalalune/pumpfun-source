#!/bin/bash
# batch.sh <slot> <names...>: capture+rx each s/<name>.py, append to screen.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a62-cto-nativeregs; W=$1; shift
cd $OUT
for n in "$@"; do r=$(bash tools/capvar.sh $n s/$n.py $W 2>&1 | tail -1); g=$(python3 tools/reg.py rx/$n/m.o 2>/dev/null); echo "{\"v\":\"$n\",\"r\":$r,\"reg\":\"$g\"}" >> screen.jsonl; rm -f ir/$n.ll rx/$n/m.ll; rm -rf var/$n; done
