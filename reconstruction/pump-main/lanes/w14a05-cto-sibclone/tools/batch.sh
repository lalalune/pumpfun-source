#!/bin/bash
# batch.sh <slot> <names...>: capvar each edits/<name>.py; record rx + fm/rm + reloads to res.jsonl
O=~/.cache/pumpfun-reconstruction/lanes/w14a05-cto-sibclone; S=$1; shift
cd $O
for n in "$@"; do
  r=$(bash tools/capvar.sh $n edits/$n.py $S 2>>$O/batch.err | tail -1)
  ab=""; [ -f rx/$n/m.o ] && ab=$(python3 tools/abs.py rx/$n/m.o 2>/dev/null | awk '{print "{\"fm\":"$4",\"rm\":"$6"}"}')
  rl=""; [ -f rx/$n/fn.bin ] && rl=$(python3 tools/reloads.py rx/$n/fn.bin)
  echo "{\"n\":\"$n\",\"rx\":${r:-null},\"abs\":${ab:-null},\"rl\":${rl:-null}}" >> res.jsonl
  rm -f ir/$n.ll
done
