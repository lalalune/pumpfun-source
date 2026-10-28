#!/bin/bash
# Review the stacked Pump fee PRs: at each PR head, run the verifiers of the research dirs it adds or changes
# relative to its predecessor in the stack (#344 vs main, #358 vs #344, #367 vs #358, #375 vs #367), plus #362.
set -u
RR=/Users/shawwalters/fees100-run
RV=$RR/review/wt
REPO=/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source
PY=$REPO/work/test-env/bin/python
OUT=$RR/review/results-pump.tsv
export TMPDIR=$RR/review/tmp
cd $REPO
: > $OUT
run() {  # pr prev
  local n=$1 prev=$2
  git -C $RV checkout -q --detach --force refs/remotes/prs/$n || { printf '%s\tcheckout-failed\n' $n >> $OUT; return; }
  local dirs=$(git diff --name-only $prev refs/remotes/prs/$n -- research | cut -d/ -f1-2 | sort -u)
  for d in $dirs; do
    for v in verify.py test_verify.py; do
      [ -f $RV/$d/$v ] || continue
      local start=$(date +%s)
      (cd $RV && timeout 1800 $PY -B $d/$v > $RR/review/log-$n-$(basename $d)-$v.txt 2>&1); local rc=$?
      printf '%s\t%s\t%s\t%s\t%ss\t%s\n' $n $d $v $rc $(( $(date +%s) - start )) "$(tail -1 $RR/review/log-$n-$(basename $d)-$v.txt | cut -c1-110)" >> $OUT
    done
  done
}
run 344 $(git merge-base origin/main refs/remotes/prs/344)
run 358 refs/remotes/prs/344
run 367 refs/remotes/prs/358
run 375 refs/remotes/prs/367
run 362 $(git merge-base origin/main refs/remotes/prs/362)
echo DONE >> $OUT
