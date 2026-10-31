#!/bin/bash
# restore.sh <name> <tag> <blocks> [old] [new]: stop-before branch-folder on rx/<name>/m.ll, edit join-pred lines, resume, score
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a20-cto-ovarmpin; SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
N=$1; T=$2; BL=$3; OLD=${4:-'$r5 = COPY killed $r6'}; NEW=${5:-'$r5 = LDD_V1 $r10, -2272'}
D=$O/rx/${N}__$T; mkdir -p $D
[ -f $O/rx/$N/sbf.mir ] || $SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $O/rx/$N/m.ll -stop-before=branch-folder -o $O/rx/$N/sbf.mir
python3 $O/t2/mired.py $O/rx/$N/sbf.mir $D/r.mir "$BL" "$OLD" "$NEW"
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $D/r.mir -start-before=branch-folder -filetype=obj -o $D/m.o || exit 1
python3 - $D <<'PY'
import sys,os,json; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a20-cto-ovarmpin/t2'); import oracle,subprocess
d=sys.argv[1]; c=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c); rr,sd=oracle.metric(c,oracle.orig_window())
o=subprocess.run([os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump'),'-dr','--no-show-raw-insn',d+'/m.o'],capture_output=True,text=True).stdout
pos=None
for l in o.split('\n'):
    if 'admin_cto_sharing_config' in l: pos=l.split(':')[0].strip(); break
r={'name':os.path.basename(d),'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd,'share_call':pos}; print(json.dumps(r)); open(d+'/res.json','w').write(json.dumps(r))
PY
