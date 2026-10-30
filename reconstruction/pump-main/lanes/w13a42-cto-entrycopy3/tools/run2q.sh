#!/bin/bash
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3
bash $O/tools/runq.sh 0 $(cat $O/q0.txt) &
bash $O/tools/runq.sh 1 $(cat $O/q1.txt) &
wait
