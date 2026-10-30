#!/bin/bash
# trial.sh <name> <edits.py> <slot>: capvar + ssc colour map at the sharing CPI call
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a29-cto-hcbools
cd $OUT
r=$(bash tools/capvar.sh $1 $2 $3) || { echo "{\"name\":\"$1\",\"error\":\"compile\"}"; exit 1; }
bash tools/sscrun.sh rx/$1
S=$(grep -E "^[0-9]+B.*JAL @_ZN14pump_recovered9pump_fees3cpi24admin_cto_sharing_config" rx/$1/ssc.log | head -1 | sed -E 's/^([0-9]+)B.*/\1/')
python3 tools/sscmap.py rx/$1/ssc.log rx/$1/ssc.log $((S-1)) $((S+1)) > rx/$1/cross.txt
n=$(wc -l < rx/$1/cross.txt | tr -d ' ')
echo "$r cross=$n"
rm -rf $OUT/var/$1
