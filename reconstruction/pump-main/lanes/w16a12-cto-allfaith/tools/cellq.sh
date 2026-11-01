#!/bin/bash
# cellq.sh name...: w15a06 exact cells (free/pin/pin+regideal) for each capture, sequential -> g/<name>.cells.out
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
for n in "$@"; do
  while [ ! -f rx/$n/res.json ]; do sleep 15; done
  [ -s g/$n.cells.out ] || bash t6/cells.sh $n rx/$n/m.ll > g/$n.cells.out 2>&1
done
