#!/bin/sh
# an.sh <name>: ir oracle ratio + frame summary + vqr region of a captured build
cd ~/.cache/pumpfun-reconstruction/lanes/w4-createv2
python3 scripts/ir.py $1 out/$1/pump_recovered.ll | head -1
python3 - $1 <<'P'
import sys;sys.path.insert(0,'scripts');import ir
rows=[r for r in ir.frame(sys.argv[1]) if r[4]!='spill-slot']
print(' '.join('%#x:%d:%s'%(r[1],r[2],r[3]) for r in sorted(rows,key=lambda r:r[1]) if 0x170<r[1]<0x510))
P
python3 scripts/maps.py orig-norm.txt irexp/$1/fn.txt | tail -2
grep -c 'sink.split:' irexp/$1/m.ll
