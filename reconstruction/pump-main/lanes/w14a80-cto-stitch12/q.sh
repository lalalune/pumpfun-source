#!/bin/bash
# sequential spec queue: runs each spec in $OUT/queue/ in sorted order (SRCBASE = pristine main crate, workers from $OUT/W)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12
cd /Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a80-cto-stitch12/reconstruction/pump-main/lanes/w14a80-cto-stitch12
while true; do
  while pgrep -f "run.py $OUT/specs" >/dev/null; do sleep 5; done
  f=$(ls $OUT/queue/ 2>/dev/null | sort | head -1); [ -z "$f" ] && { sleep 10; continue; }
  mv $OUT/queue/$f $OUT/specs/q_$f
  SRCBASE=$OUT/mainsrc/programs/pump python3 run.py $OUT/specs/q_$f $(cat $OUT/W 2>/dev/null || echo 2) >> $OUT/q.log 2>&1
done
