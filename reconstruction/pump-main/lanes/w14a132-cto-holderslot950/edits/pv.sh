#!/bin/bash
# pv.sh <name> <edit names...>: post-opt IR edits from e/ir/<x>.py on rx/base/m.ll
O=~/.cache/pumpfun-reconstruction/lanes/w14a132-cto-holderslot950; cd $O
N=$1; shift; E=(); for x in "$@"; do E+=("$O/e/ir/$x.py"); done
bash tools/pe.sh $N "${E[@]}"
