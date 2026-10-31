#!/bin/bash
# cap.sh <name> <genes> <slot>: capture raw IR of the gene variant, then thr.py (exact per-site inline decisions), rx score, inl, fr
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a141-cto-outline312; cd $OUT
tools/cv.sh $1 $2 $3 > log_$1.txt 2>&1 || { echo "$1 $2 | COMPILE FAIL $(tail -3 log_$1.txt|tr '\n' ' ')" >> ${RES:-results.txt}; exit 1; }
echo "$1 $2 | thr $(python3 tools/thr.py ir/$1.ll) | ibfi $(IB_PASSES='function(print<block-freq>)' python3 tools/ibfi.py ir/$1.ll 2>&1|tail -1) | $(python3 tools/inl.py $1|cut -c14-) | $(python3 tools/fr.py $1 | tr '\n' ' ') | $(cat rx/$1/res.json)" >> ${RES:-results.txt}
[ "$KEEP" = 1 ] || rm -f ir/$1.ll
