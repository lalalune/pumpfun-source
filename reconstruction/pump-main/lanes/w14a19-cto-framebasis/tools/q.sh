#!/bin/bash
# q.sh <queue file> : run mk.sh on each "name genes" line, 2 at a time (work0/work1), skip names with x/<name>/frame.txt
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis; i=0
while read n g; do [ -z "$n" ] && continue; [ -f $O/x/$n/frame.txt ] && continue
  w=work$((i%2)); $O/tools/mk.sh $n "$g" $w >> $O/qlog.txt 2>&1 &
  i=$((i+1)); if [ $((i%2)) = 0 ]; then wait; fi
done < $1; wait
