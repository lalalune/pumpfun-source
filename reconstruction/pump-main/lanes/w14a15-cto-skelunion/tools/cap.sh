#!/bin/bash
# cap.sh <genes_joined_by_underscore|m> <slot> [name]: gen EDITS from e/gen.py on worktree source, capture + rx
O=~/.cache/pumpfun-reconstruction/lanes/w14a15-cto-skelunion
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a15-cto-skelunion
G=$1; S=$2; N=${3:-$1}
mkdir -p $O/src_edits
if [ "$G" = m ]; then echo 'EDITS=[]' > $O/src_edits/$N.py; else python3 $O/e/gen.py $G $WT/programs/pump/src/creator/admin_cto.rs $O/src_edits/$N.py || exit 1; fi
bash $O/tools/capvar.sh $N $O/src_edits/$N.py $S
