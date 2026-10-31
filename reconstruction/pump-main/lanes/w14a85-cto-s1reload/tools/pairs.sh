#!/bin/bash
# pairs.sh name...: capvar the named edits two at a time (slots 0/1), print results + fmr
D=$(cd $(dirname $0)/..; pwd); O=~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload; cd $D
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do
  x=${a[$i]}; y=${a[$((i+1))]}
  bash tools/capvar.sh $x edits/$x.py 0 > $O/c_$x.txt 2>&1 &
  [ -n "$y" ] && bash tools/capvar.sh $y edits/$y.py 1 > $O/c_$y.txt 2>&1
  wait; i=$((i+2))
done
for n in "$@"; do r=$(tail -1 $O/c_$n.txt); f=""; [ -f $O/rx/$n/fn.bin ] && f=$(python3 tools/fmr.py $O/rx/$n/fn.bin); echo "$n | $r | $f"; done
