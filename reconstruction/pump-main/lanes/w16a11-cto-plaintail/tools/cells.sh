#!/bin/bash
# cells.sh <name> <m.ll>: w15a06 exact cells (free, +legal pin, +pin+regideal r9, +pin+regideal all) over two orig ranges
O=~/.cache/pumpfun-reconstruction/lanes/w16a11-cto-plaintail; cd $O; N=$1; I=$2; G=g/$N; mkdir -p $G
bash t6/mkdbg.sh $I $G/free >/dev/null 2>&1 || { echo "$N mkdbg FAIL"; exit 1; }
fr=$(python3 t6/objsc.py $G/free/rt.o | awk '{print $5}')
pv=$(python3 t139/mirperm.py $G/free valid 2>/dev/null | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['M'])")
P=$G/free/perm_valid.bin
out="{\"name\":\"$N\",\"free\":$fr,\"pin\":$pv"
for R in 0x3c00:0x5040 0x2800:0x5040; do lo=${R%%:*}; hi=${R##*:}
  RF=9 python3 t85/tools/regideal.py $P $G/ri9_$lo.bin $lo $hi >/dev/null 2>&1; a=$(python3 t6/objsc.py $G/ri9_$lo.bin | awk '{print $5}')
  python3 t85/tools/regideal.py $P $G/ria_$lo.bin $lo $hi >/dev/null 2>&1; b=$(python3 t6/objsc.py $G/ria_$lo.bin | awk '{print $5}')
  RF=9 python3 t85/tools/regideal.py $G/free/rt.bin $G/fri9_$lo.bin $lo $hi >/dev/null 2>&1; c=$(python3 t6/objsc.py $G/fri9_$lo.bin | awk '{print $5}')
  python3 t85/tools/regideal.py $G/free/rt.bin $G/fria_$lo.bin $lo $hi >/dev/null 2>&1; d=$(python3 t6/objsc.py $G/fria_$lo.bin | awk '{print $5}')
  out="$out,\"pin_ri9_$lo\":$a,\"pin_ria_$lo\":$b,\"ri9_$lo\":$c,\"ria_$lo\":$d"
done
echo "$out}" | tee -a data/cells.jsonl
