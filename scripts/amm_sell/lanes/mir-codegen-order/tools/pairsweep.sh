#!/bin/sh
# pairsweep.sh TAG "X1 X2 .." "Y1 Y2 .." FIXED... : all X>Y
cd $HOME/Documents/Codex/2026-10-24/amm-sell-swarm/lanes/mir-codegen-order
T=$1; XS=$2; YS=$3; shift 3; export SWEEP_FIXED="$*"
for x in $XS; do for y in $YS; do [ "$x" = "$y" ] || echo "$x>$y"; done; done | xargs -P 3 -I{} sh -c 'n=$(echo "{}" | tr ">" _); r=$(python3 tools/reorder.py '$T'_$n $SWEEP_FIXED "{}" 2>&1 | tail -1); echo "{} $r"; rm -f oracle/'$T'_$n.o oracle/'$T'_$n.s' > oracle/pair_$T.txt
sort -k5 -n oracle/pair_$T.txt | head -12
