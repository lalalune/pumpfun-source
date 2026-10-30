#!/bin/bash
# batch.sh <resultfile> name:genes ...  -- runs trial.sh two at a time (work0/work1)
D=$(cd "$(dirname "$0")" && pwd); R=$1; shift
run(){ local w=$1; shift; for x in "$@"; do $D/trial.sh "${x%%:*}" "${x#*:}" $w 2>&1 | grep -v '^ok ' >> $R; done; }
A=(); B=(); i=0; for x in "$@"; do if ((i%2==0)); then A+=("$x"); else B+=("$x"); fi; i=$((i+1)); done
run work0 "${A[@]}" & run work1 "${B[@]}" & wait; echo DONE >> $R
