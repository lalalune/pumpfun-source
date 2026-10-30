#!/bin/bash
# calls.sh name..: count call instructions in execute (internal / syscall) and print bytes
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound
for n in "$@"; do t=$(bash $O/tools/dis.sh $O/rx/$n/m.o); echo "$n calls=$(echo "$t" | grep -c ' call') n=$(echo "$t" | wc -l | tr -d ' ')"; done
