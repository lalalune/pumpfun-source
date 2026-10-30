#!/bin/bash
# greedy.sh <ex.ll> <outdir> <rounds> [base-json] : greedy nolt/mv(before holder_key) climb, one edit per round
LL=$1; OD=$2; N=$3; B=${4:-[]}; T=$(dirname "$0")
for r in $(seq 1 $N); do
  MODE=nolt,mv python3 $T/scan.py $LL $OD/r$r "$B" > $OD/r$r.txt 2>&1
  B=$(python3 -c "import json;d=json.load(open('$OD/r$r/scan.json'));print(json.dumps(d[0][2]))")
  echo "round $r: $(head -1 $OD/r$r.txt)"; rm -rf $OD/r$r/[nmb]*
done
