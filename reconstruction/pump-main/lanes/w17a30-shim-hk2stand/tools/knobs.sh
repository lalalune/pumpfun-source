#!/bin/bash
# knobs.sh <base_g16_genes> <gx genes> <knob...>: capture WXvp+X+vt + each knob (2 parallel), score
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a30-shim-hk2stand; cd $OUT
B=$1; X=$2; shift 2
run(){ k=$1; s=$2; n=k_$(echo $k | tr '+' '_'); python3 tools/mksrc.py src/$n.rs "$B+$k" $X >/dev/null 2>&1 || { echo "{\"name\":\"$n\",\"err\":\"gene\"}" >> res/knobs.jsonl; return; }
  tools/capg.sh $n $s "" $OUT/src/$n.rs >/dev/null 2>&1; NAMES="buf.i25.i _112.i _48.i _37.i _26.i _12.i _60.i" python3 tools/hprobe.py cap/$n/m.ll specs/n0.py /dev/null --par 1 --ref ir/frame_wxvp.txt 2>/dev/null | sed "s/\"name\": \"n\"/\"name\": \"$n\"/" >> res/knobs.jsonl; rm -f cap/$n/unstripped.so; }
while [ $# -gt 0 ]; do a=$1; shift; b=${1:-}; [ -n "$b" ] && shift
  run $a 0 & [ -n "$b" ] && run $b 1 & wait; done
