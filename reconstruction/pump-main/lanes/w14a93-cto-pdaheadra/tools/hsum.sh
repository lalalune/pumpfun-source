#!/bin/bash
# hsum.sh name...: one-line head RA summary per rx name
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a93-cto-pdaheadra
for n in "$@"; do t=$(echo $n | tr '+' '_'); python3 $O/tools/head.py $O/rx/$n/m.ll h_$t $HFORCE 2>/dev/null | head -1 | python3 -c "
import json,sys;d=json.loads(sys.stdin.readline());h=d['head']
print('%-26s'%'$n', d['plain/reg/L1/L2'], 'miss',d['cm'].split()[-1], 'acc_evict',d['acc_evict'][:1], 'args',h.get('arg_r5',[0,0])[1:], 'phi0',h.get('phi0',[0,0])[1:],'sharing',h.get('sharing@%0',[0,0])[1:],'curve',h.get('curve@%0',[0,0])[1:])"; done
