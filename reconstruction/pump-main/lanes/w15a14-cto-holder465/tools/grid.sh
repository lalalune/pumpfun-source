#!/bin/bash
# grid.sh <name> <m.ll>: colmap, wallet-partner vregs, screen {none, acc, dcp, acc+dcp} -> ../ed/g_<name>.jsonl
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a14-cto-holder465/r
N=$1; M=$2; EXTRA=$3
python3 tools/colmap.py $M cm/$N ${EXTRA:+--force $EXTRA} > cm/$N.out 2>&1 || { echo "$N colmap fail"; exit 1; }
read -r _ ACC < <(python3 tools/wv.py cm/$N | grep ^acc); read -r _ DCP < <(python3 tools/wv.py cm/$N | grep ^dcp)
J=../ed/gj_$N.jsonl; : > $J
for f in "none|" "acc|$ACC" "dcp|$DCP" "accdcp|$ACC,$DCP"; do k=${f%%|*}; v=${f#*|}; [ -n "$EXTRA" ] && v=${v:+$v,}$EXTRA
  if [ -n "$v" ]; then printf '{"name":"%s_%s","force":"%s","full":1}\n' $N $k "$v" >> $J; else printf '{"name":"%s_%s","full":1}\n' $N $k >> $J; fi; done
rm -f ../ed/g_$N.jsonl; python3 tools/screen.py $M $J ../ed/g_$N.jsonl 4 >/dev/null 2>&1
python3 -c "
import json,sys
for l in open('../ed/g_$N.jsonl'):
    d=json.loads(l); print(f\"{d['name']:22s} {d.get('ratio')} slots {d.get('slots')} bytes {d.get('bytes')} L2 {d.get('L2')} {d.get('error','')[:80]}\")"
