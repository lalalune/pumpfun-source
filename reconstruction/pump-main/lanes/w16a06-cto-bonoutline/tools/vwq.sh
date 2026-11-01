#!/bin/bash
# vwq.sh <base>: wait for ir/<base>.ll, then V-time 306 weights 1:2 and 1:4 via rx.py (opt+llc)
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a06-cto-bonoutline
B=$1
until [ -f ir/$B.ll ] && [ -f rx/$B/res.json ]; do sleep 5; done
for w in 1:2 1:4; do tag=$(echo $w | tr ':' '_'); VW=$w python3 tools/rx.py ${B}_vw$tag tools/vw.py --base ir/$B.ll > log_${B}_vw$tag.txt 2>&1 & done; wait
