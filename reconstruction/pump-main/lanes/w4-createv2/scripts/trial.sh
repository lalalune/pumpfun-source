#!/bin/sh
# trial.sh <name> <edit.py> [from]: mk + build(ir) + ir oracle
cd ~/.cache/pumpfun-reconstruction/lanes/w4-createv2
python3 scripts/mk.py $1 $2 ${3:-r1nc} >/dev/null || exit 1
sh scripts/build.sh $1 ir && python3 scripts/ir.py $1 out/$1/pump_recovered.ll | head -1; grep -c 'sink.split:' irexp/$1/m.ll
