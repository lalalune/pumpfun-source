#!/bin/bash
# rawscan.sh: for each block X in raw x04 body, move X to the end; report ratio
O=~/.cache/pumpfun-reconstruction/lanes/w4-buyexactquote-v3; cd $O
export RSYM=buy_exact_quote_body17h RAW=out/raw-x04/pump_recovered.ll
L=$(tail -1 an/raw-x04.irb | awk '{print $1}')
awk '{print $1}' an/raw-x04.irb | grep -v '^start$' | grep -v "^$L$" | xargs -P 3 -I{} bash -c 'r=$(bash scripts/rawexp.sh scan_{} "{}>'$L'" 2>/dev/null | tr "\n" " "); echo "{} $r"; rm -f rawexp/scan_{}.ll rawexp/scan_{}.o3.ll; rm -rf irexp/raw_scan_{}'
