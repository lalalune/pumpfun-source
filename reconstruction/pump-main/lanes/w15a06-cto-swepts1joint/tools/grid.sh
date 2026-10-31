#!/bin/bash
# grid.sh <name> <m.ll> [reg]: cells free / pin(valid) / pin(all) / r9 / r9+pin(valid) / r9+pin(all) for one base form
ME=~/.cache/pumpfun-reconstruction/lanes/w15a06-cto-swepts1joint; cd $ME; N=$1; I=$2; R=${3:-r9}; G=g/$N
mkdir -p $G
bash tools/mkdbg.sh $I $G/free >/dev/null 2>&1
echo "$N free   $(python3 tools/objsc.py $G/free/rt.o | sed 's/^[^ ]* *//')"
echo "$N pinV   $(python3 t139/mirperm.py $G/free valid 2>/dev/null)"
echo "$N pinA   $(python3 t139/mirperm.py $G/free all 2>/dev/null)"
bash tools/r9run.sh $I $G/r9x auto auto $R 2>$G/r9x.log >/dev/null || { echo "$N r9 FAIL"; cat $G/r9x.log; exit 1; }
echo "$N rt     $(python3 tools/objsc.py $G/r9x/rt.o | sed 's/^[^ ]* *//')"
echo "$N $R     $(python3 tools/objsc.py $G/r9x/r9.o | sed 's/^[^ ]* *//')"
bash tools/mkdbg.sh $G/r9x/pre_r9.mir $G/r9 -start-before=register-coalescer >/dev/null 2>&1
echo "$N ${R}rt   $(python3 tools/objsc.py $G/r9/rt.o | sed 's/^[^ ]* *//')"
echo "$N ${R}pV   $(python3 t139/mirperm.py $G/r9 valid 2>/dev/null)"
echo "$N ${R}pA   $(python3 t139/mirperm.py $G/r9 all 2>/dev/null)"
