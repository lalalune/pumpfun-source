#!/bin/bash
# emap.sh base.ll edges.txt out.jsonl : empty-asm split of each critical edge, px score
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a66-cto-feeedge
B=$1; E=$2; R=$3; mkdir -p $O/px/em
one(){ p="$1"; s="$2"; h=$(echo "$p $s" | md5 -q | cut -c1-8); f=$O/px/em/$h.ll
  python3 $O/tools/esplit.py $B $f "$p" "$s" 2>/dev/null || { echo "{\"p\":\"$p\",\"s\":\"$s\",\"err\":1}" >> $R; return; }
  r=$(python3 $O/tools/px.py $f | tail -1); echo "{\"p\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$p"),\"s\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$s"),\"r\":$r}" >> $R; rm -f $f $O/px/em/$h.bin; }
i=0; while read -r p s; do one "$p" "$s" & i=$((i+1)); if [ $((i%2)) = 0 ]; then wait; fi; done < $E; wait
