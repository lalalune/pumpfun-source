#!/bin/sh
# sweep.sh ANCHOR TAG [FIXEDOPS...] : move every block X after ANCHOR (after applying fixed ops)
cd $HOME/Documents/Codex/2026-10-24/amm-sell-swarm/lanes/mir-codegen-order
A=$1; T=$2; shift 2; export SWEEP_FIXED="$*"
for x in $(cat oracle/blocks.txt); do [ "$x" = "$A" ] && continue; echo "$x"; done | xargs -P 3 -I{} sh -c 'r=$(python3 tools/reorder.py '$T'_{} $SWEEP_FIXED "{}>'$A'" 2>&1 | tail -1); echo "{} $r"; rm -f oracle/'$T'_{}.o oracle/'$T'_{}.s' > oracle/sweep_$T.txt
sort -k5 -n oracle/sweep_$T.txt | head -12
