#!/bin/bash
OUT=~/.cache/pumpfun-reconstruction/lanes/w15a07-cto-tcfthrough; cd $OUT
f=$1; n=fs_$(echo $f|tr ',=' '__')
r=$(LLC=$OUT/bin/llc-ra RAPRIO_FORCE=$f python3 tools/px.py $n rx/m0/m.ll e/m0px.py 2>&1 | tail -1)
echo "$f $r"; rm -rf rx/$n
