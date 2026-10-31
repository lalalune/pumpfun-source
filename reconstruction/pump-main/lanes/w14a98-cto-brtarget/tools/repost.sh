#!/bin/bash
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a98-cto-brtarget; cd $O
for d in rx/*/; do n=$(basename $d); [ "$n" = m ] && continue; [ -f $d/m.ll ] || continue; grep -q "\"name\": \"$n\"" r1b.jsonl 2>/dev/null && continue
 a=$(python3 tools/post1.py $n 2>/dev/null); h=$(python3 tools/hw.py $n 'bb7.i=1:1,bb14.i=1:1' 2>/dev/null); h2=$(python3 tools/hw.py $n 'bb7.i=1:1,bb14.i=1:1,bb23.i=1:1' 2>/dev/null)
 python3 -c "import json,sys;a=json.loads(sys.argv[1]);h=json.loads(sys.argv[2]) if sys.argv[2] else {};h2=json.loads(sys.argv[3]) if sys.argv[3] else {};a['hw_M']=h.get('M');a['hw_b']=h.get('bytes');a['hw_jM']=h.get('jM');a['hw23_M']=h2.get('M');a['hw23_b']=h2.get('bytes');print(json.dumps(a))" "$a" "$h" "$h2" >> r1b.jsonl
done
