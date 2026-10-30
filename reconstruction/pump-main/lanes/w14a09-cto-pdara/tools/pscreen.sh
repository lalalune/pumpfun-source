#!/bin/bash
# pscreen.sh <slot> <listfile>: screen partner trials (names per line) -> results2.jsonl (rx + chunk + coal)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara
S=$1
while read n; do
  [ -z "$n" ] && continue
  grep -q "\"name\": \"$n\"" $O/results2.jsonl 2>/dev/null && continue
  f=$O/e/t_$(echo "$n"|tr '+' '_').py
  printf 'import sys;sys.path.insert(0,"%s/e");import g2\nEDITS=g2.edits("%s")\n' $O "$n" > $f
  nn=$(echo "$n"|tr '+' '_')
  r=$(bash $O/tools/capvar.sh $nn $f $S 2>$O/rx/$nn.err) || { echo "{\"name\": \"$n\", \"error\": \"compile\"}" >> $O/results2.jsonl; continue; }
  c=$(python3 $O/tools/chunk.py $O/rx/$nn/m.o 2>/dev/null)
  k=$(python3 $O/tools/coal.py $O/rx/$nn 2>/dev/null | tail -1 | sed 's/^[^:]*: //')
  python3 -c "import json,sys;a=json.loads(sys.argv[1]);b=json.loads(sys.argv[2]);a.update({k:b[k] for k in ('fm','rm','rmV','rmT')});a['name']=sys.argv[3];a['coal']=sys.argv[4];print(json.dumps(a))" "$r" "$c" "$n" "$k" >> $O/results2.jsonl
  rm -f $O/rx/$nn/dbg.o $O/ir/$nn.ll
done < $2
