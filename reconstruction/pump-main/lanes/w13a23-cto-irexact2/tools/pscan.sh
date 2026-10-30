#!/bin/bash
# pscan.sh <post.ll> <prefix> <basespec>: run the 8 item files as 8 processes
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a23-cto-irexact2
for k in 0 1 2 3 4 5 6 7; do python3 tools/iredit.py scan $1 t/$2_$k "$3" $2_$k.txt -j 2 > $2_$k.jsonl 2>/dev/null & done; wait
