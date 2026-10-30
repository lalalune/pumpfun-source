#!/bin/bash
# batch.sh <slot> <names...>: capvar each edits/<name>.py then llcb features; append to res.jsonl
O=~/.cache/pumpfun-reconstruction/lanes/w14a01-cto-acctlive; S=$1; shift
cd $O
for n in "$@"; do
  r=$(bash tools/capvar.sh $n edits/$n.py $S 2>>$O/batch.err | tail -1)
  f=""; [ -f rx/$n/m.ll ] && f=$(python3 tools/llcb.py rx/$n/m.ll 2>/dev/null | tail -1)
  rl=""; [ -f rx/$n/fn.bin ] && rl=$(python3 tools/reloads.py rx/$n/fn.bin)
  echo "{\"n\":\"$n\",\"rx\":$r,\"llcb\":${f:-null},\"rl\":${rl:-null}}" >> res.jsonl
done
