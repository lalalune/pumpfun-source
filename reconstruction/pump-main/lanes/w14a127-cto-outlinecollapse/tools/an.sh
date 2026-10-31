#!/bin/bash
# an.sh name...: M metrics, new-copy alloca present?, J flip / relaid, bfi cold pattern summary
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a127-cto-outlinecollapse; cd $O
for n in "$@"; do
  [ -f rx/$n/fn.bin ] || { echo "$n: no fn.bin"; continue; }
  f=$(python3 tools/fr.py $n | sed 's/  */ /g'); c=$(grep -c "sroa.[0-9]* = alloca \[32 x i8\], align 1" rx/$n/m.ll); nc=$(grep -c "0.new.sroa_idx, i64 32" rx/$n/m.ll)
  j=$(python3 t93/jfix3.py $O/rx/$n/m.ll $O/jf/$n 2>&1 | python3 -c "import sys,json;d=json.loads(sys.stdin.read() or '{}');print('noflip' if 'note' in d else 'flip moved=%s relay=%s'%(d.get('moved'),d.get('relay','')[:60]))" 2>&1)
  b=$( [ -f ir/$n.ll ] && python3 tools/bfi.py ir/$n.ll | awk '{printf "%s%s ", $5, ($6=="COLD"?"c":"h")}')
  echo "$f | a32=$c newcp=$nc | $j | bfi $b"
done
