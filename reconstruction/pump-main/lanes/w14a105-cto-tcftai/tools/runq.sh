#!/bin/bash
# runq.sh slot names...: sequential raw-IR captures + rx oracle (experiment only)
OUT=~/.cache/pumpfun-reconstruction/lanes/w14a105-cto-tcftai; cd $OUT
export SRC=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a105-cto-tcftai/programs/pump
W=$1; shift
for n in "$@"; do r=$(bash tools/capvar.sh $n edits/$n.py $W 2>&1 | tail -1); echo "$r" >> results.jsonl; done
