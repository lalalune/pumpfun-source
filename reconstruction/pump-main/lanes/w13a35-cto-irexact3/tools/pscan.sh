#!/bin/bash
# pscan.sh <post.ll> <prefix> <basespec> [n]: run the n item files as n processes
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a35-cto-irexact3
N=${4:-8}
for k in $(seq 0 $((N-1))); do python3 tools/iredit.py scan $1 t/$2_$k "$3" $2_$k.txt -j 2 > $2_$k.jsonl 2>/dev/null & done; wait
