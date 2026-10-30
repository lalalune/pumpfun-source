#!/bin/bash
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a17-cto-sweepr0
while read x; do
  n=$(echo $x | tr -d '%.'); XVAL=$x XGEP=%i363 python3 tools/fscan.py rx/base4/mn.ll x fs4/$n.jsonl 4 > fs4/$n.log 2>&1
done < fs4.list
echo done > fs4/ALLDONE
