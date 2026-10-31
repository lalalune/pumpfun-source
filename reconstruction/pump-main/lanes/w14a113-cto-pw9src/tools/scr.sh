#!/bin/bash
# scr.sh <m.ll>: pw9 screen: ratio from res.json, wf2 F/Fw, wd reg diffs, regmap r9->r8 count, new-ptr live size + word-1 register
O=~/.cache/pumpfun-reconstruction/lanes/w14a113-cto-pw9src; cd $O; M=$1; d=$(dirname $M)
R=$(python3 -c "import json;r=json.load(open('$d/res.json'));print(r['ratio'],r['bytes'],r.get('slots_diff'),r.get('eq_main'))" 2>/dev/null)
F=$(python3 tools/wf2.py $M | awk '{print $2,$4}')
W=$(python3 tools/wd.py $M | grep -o "'reg': [0-9]*")
G=$(python3 tools/regmap.py $M | head -1 | grep -o 'r9->r8:[0-9]*'); [ -z "$G" ] && G="r9->r8:<12th"
[ -f $d/ra.log ] || bash tools/ra.sh $M $d/ra.log
NV=$(grep -m1 -o '%[0-9]*:gpr = LDD_V1 %[0-9]*:gpr, -4088' $d/ra.log | cut -d: -f1)
NL=$(python3 tools/wtl.py $d/ra.log 0 90000 $NV | head -1 | awk '{print $4,$5,$6,$7,$NF}')
echo "$(basename $d) | $R | $F | $W | $G | new=$NV $NL"
