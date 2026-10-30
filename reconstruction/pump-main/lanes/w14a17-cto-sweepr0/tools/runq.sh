#!/bin/bash
# runq.sh <slot> <listfile> <resfile>: run capvar for each name in list (edits in e/combo/<name>.py), append results
cd ~/.cache/pumpfun-reconstruction/lanes/w14a17-cto-sweepr0
while read n; do
  [ -z "$n" ] && continue
  r=$(bash tools/capvar.sh $n e/combo/$n.py $1 2>/dev/null | tail -1)
  echo "$r" >> $3
  [ -f rx/$n/m.ll ] && python3 tools/pe.py pe_$n --base rx/$n/m.ll >> $3.pe 2>/dev/null
  rm -rf var/$n rx/$n/m.o pe/pe_$n/m.o pe/pe_$n/m.ll
done < $2
