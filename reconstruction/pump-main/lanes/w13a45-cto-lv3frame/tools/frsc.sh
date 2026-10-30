#!/bin/bash
# frsc.sh <m.ll> <spec> <tag>: frsweep-run spec, keep module, print score + stack-coloring groups
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame
T=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a45-cto-lv3frame/reconstruction/pump-main/lanes/w13a17-cto-outlineport/tools
DL=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc
python3 $O/tools/frsweep.py run $1 "$2" --keep $O/k/$3
$DL -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $O/k/$3/m.ll -filetype=obj -o /dev/null -debug-only=stack-coloring 2> $O/k/$3/sc.log
python3 $T/scg.py $O/k/$3/sc.log > $O/k/$3/scg.txt; rm $O/k/$3/sc.log
