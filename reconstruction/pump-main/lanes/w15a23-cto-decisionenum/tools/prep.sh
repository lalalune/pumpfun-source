#!/bin/bash
# prep.sh <unstripped.so> <outprefix>: fn.bin + dis + syms for webs.py
SO=$1; P=$2; T=~/.cache/pumpfun-reconstruction/lanes/w15a23-cto-decisionenum
RE=$(ls ~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-readelf)
python3 -c "
import sys;sys.path.insert(0,'$T/t128');import oracle
open('$P.bin','wb').write(oracle.elf_fn('$SO',oracle.KEEP))"
python3 $T/tools/dis.py $P.bin 0 100000 > $P.dis
# symbol addresses relative to the window start 0x22a10 of this candidate
$RE -sW $SO | awk '$4=="FUNC"{print $2,$3,$8}' > $P.syms0
python3 - $P.syms0 $P.syms <<'PY'
import sys
L=[l.split() for l in open(sys.argv[1])]
st=[int(a,16) for a,s,n in L if 'admin_cto7execute' in n][0]
open(sys.argv[2],'w').write(''.join(f'{int(a,16)-st+0x22a10:x} {s} {n}\n' for a,s,n in L))
PY
