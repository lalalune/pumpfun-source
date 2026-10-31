#!/bin/bash
# run.sh <name> <edits...>: pe.sh + wf2 + wd one-line summary
O=~/.cache/pumpfun-reconstruction/lanes/w14a82-cto-walletweight; cd $O
N=$1; shift; E=(); for x in "$@"; do E+=("e/ir/$x.py"); done
R=$(bash tools/pe.sh $N "${E[@]}"); F=$(python3 tools/wf2.py pe/$N/m.ll | awk '{print $2,$4}'); D=$(python3 tools/wd.py pe/$N/m.ll | cut -d' ' -f2-)
echo "$R $F $D" | sed 's/"f": //'
