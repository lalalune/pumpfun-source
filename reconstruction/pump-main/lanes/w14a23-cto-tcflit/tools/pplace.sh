#!/bin/bash
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a23-cto-tcflit
declare -A XV=([_227i]=%_227.i [_228i]=%_228.i [_229i]=%_229.i [_230i]=%_230.i [_231i131]=%_231.i131 [_232i132]=%_232.i132 [_249i136]=%_249.i136 [x11i]=%x11.i [x12i]=%x12.i [x13i]=%x13.i [xi]=%x.i)
while read n p; do
  MODE=pp PLACE=$p XVAL=${XV[$n]} XGEP=%i363 python3 tools/pscan.py rx/m4/mn.ll x pp4/ppl_${n}_$p.jsonl 4 > /dev/null 2>&1
done < ppl.jobs
echo fin
