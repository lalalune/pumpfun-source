#!/bin/bash
cd ~/.cache/pumpfun-reconstruction/lanes/w14a34-cto-curvetail
bash runq.sh 0 $1 $2 & bash runq.sh 1 $1 $2 & wait; echo done >> $2.done
