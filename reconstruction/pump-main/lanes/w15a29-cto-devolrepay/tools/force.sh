#!/bin/bash
# force.sh <m.ll> <name> <RAPRIO_FORCE> : private llc with force, prints M/ratio/bytes
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a29-cto-devolrepay
d=$OUT/cm/f/$2; mkdir -p $d
RAPRIO_FORCE="$3" $OUT/llvmb/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1 -filetype=obj -o $d/m.o || exit 1
python3 - $d <<'P'
import sys,difflib,json
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a29-cto-devolrepay'
exec(open(T+'/tools/rx.py').read().split('OUT=os.environ')[0])
d=sys.argv[1]; c=elf_fn(d+'/m.o',KEEP); open(d+'/fn.bin','wb').write(c)
O=mask(open(T+'/orig.bin','rb').read()); cm=mask(c)
M=sum(b.size for b in difflib.SequenceMatcher(None,O,cm,autojunk=False).get_matching_blocks())
r,sd=metric(c,open(T+'/orig.bin','rb').read())
print(json.dumps({'d':d.split('/')[-1],'bytes':len(c),'M':M,'ratio':round(r,5),'slots':sd}))
P
