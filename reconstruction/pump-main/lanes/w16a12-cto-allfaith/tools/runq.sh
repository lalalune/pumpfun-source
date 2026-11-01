#!/bin/bash
# runq.sh <pid-to-wait-for|0> spec...: run each spec file through scr.py (2 workers) after the given pid exits (this lane only)
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
P=$1; shift
while [ "$P" != "0" ] && kill -0 $P 2>/dev/null; do sleep 15; done
for s in "$@"; do python3 tools/scr.py $s 2 > ${s%.txt}.log 2>&1; done
