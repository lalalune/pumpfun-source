#!/bin/bash
# mbp.sh <name> <tag> <python-edit-expr-file|-> : stop-before block-placement, apply edits (EDITS list old,new in MIR text), resume, score
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop; SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
N=$1; T=$2; E=$3; D=$O/rx/${N}__$T; mkdir -p $D
A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
[ -f $O/rx/$N/sbp.mir ] || $SDK/llc $A $O/rx/$N/m.ll -stop-before=block-placement -o $O/rx/$N/sbp.mir
python3 - $O/rx/$N/sbp.mir $D/r.mir $E <<'PY'
import sys,runpy
s=open(sys.argv[1]).read()
if sys.argv[3]!='-':
    for a,b in runpy.run_path(sys.argv[3])['EDITS']:
        c=s.count(a); assert c==1,(c,a); s=s.replace(a,b)
open(sys.argv[2],'w').write(s)
PY
$SDK/llc $A $D/r.mir -start-before=block-placement -filetype=obj -o $D/m.o || exit 1
python3 - $D <<'PY'
import sys,os,json; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop/t2'); import oracle
d=sys.argv[1]; c=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c); rr,sd=oracle.metric(c,oracle.orig_window())
r={'name':os.path.basename(d),'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd}; print(json.dumps(r))
PY
