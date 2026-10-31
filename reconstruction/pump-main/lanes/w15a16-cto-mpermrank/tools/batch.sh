#!/bin/bash
# batch.sh <srcdir-of-rx> <prefix> <out.jsonl> [par]: mp.py over every stable rx/<n>/m.ll
SRC=$1; PFX=$2; RES=$3; PAR=${4:-3}; O=$(dirname $(dirname $0))
cd $O
find $SRC -maxdepth 2 -name m.ll -mmin +2 | sort | while read f; do n=$(basename $(dirname $f)); grep -q "\"n\": \"$PFX$n\"" $RES 2>/dev/null || echo "$PFX$n $f"; done |
  xargs -P $PAR -n 2 sh -c 'HC=${HC:-1} python3 tools/mp.py "$0" "$1" 2>/dev/null; rm -rf rx/$0/f.o' >> $RES
