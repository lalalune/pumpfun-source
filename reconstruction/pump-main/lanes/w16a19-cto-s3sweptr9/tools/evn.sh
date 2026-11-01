#!/bin/bash
# evn.sh name...: price captured forms rx/<name>/m.ll with plain RAPRIO llc (no restore): payload regs + Mperm/Mhc -> cm/evn.jsonl
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9; cd $O
for n in "$@"; do python3 t2/ire.py V_$n --base rx/$n/m.ll --no-ares --perm 2>&1 | tail -1 >> cm/evn.jsonl; done
echo done >> cm/evn.done
