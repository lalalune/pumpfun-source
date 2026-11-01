#!/bin/bash
# reland.sh <pr> <branch> <genes>: merge latest main, re-apply text genes on main's admin_cto.rs, push, land.py; loop on exit 3 (conflict)
set -u
PR=$1; BR=$2; GENES=$3
C=$HOME/.cache/pumpfun-reconstruction; OUT=$C/lanes/w19b13-cto-v1-holder-and1
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w19b13-cto-v1-holder-and1
LAND=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/land.py
F=programs/pump/src/creator/admin_cto.rs
for attempt in 1 2 3 4 5 6 7 8; do
  git -C $WT fetch -q origin || { sleep 20; continue; }
  if ! git -C $WT merge-base --is-ancestor origin/main HEAD; then
    git -C $WT merge --no-commit --no-ff origin/main > /dev/null 2>&1
    git -C $WT show origin/main:$F > $OUT/src/base.rs
    python3 $OUT/tools/g.py rl $GENES || { echo "GENE FAILED"; git -C $WT merge --abort; exit 9; }
    cp $OUT/src/rl.rs $WT/$F
    git -C $WT add -A $F
    git -C $WT checkout origin/main -- $(git -C $WT diff --name-only --diff-filter=U | grep -v "^$F$" | grep -v "reconstruction/pump-main/lanes/w19b13" ) 2>/dev/null
    git -C $WT add -A reconstruction/pump-main/lanes/w19b13-cto-v1-holder-and1 2>/dev/null
    git -C $WT commit -q -m "Merge origin/main into $BR, re-apply the 307 key gene

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || { echo "COMMIT FAILED"; git -C $WT status --short | head; exit 8; }
    git -C $WT push -q origin HEAD:$BR 2>&1 | tail -1
  fi
  st=$(gh pr view $PR --repo lalalune/pumpfun-source --json state -q .state 2>/dev/null)
  if [ "$st" = "CLOSED" ]; then gh pr reopen $PR --repo lalalune/pumpfun-source 2>&1 | tail -1; fi
  echo "attempt $attempt main $(git -C $WT rev-parse --short origin/main) $(date)"
  python3 $LAND $PR --allow-forcing > $OUT/res/land_$PR.$attempt.out 2>&1; e=$?
  tail -1 $OUT/res/land_$PR.$attempt.out | cut -c1-700
  echo "exit $e"
  [ $e = 3 ] || exit $e
done
exit 7
