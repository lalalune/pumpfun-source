#!/bin/sh
# dis.sh <so> <out_prefix> [sym_start] [size]
B=~/.cache/solana/v1.44/platform-tools/llvm/bin
S=${3:-0x22a10}
SZ=${4:-$($B/llvm-readelf -s $1 | awk -v s=$(printf "%016x" $S) '$2==s && $4=="FUNC"{print $3; exit}')}
$B/llvm-objdump -d --no-show-raw-insn --start-address=$S --stop-address=$(($S+$SZ)) $1 | grep -E '^ +[0-9]+:' > $2_raw.txt
python3 -c "
import re,sys
o=open('$2_r.txt','w')
for l in open('$2_raw.txt'):
    m=re.match(r'\s*(\d+):\s+(.*)',l); o.write('0x%x  %s\n'%(int(m.group(1))*8, re.sub(r'\s*<.*>$','',m.group(2))))
"
echo $SZ
