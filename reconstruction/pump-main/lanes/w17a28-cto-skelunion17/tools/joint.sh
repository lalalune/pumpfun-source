#!/bin/bash
# joint.sh name: mpp (RA climb2 final forces + spill relabel) for st/<name>
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a28-cto-skelunion17; cd $OUT
n=$1
F=$(python3 -c "
import json
for l in open('c2/$n.log'):
    if l.startswith('{\"final\"'): print(','.join(json.loads(l)['final']['forces']))")
RAPRIO_STICKY=1 RAPRIO_FORCE=$F python3 tools/mpp.py j_$n st/$n/m.ll
