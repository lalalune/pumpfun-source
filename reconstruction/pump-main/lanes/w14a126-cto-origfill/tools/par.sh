#!/bin/bash
# par.sh <spec>: names (genes = name unless 2nd column) two at a time through two.sh
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a126-cto-origfill; cd $OUT
awk 'NR%2==1' $1 > $1.a; awk 'NR%2==0' $1 > $1.b
run(){ while read n g; do [ -z "$n" ] && continue; tools/two.sh $n ${g:-$n} $2; done < $1; }
run $1.a 0 & run $1.b 1 & wait
