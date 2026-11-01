#!/bin/bash
# capq.sh <slot> <names...>: capture a queue of variants sequentially in one build slot
s=$1; shift; cd $HOME/.cache/pumpfun-reconstruction/lanes/w17a26-shim-assumeq
for n in "$@"; do ./tools/cap.sh $n $s > res/cap_$n.out 2>&1; done
