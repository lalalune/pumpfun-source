#!/bin/bash
# mploop.sh: run mp.py (Mperm/Mhc) on every captured rx/<name>/m.ll lacking rx/mp_<name>/mp.json; loops until killed.
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a14-cto-vcretune
while true; do
  for d in rx/*/; do n=$(basename $d); case $n in mp_*) continue;; esac
    [ -f rx/$n/m.ll ] || continue; [ -f rx/mp_$n/mp.json ] && continue
    HC=1 python3 s16/mp.py mp_$n rx/$n/m.ll >> rx/mploop.log 2>&1
  done; sleep 20
done
