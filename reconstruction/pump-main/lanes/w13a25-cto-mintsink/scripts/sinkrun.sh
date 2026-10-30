#!/bin/bash
# sinkrun.sh <mod.ll> <outdir> <label>=<v1,v2> ...: edit_sink1 llc oracle + clonefeat per spec
D=$(cd "$(dirname "$0")" && pwd); M=$1; O=$2; shift 2
for spec in "$@"; do lab=${spec%%=*}; vs=${spec#*=}
  r=$(SINK=$vs python3 $D/ctoracle.py run $M $O/$lab --edit $D/edit_sink1.py 2>&1 | tail -1)
  cf=$(python3 -c "
import sys;sys.path.insert(0,'$D');import clonefeat as c
b=open('$O/$lab/fn.bin','rb').read();t=[];i=0
while i<len(b):
  n=16 if b[i]==0x18 else 8;t.append(b[i:i+n]);i+=n
print('%d/%d'%c.feats(t))" 2>/dev/null)
  echo "$lab $r cf=$cf"; done
