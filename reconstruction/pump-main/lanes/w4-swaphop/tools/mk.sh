#!/bin/bash
# mk.sh name edit.py : copy worktree crate to OUT/src/name and apply python edit (string replacements)
O=~/.cache/pumpfun-reconstruction/lanes/w4-swaphop; W=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-swaphop
rm -rf $O/src/$1; mkdir -p $O/src; rsync -a --exclude target $W/programs/pump/ $O/src/$1/
python3 $2 $O/src/$1/src/multi_hop_curve_swap.rs || exit 1
