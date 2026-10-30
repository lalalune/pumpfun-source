#!/bin/sh
# trial.sh <name> <edit.py> [from=g7]: mk + build(ir) + ir oracle
cd ~/.cache/pumpfun-reconstruction/lanes/w6r1-execute-ir
python3 scripts/mk.py $1 $2 ${3:-g7} >/dev/null || exit 1
sh scripts/build.sh $1 ir && N=0 python3 scripts/ir.py $1 out/$1/pump_recovered.ll | head -1
