#!/bin/bash
# odis.sh <m.o> : function-relative hex listing of the (slimmed) oracle object = admin_cto::execute
~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump -d --no-show-raw-insn $1 2>/dev/null | python3 -c "
import sys,re
for l in sys.stdin:
    m=re.match(r'\s*(\d+):\s+(.*)',l)
    if m: print('%05x %s'%(int(m.group(1))*8,m.group(2).strip()))"
