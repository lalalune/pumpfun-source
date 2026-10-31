#!/bin/bash
# sequential spec queue: waits for any running run.py of this lane, then runs each spec in $OUT/queue/ in order
cd /Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a80-cto-stitch12/reconstruction/pump-main/lanes/w14a80-cto-stitch12
while true; do
  while pgrep -f "run.py /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12/specs" >/dev/null; do sleep 5; done
  f=$(ls /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12/queue/ 2>/dev/null | sort | head -1); [ -z "$f" ] && { sleep 10; continue; }
  mv /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12/queue/$f /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12/specs/q_$f
  python3 run.py /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12/specs/q_$f 2 >> /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12/q.log 2>&1
done
