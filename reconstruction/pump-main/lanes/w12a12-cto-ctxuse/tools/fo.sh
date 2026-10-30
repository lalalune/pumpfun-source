#!/bin/bash
# fo.sh NAME [frameoracle args...]  -> prints masked ratio + equal r10 pairs
WT=${WT:?set WT to your worktree}; OUT=${OUT:?set OUT to your lane out dir}; mkdir -p $OUT/fo; cd $OUT
n=$1; shift
IR=${IR:-$OUT/ir-base/pump_recovered.ll}
python3 $WT/reconstruction/pump-main/lanes/w4-frame-oracle/frameoracle.py --ir $IR --sym '_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]+E' --win 0x22a10 --name $n --out $OUT/fo --no-partition "$@" > $OUT/fo/$n.txt 2>&1
echo "$n: $(head -2 $OUT/fo/$n.txt | tr '\n' ' ' | grep -o 'masked-exact-ratio [0-9.]*\|cand bytes [0-9]*\|equal [0-9]*' | tr '\n' ' ')"
