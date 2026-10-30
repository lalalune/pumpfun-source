#!/bin/bash
# screen.sh <base genes> <prefix> <knob list file> : base+knob capture, IR-compensate (amove target.i.sroa.0 into hk hole), mm both
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis; T=$O/tools; B=$1; P=$2; i=0
one(){ k=$1; w=$2; n=${P}_$(echo $k | tr ':' '_'); [ -f $O/x/$n/fn.txt ] || $T/mk.sh $n "$B,$k" $w >/dev/null 2>&1
  [ -f $O/x/$n/fn.txt ] || { echo "$n FAIL" >> $O/screen_$P.txt; return; }
  python3 $T/amove.py $O/x/$n $O/x/${n}_am target.i.sroa.0:hk >/dev/null 2>&1
  echo "$(python3 $T/mm.py $O/x/$n) | AM $(python3 $T/mm.py $O/x/${n}_am 2>/dev/null) | $(python3 $T/fdelta.py $O/x/m3 $O/x/$n | tail -1)" >> $O/screen_$P.txt
  rm -f $O/x/$n/pei.mir $O/x/${n}_am/pei.mir $O/x/$n/ex.o $O/x/${n}_am/ex.o; }
while read k; do [ -z "$k" ] && continue; one $k work$((i%2)) & i=$((i+1)); [ $((i%2)) = 0 ] && wait; done < $3; wait
