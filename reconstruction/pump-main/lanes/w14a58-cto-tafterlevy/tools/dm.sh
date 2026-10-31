#!/bin/bash
# dm.sh <res.jsonl> <refname> <refM> <refbytes>: M / bytes deltas vs a reference
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a58-cto-tafterlevy; cd $O
python3 tools/mr.py $(python3 -c "import json,sys;print(' '.join(json.loads(l)['name'] for l in open('$1') if 'ratio' in l))") | awk -v rm=$3 -v rb=$4 '{printf "%-34s %s %6d %+4d M %d %+d\n",$1,$2,$3,$3-rb,$5,$5-rm}'
