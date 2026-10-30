#!/bin/bash
O=~/.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi
export PUMP_BUILD_SLOTS=10
cd /tmp; python3 $O/tools/capture_ir.py $O/trials/$1 $O/ir/post-$1 $O/work-ir > $O/ir/post-$1.log 2>&1
python3 $O/tools/slim.py $O/ir/post-$1/module.ll ${SYMS:-_ZN14pump_recovered5trade4sell17h} $O/oracle/$1.slim.ll
rm -f $O/ir/post-$1/module.ll
python3 $O/tools/irx.py $O/oracle/$1.slim.ll - $1
