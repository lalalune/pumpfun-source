#!/bin/bash
# gate.sh <name> [so]: live high slots (>=0x8d0) at the sharing CPI; flags entry r3/r4 spill webs
T=~/.cache/pumpfun-reconstruction/lanes/w15a23-cto-decisionenum; N=$1; SO=${2:-$T/t/$N/unstripped.so}
cd $T; [ -f an/$N.dis ] || tools/prep.sh $SO an/$N
C=$(SYMS=an/$N.syms python3 tools/calls.py an/$N.dis | grep admin_cto_sharing_config | awk '{print $1}')
SYMS=an/$N.syms python3 tools/webs.py an/$N.dis --live-at $C 2>/dev/null | sed -n '/== live/,$p' | awk -v n=$N -v c=$C '$1 ~ /^0x(8[d-f]|9)/ {k++; if ($3 ~ /^0x(8|10|18|20)$/) e=e" "$1"("$5")"} END{print n, "cpi",c, "high-live",k, "entry-arg-spills-live:",e}'
