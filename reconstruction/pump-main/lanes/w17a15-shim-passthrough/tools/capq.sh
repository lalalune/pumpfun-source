#!/bin/bash
# capq.sh <slot> <names...>: capture a queue of variants sequentially in one build slot
s=$1; shift; cd $HOME/.cache/pumpfun-reconstruction/lanes/w17a15-shim-passthrough
for n in "$@"; do ./tools/cap.sh $n $s > res/cap_$n.out 2>&1; done
