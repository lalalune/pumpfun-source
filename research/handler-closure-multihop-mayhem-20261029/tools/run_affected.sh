#!/bin/bash
# Required + affected suites against the maintained candidate (no source change).
set -u
REPO=/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained
WORK=/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/work-handlers
OUT=$WORK/packet/receipts/affected
LOG=$WORK/wsl
mkdir -p "$OUT"
cd "$REPO"
CAND=research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so

run() {
  name="$1"; shift
  echo "=== $name start $(date -u +%H:%M:%S) ==="
  if python3 -B "$@" > "$LOG/affected-$name.log" 2>&1; then
    echo "=== $name OK ==="
  else
    echo "=== $name FAILED (exit $?) ==="
  fi
}

run verify_evidence scripts/verify_evidence.py
run test_tooling scripts/test_tooling.py
run tokenkeg_two_curve scripts/pump_tokenkeg_two_curve_differential.py --candidate "$CAND" --output "$OUT/tokenkeg_two_curve.json.gz"
run multi_hop_curve_partial repro/pump/native-curve-partial-fortyeight/harness/pump_multi_hop_curve_differential.py --candidate "$CAND" --output "$OUT/multi_hop_curve_partial.json"
run create_mayhem_preexisting scripts/pump_create_mayhem_differential.py --candidate-pump "$CAND" --candidate-mayhem evidence/original/mayhem/deployed.so --output "$OUT/create_mayhem_preexisting.json.gz"
run nested_create scripts/pump_create_nested_differential.py --candidate "$CAND" --output "$OUT/nested_create.json.gz"
run create_v2_quote scripts/pump_create_quote_differential.py --candidate "$CAND" --output "$OUT/create_v2_quote.json.gz"
echo "ALL DONE $(date -u +%H:%M:%S)"
