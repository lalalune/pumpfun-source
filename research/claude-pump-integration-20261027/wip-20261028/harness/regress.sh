#!/bin/bash
# regress.sh <pkg-name> [workers] -- run the 44-suite captured-loader corpus for an integration package in the full worktree
set -uo pipefail
W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work
PKG=$1; N=${2:-4}
REL=research/claude-pump-integration-20261027/$PKG
PY=/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source/work/test-env/bin/python
mkdir -p $W/full/research/claude-pump-integration-20261027 $W/full/work/claude-pkgbuild/$PKG
rsync -a --delete $W/int/$REL/ $W/full/$REL/
rsync -a --delete $W/int/work/claude-pkgbuild/$PKG/source/ $W/full/work/claude-pkgbuild/$PKG/source/
OUT=$W/full/work/claude-reg/$PKG
rm -rf $OUT; mkdir -p $OUT
cd $W/full
start=$(date +%s)
$PY -B scripts/pump_validate_parallel.py --candidate $REL/candidate.so --source-directory work/claude-pkgbuild/$PKG/source/programs/pump \
   --build-comparison $REL/build-comparison.json --output $OUT/full.json.gz --captured-loader --workers $N > $OUT/run.log 2>&1
rc=$?
echo "rc=$rc seconds=$(( $(date +%s) - start ))" | tee -a $OUT/run.log
exit $rc
