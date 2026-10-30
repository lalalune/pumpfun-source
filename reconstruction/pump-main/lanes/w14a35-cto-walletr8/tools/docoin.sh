#!/bin/bash
# docoin.sh <m.ll>: print the wallet flag-init sequence (orig: mov64 r8,0x0; mov64 r6,0x0; jne r0,0x0,+0x1)
bash ~/.cache/pumpfun-reconstruction/lanes/w14a35-cto-walletr8/tools/dll.sh $1 | grep -B3 "jne r0, 0x0, +0x1" | grep -A0 -B3 "mov64 r6, 0x0" | head -4 | tr '\n' ';' ; echo
