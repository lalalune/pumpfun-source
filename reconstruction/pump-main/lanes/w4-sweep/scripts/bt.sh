#!/bin/bash
# bt.sh NAME file.rs : trial with pre-inline dump and BFI path listing
O=~/.cache/pumpfun-reconstruction/lanes/w4-sweep
S=_ZN14pump_recovered5sweep7execute17h63039d4d7bb21efdE
LLVMARGS="-print-before=inline -filter-print-funcs=$S" bash $O/scripts/trial.sh $1 $2 2>&1 | grep -v "^ *0\.\|Trace\|File\|i=t.index\|ValueError" 
python3 $O/scripts/bfi.py $O/out/$1/build.log $O/out/$1/fn.ll > $O/out/$1/bfi.txt 2>&1
python3 $O/scripts/bfipath.py $O/out/$1/fn.ll.n.ll > $O/out/$1/bfipath.txt 2>&1
grep -i "clone\|admit\|transfer\|rent" $O/out/$1/bfi.txt | cut -c1-70
