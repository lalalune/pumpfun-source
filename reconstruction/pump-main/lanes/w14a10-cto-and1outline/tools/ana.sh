#!/bin/bash
# ana.sh name: print holder/tag test forms in post-opt IR + lseq
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a10-cto-and1outline
grep -E "= and i8 %holder|and i8 %_[0-9a-z.]*copyload, 1|icmp eq i8 %_[0-9]+.sroa.0.0.copyload, 0" $O/rx/$1/m.ll | head -8
python3 $O/tools/lseq.py $O/rx/$1/m.o | tail -1
