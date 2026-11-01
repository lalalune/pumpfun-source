#!/bin/bash
# stkq.sh name...: sequential stk.sh (no force) for each name once rx/<name>/m.ll exists -> stk/<name>.out
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
for n in "$@"; do
  while [ ! -f rx/$n/res.json ]; do sleep 15; done
  [ -f stk/${n}_p0/stk.json ] || t2/stk.sh $n '' p0 > stk/$n.out 2>&1
done
