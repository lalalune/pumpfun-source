#!/bin/bash
# runq.sh <listfile> <slot> <out.jsonl>: capture+rx+post1 each variant name (v/<name>.py)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a98-cto-brtarget
cd $O
while read n; do
  [ -z "$n" ] && continue
  grep -q "\"name\": \"$n\"" $3 2>/dev/null && continue
  r=$(bash tools/capvar.sh $n v/$n.py $2 2>&1 | tail -1)
  if echo "$r" | grep -q '"ratio"'; then python3 tools/post1.py $n >> $3 2>>$O/post.err; else echo "{\"name\":\"$n\",\"error\":$(echo "$r" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()[-300:]))')}" >> $3; fi
  rm -rf $O/var/$n $O/ir/$n.ll
done < $1
