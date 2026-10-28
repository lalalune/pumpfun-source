#!/bin/bash
# Check out each Fees PR head in a dedicated review worktree and run the packet's own verifier(s).
# Writes one line per PR to results.tsv: PR, packet dir, verifier, exit code, seconds, last output line.
set -u
RR=/Users/shawwalters/fees100-run
RV=$RR/review/wt
REPO=/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source
PY=$REPO/work/test-env/bin/python
OUT=$RR/review/results.tsv
cd $REPO
if [ ! -d $RV ]; then
  git worktree add -q --no-checkout --detach $RV origin/main
  git -C $RV sparse-checkout init --cone
  git -C $RV sparse-checkout set research scripts evidence programs docs localnet .github audit binaries \
    repro/pump_fees repro/layered-passes/pass-36 repro/function-inventory repro/behavioral-recovery repro/consolidation \
    repro/donation-relay/linked-elf-reproduction repro/experiments
fi
: > $OUT
for n in "$@"; do
  git -C $RV checkout -q --detach --force refs/remotes/prs/$n || { printf '%s\t-\t-\tcheckout-failed\n' $n >> $OUT; continue; }
  base=$(git merge-base origin/main refs/remotes/prs/$n)
  dirs=$(git diff --name-only $base refs/remotes/prs/$n -- research | cut -d/ -f1-2 | sort -u)
  for d in $dirs; do
    for v in verify.py test_verify.py; do
      [ -f $RV/$d/$v ] || continue
      start=$(date +%s)
      (cd $RV && timeout 1200 $PY -B $d/$v > $RR/review/log-$n-$(basename $d)-$v.txt 2>&1); rc=$?
      printf '%s\t%s\t%s\t%s\t%ss\t%s\n' $n $d $v $rc $(( $(date +%s) - start )) "$(tail -1 $RR/review/log-$n-$(basename $d)-$v.txt | cut -c1-120)" >> $OUT
    done
  done
done
echo DONE >> $OUT
