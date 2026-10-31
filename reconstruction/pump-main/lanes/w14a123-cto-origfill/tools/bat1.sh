#!/bin/bash
# bat1.sh <spec> <slot>: one worker; lines "name genes"; results appended to $RES
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a123-cto-origfill; cd $OUT
while read n g; do [ -z "$n" ] && continue; [ -f rx/$n/res.json ] && continue; [ -f STOP_$2 ] && break
 r=$(tools/cvO.sh $n $g $2 2>&1 | tr '\n' ' '); echo "$n $g | $r" >> ${RES:-res.txt}; rm -f ir/$n.ll rx/$n/m.ll rx/$n/m.o rx/${n}_O/m.ll rx/${n}_O/m.o; done < $1
