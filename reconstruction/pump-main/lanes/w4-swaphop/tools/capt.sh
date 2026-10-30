#!/bin/bash
# capt.sh name : capture IR for src/name, extract swap_hop, oracle+mir
O=~/.cache/pumpfun-reconstruction/lanes/w4-swaphop; N=$1; export PUMP_BUILD_SLOTS=10
python3 $O/bin/capirn.py --src $O/src/$N --work $O/work-ir-$N --out $O/ir/$N > $O/ir/$N.log 2>&1 || { tail -5 $O/ir/$N.log; exit 1; }
rm -rf $O/work-ir-$N
python3 $O/bin/extract.py $O/ir/$N/module.ll $O/ir/$N/sh.ll 8swap_hop17h; rm $O/ir/$N/module.ll $O/ir/$N/candidate.so
python3 $O/bin/oracle.py $O/ir/$N/sh.ll ${N}base - --mir
