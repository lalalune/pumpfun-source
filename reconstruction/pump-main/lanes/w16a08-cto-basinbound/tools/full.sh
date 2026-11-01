#!/bin/bash
# full.sh <rx>: stack + RA pass 1 + pass 2 (restore-aware), no frame band shift
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound; cd $O; n=$1
bash t2/stack.sh $n > /dev/null 2>&1
bash t2/rpipe.sh $n 30 12 > cm/$n.rpipe.out 2>&1
bash t2/rpass2.sh $n p2 30 12 > cm/${n}p2.out 2>&1
